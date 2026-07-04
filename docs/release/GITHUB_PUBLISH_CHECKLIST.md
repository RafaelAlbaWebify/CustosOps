# CustosOps GitHub Publish Checklist

Status: publish-prep checklist for CustosOps v0.29.

## Recommended repository visibility

Start as a private GitHub repository. Make it public only after the owner reviews screenshots, demo text, and all public-readiness scans.

## Repository description

Local-first cybersecurity evidence, posture, and reporting platform for endpoint, DNS, application log, Windows Event, and IIS/Application evidence.

## Suggested topics

```text
cybersecurity
local-first
evidence
security-reporting
windows
iis
fastapi
react
typescript
portfolio-project
```

## Before publishing

```text
1. Confirm git status is clean.
2. Confirm HEAD is tagged with the latest release tag.
3. Confirm frontend build passes.
4. Confirm backend tests pass.
5. Confirm platform contract audit passes.
6. Confirm evidence contract audit passes.
7. Confirm Desktop UI proof passes with 10 workspaces.
8. Confirm UI proof artifact checker passes.
9. Confirm no non-allowlisted secret-pattern matches.
10. Confirm no private workplace/customer references are present in tracked files.
```

## What not to upload manually

Do not upload local proof ZIPs, generated reports, local evidence files, virtual environments, node_modules, dist folders, or runtime history data.

## Suggested first GitHub push

```powershell
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin master --tags
```

Use a private repository first unless a final manual review has been completed.