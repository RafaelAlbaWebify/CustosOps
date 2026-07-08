# Risky Sign-In Demo Notes

## Purpose

Show CustosOps as a safe, read-only SOC triage learning project using synthetic Microsoft 365 / Entra-style sign-in evidence.

This is not a live tenant monitor and not an identity administration tool.

## Five-minute demo flow

```text
1. Explain the alert scenario.
2. Show the synthetic risky sign-in evidence sample.
3. Run or describe /api/risky-signins/sample-findings.
4. Review the generated findings.
5. Explain severity, confidence, limitations, and safe next steps.
6. Generate a Risky Sign-In Evidence Report.
7. Show that the report is suitable for escalation, not automatic remediation.
```

## Scenario summary

```text
A small organization has several sign-in records that look unusual:
- one successful high-risk sign-in
- MFA not confirmed as satisfied
- repeated failed attempts for the same user
- legacy client application attempts
- multi-country activity for one user
```

## What I am demonstrating

```text
- I can start from alert-like evidence.
- I can separate evidence from assumptions.
- I can classify severity and confidence.
- I can write safe next steps.
- I can explain limitations.
- I can escalate without overclaiming compromise.
- I do not use a portfolio tool to change accounts or policies.
```

## What I should say in an interview

```text
CustosOps has a risky sign-in scenario using synthetic Entra-style evidence. The goal is not to replace Entra ID, Defender, or a SIEM. The goal is to show how I think as a SOC learner: I review the user, IP, country, device, app, risk state, MFA result, and Conditional Access result; then I classify the evidence, document limitations, and produce an escalation-ready report.
```

## Findings to explain

```text
RISKY_SIGNIN_ACTIVE_HIGH_RISK
- High-risk evidence needs review.
- It is not proof of compromise by itself.

RISKY_SIGNIN_SUCCESS_MFA_NOT_SATISFIED
- A risky successful sign-in lacks confirmed MFA satisfaction.
- Validate in the approved identity console.

RISKY_SIGNIN_LEGACY_CLIENT_APP_USED
- Legacy client sign-in evidence increases identity attack surface.
- Confirm if legacy authentication is blocked or intentionally allowed.

RISKY_SIGNIN_REPEATED_FAILURES
- Repeated failures may be password spraying, stale credentials, user error, or app misconfiguration.
- Escalate when repeated attempts are suspicious or followed by success.

RISKY_SIGNIN_MULTI_COUNTRY_ACTIVITY
- Multi-country evidence is useful context.
- It does not prove impossible travel without validation.
```

## Safe escalation wording

```text
I would not disable the account directly from this tool. I would validate the event in Entra ID or the approved identity console, check whether the user recognizes the activity, review MFA and Conditional Access details, and escalate to the identity/security owner if the activity remains suspicious.
```

## Boundaries to state clearly

```text
- No live tenant connection.
- No credential collection.
- No password reset.
- No account disablement.
- No session revocation.
- No Conditional Access changes.
- No claim that a risky sign-in proves compromise by itself.
```

## Natural closing line

```text
This project helps me demonstrate SOC triage discipline: collect evidence safely, classify what matters, document uncertainty, recommend safe next steps, and escalate with a clear report instead of guessing or taking unsafe actions.
```
