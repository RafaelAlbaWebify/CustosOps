# Milestone 23 - Dependency and Packaging Hygiene

## Goal

Improve CustosOps local maintainability after the v0.21.0 stable checkpoint.

This milestone does not add new evidence features.

## Added

- CustosOps doctor script.
- Dependency audit script.
- Local package script.
- Operations quickstart documentation.
- Frontend npm audit helper scripts.
- Backend inventory test for hygiene scripts.
- Local package ZIP generation.

## Dependency policy

Safe dependency remediation may use npm audit fix.

Forced remediation is not used.

Forced upgrades can introduce breaking changes and should only be considered in a dedicated maintenance task after reviewing the dependency tree.

## Packaging policy

The local package includes source code, docs, samples, scripts, metadata, dependency audit output, and release smoke output.

The local package excludes heavy runtime artifacts such as node_modules, backend virtual environment, frontend dist, git internals, report archive contents, and caches.

## Completion criteria

- Backend tests pass.
- Frontend build passes.
- Doctor script runs.
- Dependency audit script runs.
- Local package script creates a ZIP.
- Git working tree is clean after commit.
- Local hygiene tag exists.
