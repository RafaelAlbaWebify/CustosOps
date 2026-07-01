from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_hygiene_scripts_exist():
    expected = [
        ROOT / "scripts" / "custosops-doctor.ps1",
        ROOT / "scripts" / "custosops-dependency-audit.ps1",
        ROOT / "scripts" / "custosops-local-package.ps1",
        ROOT / "scripts" / "custosops-release-smoke.py",
        ROOT / "scripts" / "custosops-release-audit.ps1",
    ]

    for path in expected:
        assert path.exists(), f"Missing script: {path}"


def test_dependency_script_uses_safe_npm_audit_fix_only():
    script = (ROOT / "scripts" / "custosops-dependency-audit.ps1").read_text(encoding="utf-8-sig").lower()

    assert "npm.cmd audit fix" in script
    assert "audit fix --force" not in script


def test_local_package_script_mentions_excluded_runtime_artifacts():
    script = (ROOT / "scripts" / "custosops-local-package.ps1").read_text(encoding="utf-8-sig").lower()

    assert "node_modules" in script
    assert "backend virtual environment" in script
    assert "frontend dist" in script
    assert "excludes" in script
