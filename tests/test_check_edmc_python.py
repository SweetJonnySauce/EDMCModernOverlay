from __future__ import annotations

from pathlib import Path

import pytest

from scripts import check_edmc_python


EXPECTED_VERSION = (3, 13, 9)
EXPECTED_ARCH = "32bit"


def _configure_runtime(monkeypatch, *, version: tuple[int, int, int], arch: str) -> None:
    monkeypatch.setattr(check_edmc_python, "_load_expected", lambda: (EXPECTED_VERSION, EXPECTED_ARCH))
    monkeypatch.setattr(check_edmc_python, "_current_version", lambda: version)
    monkeypatch.setattr(check_edmc_python, "_current_arch", lambda: arch)


def test_edmc_python_baseline_matches_current_upstream_tested_runtime() -> None:
    assert check_edmc_python.BASELINE_PATH.read_text(encoding="utf-8") == "3.13.9 32bit\n"


def test_matching_edmc_python_runtime_passes_without_override(monkeypatch, capsys) -> None:
    _configure_runtime(monkeypatch, version=(3, 13, 10), arch=EXPECTED_ARCH)
    monkeypatch.delenv(check_edmc_python.ALLOW_ENV, raising=False)

    check_edmc_python.main()

    assert "matches tested baseline 3.13.9+ in the 3.13 series (32bit)" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("version", "arch"),
    [
        ((3, 12, 10), EXPECTED_ARCH),
        ((3, 13, 8), EXPECTED_ARCH),
        ((3, 14, 0), EXPECTED_ARCH),
        (EXPECTED_VERSION, "64bit"),
    ],
)
def test_nonparity_runtime_fails_without_override(
    monkeypatch,
    version: tuple[int, int, int],
    arch: str,
) -> None:
    _configure_runtime(monkeypatch, version=version, arch=arch)
    monkeypatch.delenv(check_edmc_python.ALLOW_ENV, raising=False)

    with pytest.raises(SystemExit, match="does not match tested EDMC runtime"):
        check_edmc_python.main()


def test_nonparity_runtime_override_is_explicit_and_successful(monkeypatch, capsys) -> None:
    _configure_runtime(monkeypatch, version=(3, 12, 3), arch="64bit")
    monkeypatch.setenv(check_edmc_python.ALLOW_ENV, "1")

    check_edmc_python.main()

    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "does not match tested EDMC runtime" in output
    assert check_edmc_python.ALLOW_ENV in output


def test_nonparity_runtime_rejects_non_one_override(monkeypatch) -> None:
    _configure_runtime(monkeypatch, version=(3, 12, 3), arch="64bit")
    monkeypatch.setenv(check_edmc_python.ALLOW_ENV, "0")

    with pytest.raises(SystemExit, match="does not match tested EDMC runtime"):
        check_edmc_python.main()


def test_nonparity_ci_jobs_use_the_documented_override() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert 'ALLOW_EDMC_PYTHON_MISMATCH: "1"' in workflow
    assert 'python-version: "3.13"' in workflow
