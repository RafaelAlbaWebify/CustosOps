# CustosOps v1.1.0 Release Preparation

## Release goal

Publish the completed TRACE-aligned portfolio interface and the post-v1 maintenance baseline as CustosOps `v1.1.0`.

## Included since v1.0.0

- TRACE-compatible light operational-console visual system.
- Responsive navigation and workspace layouts.
- Operations and Governance navigation grouping.
- Consistent Overview, evidence, Reports, Archive, Run History, and Redaction surfaces.
- Final ten-workspace screenshot proof.
- FastAPI 0.139.2 maintenance update.
- Vite 8.1.5 maintenance update.
- Five-minute evaluator path.
- Keyboard, accessible-name, mobile-overflow, and light-theme contract tests.
- Optional committed Playwright visual-regression baseline.

## Release gates

- [ ] README reflects the completed release state.
- [ ] Reviewed GUI screenshots are committed under `docs/images/`.
- [ ] Five-minute evaluator path is linked from the README.
- [ ] Full Linux and Windows CI passes on the exact candidate SHA.
- [ ] Accessibility and responsive-contract tests pass.
- [ ] Reviewed Playwright baseline is committed and passes with `CUSTOSOPS_VISUAL_REGRESSION=1`.
- [ ] Fresh post-GUI Windows acceptance package passes.
- [ ] Acceptance logs, paths, reports, and screenshots are manually reviewed for public safety.
- [ ] `v1.1.0` annotated tag and GitHub release are created at the accepted SHA.
- [ ] Release page, tag, repository description, evaluator path, and public screenshots are verified.

## Draft release notes

CustosOps v1.1.0 packages the completed portfolio interface and post-v1 maintenance baseline.

### Visual and evaluator experience

- Replaced the original dark fixed-width dashboard treatment with a responsive TRACE-aligned operational-console interface.
- Added light surfaces, restrained semantic colors, compact navigation, and consistent workspace hierarchy.
- Added a five-minute evaluator path for recruiters, hiring managers, and technical reviewers.
- Added reviewed GUI screenshots to the public project documentation.

### Engineering assurance

- Added keyboard reachability, accessible-name, mobile-overflow, and visual-contract browser tests.
- Added an opt-in committed Playwright visual-regression baseline.
- Retained Linux browser verification, Windows PowerShell/build validation, dependency audit, supply-chain inventory, and clean-machine acceptance.

### Maintenance

- FastAPI 0.139.2.
- Vite 8.1.5.

### Product boundary

CustosOps remains local-first, read-only, synthetic/public-safe, and explicitly non-remediating. It is not presented as a SIEM, EDR, vulnerability scanner, MDR service, or live Microsoft 365 tenant monitor.
