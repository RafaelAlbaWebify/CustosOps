# Risky Sign-In Escalation Note

## Scenario

Synthetic Microsoft 365 / Entra-style risky sign-in evidence shows unusual identity activity for review.

## Evidence reviewed

```text
- Sign-in records: 8
- Users represented: 3
- Risk indicators: high risk, MFA not confirmed, repeated failures, legacy client attempts, multi-country activity
- Source: samples/risky_signins/sample-risky-signins.json
```

## Initial assessment

This evidence requires identity/security review, but it is not enough to declare account compromise by itself.

The most concerning pattern is a successful high-risk sign-in where MFA was required but not confirmed as satisfied. Repeated failures and legacy client attempts increase the need for validation.

## Evidence table

| Evidence area | Observation | Why it matters | Limitation |
|---|---|---|---|
| High-risk sign-in | One user has active high-risk sign-in evidence | May indicate credential theft, unusual location, anonymous IP, or unfamiliar sign-in properties | Risk level depends on source data and must be validated in Entra ID |
| MFA result | Risky successful sign-in does not show confirmed MFA satisfaction | Could indicate MFA reporting, Conditional Access, or session-control issue | Exported evidence may not include full authentication details |
| Repeated failures | Same user has repeated failed attempts | Could be password spraying, stale credentials, user error, or app misconfiguration | Small sample does not prove attack pattern |
| Legacy client | IMAP/SMTP-style client usage appears | Legacy clients can weaken modern identity controls | Needs tenant policy confirmation |
| Multi-country activity | Same user has sign-in records from multiple countries | Useful context for suspicious travel/VPN/proxy review | Does not prove impossible travel |

## Recommended safe next steps

```text
1. Validate the sign-ins in the approved identity console.
2. Review user, IP, country, app, device, risk state, MFA, and Conditional Access result.
3. Check whether the user recognizes the activity.
4. Compare with travel, VPN, known support tickets, and application migration context.
5. Escalate to the identity/security owner if the activity remains suspicious.
```

## Non-actions

```text
- Do not disable the account from CustosOps.
- Do not reset the password from CustosOps.
- Do not revoke sessions from CustosOps.
- Do not modify Conditional Access from CustosOps.
- Do not accuse the user of compromise based on this evidence alone.
```

## Escalation message

```text
I reviewed the risky sign-in evidence and found one successful high-risk sign-in where MFA was not confirmed as satisfied, plus repeated failed attempts and legacy client activity for related users. I cannot confirm compromise from this evidence alone, but I recommend validating the event in Entra ID, checking authentication details and Conditional Access results, and confirming whether the user recognizes the activity. If the user does not recognize it or the risk remains active, this should be escalated through the identity/security process.
```

## Interview explanation

```text
In a SOC role, I would avoid jumping straight to remediation. First I would confirm the evidence, check context, understand impact, document uncertainty, and escalate with the right details. CustosOps shows that workflow in a safe local-first way.
```
