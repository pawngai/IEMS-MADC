"""Repository-artifact hygiene guard.

Fails CI if committed runtime artifacts, root-level debug scripts, archived
legacy directories, or completed-migration handoff docs are reintroduced.

Scope: anything tracked by git in the repo root, the backend, or the docs tree.
The repo is considered post-migration, so these surfaces should stay gone.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_no_committed_runtime_logs() -> None:
    files = _tracked_files()
    log_like = re.compile(r"(?:^|/)([^/]+\.(?:log|out|err))$")
    violations = [
        path
        for path in files
        if log_like.search(path) and not path.startswith("docs/")
    ]
    assert not violations, (
        "Runtime logs (*.log, *.out, *.err) must not be committed. "
        "Add them to .gitignore and git rm:\n" + "\n".join(sorted(violations))
    )


def test_no_committed_test_reports_or_uploads() -> None:
    files = _tracked_files()
    forbidden_prefixes = ("test_reports/", "uploads/")
    violations = [
        path
        for path in files
        if any(path.startswith(prefix) for prefix in forbidden_prefixes)
    ]
    assert not violations, (
        "test_reports/ and uploads/ directories must not contain committed files:\n"
        + "\n".join(sorted(violations))
    )


def test_no_root_debug_admin_scripts() -> None:
    files = _tracked_files()
    pattern = re.compile(r"^(_check_|_debug_|_reset_|_seed_|_update_|_remove_|onboard_).*\.py$")
    violations = [path for path in files if pattern.match(path)]
    violations += [path for path in files if path == "scan-cleanup.ps1"]
    assert not violations, (
        "Root-level debug/admin/reset scripts are forbidden. "
        "Move operational tooling to backend/scripts/ and harden it:\n"
        + "\n".join(sorted(violations))
    )


def test_no_root_loose_test_binaries() -> None:
    files = _tracked_files()
    pattern = re.compile(r"^test_(?:photo|sig|signature|upload)\.[a-z0-9]+$")
    violations = [path for path in files if pattern.match(path)]
    violations += [path for path in files if path == "structure.txt"]
    assert not violations, (
        "Loose test binaries and the structure.txt dump must not be committed:\n"
        + "\n".join(sorted(violations))
    )


def test_no_legacy_handoff_or_migration_docs() -> None:
    files = _tracked_files()
    forbidden = {
        "backend/LEGACY_MIGRATION_CHECKLIST.md",
        "backend/LEGACY_REMOVAL_CANDIDATES.md",
        "backend/PR_HANDOFF_LEGACY_CUTOVER.md",
        "docs/reference/MIGRATION_MAP.md",
        "docs/reference/REFACTOR_SUMMARY.md",
    }
    forbidden_prefixes = (
        "docs/archives/",
        # docs/refactor/ holds the ACTIVE context-minimization migration
        # inventories (Phase 0). Re-add this prefix once that migration is fully
        # completed and its handoff docs are archived.
        "docs/releases/",
        "backend/scripts/archived/",
    )
    violations = sorted(
        path
        for path in files
        if path in forbidden or any(path.startswith(p) for p in forbidden_prefixes)
    )
    assert not violations, (
        "Completed-migration handoff docs and archived script trees must stay removed:\n"
        + "\n".join(violations)
    )


def test_no_deploy_bundle_zips_at_root() -> None:
    files = _tracked_files()
    pattern = re.compile(r"^deploy-.*\.zip$")
    violations = [path for path in files if pattern.match(path)]
    assert not violations, (
        "Deploy bundle zips must not be committed:\n" + "\n".join(sorted(violations))
    )


def test_no_mojibake_in_source_files() -> None:
    """Tracked source files must not contain UTF-8/Win-1252 round-trip artifacts.

    Sequences like ``â€¢``, ``â€“``, ``â€”``, ``Ã‚`` are signs that text was
    decoded with the wrong codec on a previous edit. They render as garbage
    for users and are almost always unintended.

    The scan walks ``git ls-files`` so generated/local artifacts (e.g. a
    Vite ``frontend/dist`` build) and uncommitted scratch files do not
    create noise. The hygiene-test file itself is excluded because it
    intentionally embeds the mojibake byte sequences it scans for.
    """

    # Each sequence is the UTF-8 read of bytes that originated as a CP1252
    # double-encoding of a punctuation character.
    bad_sequences = (
        "â€¢",          # bullet "â€¢"
        "â€“",          # en dash "â€“"
        "â€”",          # em dash "â€”"
        "Ã‚",                # NBSP-leading "Ã‚"
        "Ãƒ",                # umlaut-leading "Ãƒ"
    )
    scan_extensions = {".py", ".md", ".jsx", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml"}
    self_relative = Path(__file__).relative_to(REPO_ROOT).as_posix()

    tracked = _tracked_files()
    violations: list[str] = []
    for rel in tracked:
        if rel == self_relative:
            continue
        if not any(rel.endswith(ext) for ext in scan_extensions):
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for bad in bad_sequences:
            if bad in text:
                violations.append(f"{rel}: contains mojibake sequence")
                break

    assert not violations, (
        "Mojibake / UTF-8 round-trip artifacts detected in source files. "
        "Re-save the file as UTF-8 with the intended characters:\n"
        + "\n".join(sorted(violations))
    )
