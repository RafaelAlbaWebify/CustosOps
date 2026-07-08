from collections import defaultdict
from datetime import datetime
from typing import Any

from app.schemas.finding import EvidenceItem, SecurityFinding
from app.schemas.risky_signin import RiskySignInEvidence, RiskySignInRecord


LEGACY_CLIENT_APPS = {
    "imap",
    "pop",
    "smtp",
    "other clients",
    "exchange activesync",
    "autodiscover",
}


def _evidence(source: str, key: str, value: Any) -> EvidenceItem:
    return EvidenceItem(source=source, key=key, value=str(value))


def _user(record: RiskySignInRecord) -> str:
    return record.user_principal_name or "unknown-user"


def _risk_level(record: RiskySignInRecord) -> str:
    return str(record.risk_level_aggregated or "unknown").lower()


def _risk_state(record: RiskySignInRecord) -> str:
    return str(record.risk_state or "unknown").lower()


def _country(record: RiskySignInRecord) -> str:
    return str(record.location.country_or_region or "unknown")


def _client_app(record: RiskySignInRecord) -> str:
    return str(record.client_app_used or "unknown").strip().lower()


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _format_records(records: list[RiskySignInRecord]) -> str:
    return ", ".join(record.sign_in_id for record in records[:5])


def analyze_risky_signin_evidence(evidence: RiskySignInEvidence) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []

    high_risk_active = [
        record
        for record in evidence.records
        if _risk_level(record) == "high" and _risk_state(record) in {"at_risk", "unknown"}
    ]
    if high_risk_active:
        users = sorted({_user(record) for record in high_risk_active})
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_ACTIVE_HIGH_RISK",
                title="Active high-risk sign-in evidence needs review",
                severity="high",
                confidence="high",
                category="Identity alert triage",
                affected_asset=", ".join(users[:5]),
                evidence=[
                    _evidence("risky_signins", "high_risk_active_count", len(high_risk_active)),
                    _evidence("risky_signins", "example_sign_in_ids", _format_records(high_risk_active)),
                ],
                why_it_matters=(
                    "High-risk sign-in evidence can indicate credential theft, impossible travel, "
                    "unfamiliar sign-in properties, or another identity risk signal. This requires "
                    "SOC-style review before assuming either compromise or false positive."
                ),
                limitations=[
                    "This module analyzes exported or synthetic sign-in evidence only; it does not query a live tenant.",
                    "Risk levels depend on the upstream identity provider or sample data quality.",
                    "A high-risk sign-in is not proof of account compromise by itself.",
                ],
                safe_next_steps=[
                    "Check the user, IP address, country, application, device, risk state, and MFA result.",
                    "Compare with the user's expected working location, travel, and recent support tickets.",
                    "Escalate to identity/security operations if the sign-in remains suspicious.",
                ],
                non_actions=[
                    "Do not reset passwords, disable accounts, or revoke sessions from this tool.",
                    "Do not contact users with sensitive accusations based on this evidence alone.",
                ],
            )
        )

    successful_without_mfa = [
        record
        for record in evidence.records
        if record.status == "success"
        and _risk_level(record) in {"medium", "high"}
        and record.mfa_required is True
        and record.mfa_satisfied is not True
    ]
    if successful_without_mfa:
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_SUCCESS_MFA_NOT_SATISFIED",
                title="Risky successful sign-in without confirmed MFA satisfaction",
                severity="high",
                confidence="medium",
                category="Identity control validation",
                affected_asset=", ".join(sorted({_user(record) for record in successful_without_mfa})[:5]),
                evidence=[
                    _evidence("risky_signins", "successful_risky_without_mfa_count", len(successful_without_mfa)),
                    _evidence("risky_signins", "example_sign_in_ids", _format_records(successful_without_mfa)),
                ],
                why_it_matters=(
                    "A successful risky sign-in where MFA was required but not confirmed as satisfied "
                    "may indicate a Conditional Access, MFA reporting, or session-control issue that needs validation."
                ),
                limitations=[
                    "MFA status fields can differ between exports, portals, and licensing levels.",
                    "The evidence does not prove whether a token or session was later revoked.",
                ],
                safe_next_steps=[
                    "Validate the event in Entra ID sign-in logs or the approved identity console.",
                    "Check Conditional Access result, authentication requirement, and authentication details.",
                    "Escalate if the sign-in was successful and the user does not recognize the activity.",
                ],
                non_actions=[
                    "Do not change Conditional Access policy based on this sample analysis alone.",
                ],
            )
        )

    legacy_client_records = [
        record for record in evidence.records if _client_app(record) in LEGACY_CLIENT_APPS
    ]
    if legacy_client_records:
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_LEGACY_CLIENT_APP_USED",
                title="Legacy client application sign-in evidence found",
                severity="medium",
                confidence="high",
                category="Identity attack surface",
                affected_asset=", ".join(sorted({_user(record) for record in legacy_client_records})[:5]),
                evidence=[
                    _evidence("risky_signins", "legacy_client_count", len(legacy_client_records)),
                    _evidence("risky_signins", "client_apps", ", ".join(sorted({_client_app(record) for record in legacy_client_records}))),
                ],
                why_it_matters=(
                    "Legacy authentication or older client protocols can reduce enforcement of modern identity controls "
                    "and are frequently reviewed during identity security hygiene checks."
                ),
                limitations=[
                    "Client app labels depend on the source export and may require tenant-side confirmation.",
                    "Some records may represent historical or blocked attempts rather than current exposure.",
                ],
                safe_next_steps=[
                    "Confirm whether legacy authentication is blocked by policy.",
                    "Check whether the affected user or application has a justified exception.",
                    "Escalate policy questions to the identity administration owner.",
                ],
                non_actions=[
                    "Do not disable protocols or application access from this tool.",
                ],
            )
        )

    failures_by_user: dict[str, list[RiskySignInRecord]] = defaultdict(list)
    for record in evidence.records:
        if record.status == "failure":
            failures_by_user[_user(record)].append(record)

    repeated_failures = {
        user: records for user, records in failures_by_user.items() if len(records) >= 3
    }
    if repeated_failures:
        top_user, records = sorted(repeated_failures.items(), key=lambda item: len(item[1]), reverse=True)[0]
        countries = sorted({_country(record) for record in records})
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_REPEATED_FAILURES",
                title="Repeated failed sign-in evidence for one or more users",
                severity="medium",
                confidence="medium",
                category="Identity alert triage",
                affected_asset=top_user,
                evidence=[
                    _evidence("risky_signins", "top_user", top_user),
                    _evidence("risky_signins", "failure_count", len(records)),
                    _evidence("risky_signins", "countries", ", ".join(countries)),
                ],
                why_it_matters=(
                    "Repeated failed sign-ins can indicate password spraying, user error, stale credentials, "
                    "misconfigured applications, or automated attempts. The correct response depends on context."
                ),
                limitations=[
                    "This rule does not prove password spraying because it analyzes a small local evidence set.",
                    "Thresholds are intentionally conservative for portfolio/sample evidence.",
                ],
                safe_next_steps=[
                    "Check whether failures came from one IP, many IPs, one country, or multiple countries.",
                    "Compare with lockout, MFA, user helpdesk, and application migration context.",
                    "Escalate if failures are widespread, high-volume, or followed by a successful risky sign-in.",
                ],
                non_actions=[
                    "Do not block IPs or disable users from this tool.",
                ],
            )
        )

    countries_by_user: dict[str, set[str]] = defaultdict(set)
    timestamps_by_user: dict[str, list[datetime]] = defaultdict(list)
    for record in evidence.records:
        countries_by_user[_user(record)].add(_country(record))
        parsed = _parse_timestamp(record.created_at)
        if parsed:
            timestamps_by_user[_user(record)].append(parsed)

    multi_country_users = [
        user
        for user, countries in countries_by_user.items()
        if len({country for country in countries if country != "unknown"}) >= 2
    ]
    if multi_country_users:
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_MULTI_COUNTRY_ACTIVITY",
                title="Same user has sign-in evidence from multiple countries",
                severity="medium",
                confidence="low",
                category="Identity context review",
                affected_asset=", ".join(sorted(multi_country_users)[:5]),
                evidence=[
                    _evidence("risky_signins", "users_with_multiple_countries", len(multi_country_users)),
                ],
                why_it_matters=(
                    "Multiple-country sign-in activity can be normal travel, VPN/proxy use, cloud service behavior, "
                    "or suspicious access. It is useful triage context but needs validation."
                ),
                limitations=[
                    "This rule does not calculate physical travel distance or prove impossible travel.",
                    "VPN, proxy, and geolocation quality can create misleading location evidence.",
                ],
                safe_next_steps=[
                    "Review timestamps, device details, IP reputation context, and user travel expectations.",
                    "Escalate only if the activity remains unusual after business-context checks.",
                ],
                non_actions=[
                    "Do not assume compromise based only on country changes.",
                ],
            )
        )

    if not findings:
        findings.append(
            SecurityFinding(
                finding_id="RISKY_SIGNIN_NO_MAJOR_FINDINGS",
                title="No major risky sign-in findings in current evidence",
                severity="info",
                confidence="medium",
                category="Identity alert triage",
                affected_asset=evidence.tenant_label,
                evidence=[_evidence("risky_signins", "analysis_result", "no_major_findings")],
                why_it_matters="The current evidence did not trigger the initial CustosOps risky sign-in rules.",
                limitations=[
                    "This is not a live Entra ID investigation.",
                    "Absence of findings in sample evidence is not proof that identity risk is absent.",
                ],
                safe_next_steps=[
                    "Continue reviewing endpoint, DNS, Windows Event, and application evidence.",
                ],
                non_actions=[
                    "Do not treat this as proof of complete identity security posture.",
                ],
            )
        )

    return findings
