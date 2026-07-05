# Private-first GitHub Push Guide

This guide prepares CustosOps for GitHub publication. It does not require the repository to be public.

## Current expected baseline

```text
custosops-v0.31.0-beginner-runbook-launch-audit
```

## Recommended order

```text
1. Create a private GitHub repository.
2. Add the remote locally.
3. Push master and tags.
4. Review GitHub-rendered README, docs, and file list.
5. Keep the repository private until final manual review is complete.
6. Make public only if desired.
```

## Commands

From the local repository root:

```powershell
git status --short
git log -1 --oneline
git tag --points-at HEAD
```

Expected tag:

```text
custosops-v0.31.0-beginner-runbook-launch-audit
```

Add the remote if needed:

```powershell
git remote add origin <YOUR_PRIVATE_GITHUB_REPO_URL>
```

Push:

```powershell
git push -u origin master
git push origin --tags
```

If the remote already exists:

```powershell
git remote -v
git remote set-url origin <YOUR_PRIVATE_GITHUB_REPO_URL>
git push -u origin master
git push origin --tags
```

## Final manual review on GitHub

```text
- README renders correctly.
- LICENSE is visible.
- docs/onboarding, docs/demo, docs/launch, docs/portfolio, and docs/release are visible.
- LAUNCH_CUSTOSOPS.bat and STOP_CUSTOSOPS.bat are visible.
- No generated ZIPs or proof artifacts are tracked.
- No private local paths or workplace/customer names appear.
- Latest tag is present.
```

## Public release note

Use private first. Make public only after the final manual review is complete.