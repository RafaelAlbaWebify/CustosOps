# M28A - Release Audit Alignment

Status: complete

Purpose:

Align release-hardening audit coverage with the IIS/Application workspace added in M27.

Scope:

```text
In scope:
- Ensure platform contract audit includes the IIS/Application workspace row.
- Preserve the 10-workspace Desktop UI proof requirement.
- Document release-hardening scan interpretation.

Out of scope:
- Product runtime changes.
- New collectors.
- Frontend UI redesign.
```

Release-hardening interpretation:

```text
TODO/FIXME/HACK scan must be zero before final packaging.
Redacted placeholder strings such as [REDACTED_PASSWORD], [REDACTED_TOKEN], [REDACTED_API_KEY], and [REDACTED_SECRET] are expected redaction examples, not live secrets.
The final packaging audit should still scan for secret-like strings and review every match manually.
```

Validation:

```text
1. frontend build
2. backend tests
3. platform contract audit with IIS row
4. evidence module contract audit
5. Desktop UI proof with 10 workspaces
6. UI proof artifact checker
```

Release tag:

```text
custosops-v0.28.0-release-audit-alignment
```

Next recommended milestone:

```text
M28B - final README, operator quickstart, known limitations, and demo script
```
