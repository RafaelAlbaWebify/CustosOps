# Private-first GitHub Push Guide

This guide prepares CustosOps for GitHub publication. It does not require the repository to be public.

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
custosops-v0.29.1-final-github-portfolio-package
```

Add the remote:

```powershell
git remote add origin <YOUR_PRIVATE_GITHUB_REPO_URL>
```

Push:

```powershell
git push -u origin master --tags
```

If the remote already exists:

```powershell
git remote -v
git remote set-url origin <YOUR_PRIVATE_GITHUB_REPO_URL>
git push -u origin master --tags
```

## Final manual review on GitHub

```text
- README renders correctly.
- LICENSE is visible.
- docs/demo and docs/release are visible.
- No generated ZIPs or proof artifacts are tracked.
- No private local paths or workplace/customer names appear.
- Latest tag is present.
```

## Public release note

Use private first. Make public only after the final manual review is complete.