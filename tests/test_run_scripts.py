"""Sanity checks on the run scripts themselves.

There is no bash or PowerShell interpreter guaranteed to be available in
every environment this test suite runs in, so these are structural
checks (the scripts exist, are non-empty, and have balanced
brackets/quotes), not a functional test of either script. See
docs/LIMITATIONS.md: scripts/run.ps1 has not been executed on a real
Windows machine.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _balanced(text: str, open_char: str, close_char: str) -> bool:
    depth = 0
    for ch in text:
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
        if depth < 0:
            return False
    return depth == 0


def test_run_sh_exists_and_is_nonempty():
    path = REPO_ROOT / "scripts" / "run.sh"
    assert path.exists()
    text = path.read_text()
    assert "#!/usr/bin/env bash" in text
    assert len(text) > 500


def test_run_sh_braces_are_balanced():
    # Not checking parens: bash `case ... in pattern) ... ;; esac` blocks
    # legitimately contain a ')' with no matching '(', so a naive paren
    # balance check would misfire on valid bash.
    text = (REPO_ROOT / "scripts" / "run.sh").read_text()
    assert _balanced(text, "{", "}")


def test_run_ps1_exists_and_is_nonempty():
    path = REPO_ROOT / "scripts" / "run.ps1"
    assert path.exists()
    text = path.read_text()
    assert "SmokeOnly" in text
    assert "SkipTests" in text
    assert len(text) > 500


def test_run_ps1_braces_and_parens_are_balanced():
    text = (REPO_ROOT / "scripts" / "run.ps1").read_text()
    assert _balanced(text, "{", "}")
    assert _balanced(text, "(", ")")


def _bash_actually_works() -> bool:
    """True only if invoking bash actually runs a shell, not just if it's on PATH.

    On Windows, ``bash`` is frequently a relay stub at
    C:\\Windows\\System32\\bash.exe that launches WSL - it is found by
    shutil.which even when no WSL distro is installed, and then fails at
    invocation time with an unrelated "execvpe(/bin/bash) failed" error.
    That is an environment problem, not a run.sh syntax problem, so it
    must not be reported as this test failing.
    """
    if shutil.which("bash") is None:
        return False
    try:
        result = subprocess.run(
            ["bash", "-c", "true"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


@pytest.mark.skipif(not _bash_actually_works(), reason="bash not available or not runnable")
def test_run_sh_passes_bash_syntax_check():
    """A real syntax check (bash -n), not just balanced-bracket heuristics."""
    result = subprocess.run(
        ["bash", "-n", str(REPO_ROOT / "scripts" / "run.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_run_ps1_covers_the_same_seven_phases_as_run_sh():
    ps1_text = (REPO_ROOT / "scripts" / "run.ps1").read_text()
    for phase in [
        "[1/7]",
        "[2/7]",
        "[3/7]",
        "[4/7]",
        "[5/7]",
        "[6/7]",
        "[7/7]",
    ]:
        assert phase in ps1_text, f"missing phase marker {phase} in run.ps1"
