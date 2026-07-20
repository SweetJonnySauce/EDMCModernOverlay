from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_makefile_uses_the_root_developer_environment() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert ".venv/bin/python" in makefile
    assert "else echo python3" in makefile
    assert "overlay_client/.venv" not in makefile


def test_ci_dependency_source_declares_required_developer_tools() -> None:
    requirements = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (
            REPO_ROOT / "requirements" / "dev.txt",
            REPO_ROOT / "overlay_client" / "requirements" / "base.txt",
            REPO_ROOT / "overlay_client" / "requirements" / "wayland.txt",
        )
    )

    assert "-r ../overlay_client/requirements/base.txt" in requirements
    assert "-r ../overlay_client/requirements/wayland.txt" in requirements
    assert all(name in requirements for name in ("pytest", "ruff", "mypy", "pyqt6"))


def test_active_developer_documentation_uses_the_root_environment() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    implementation_plan = (
        REPO_ROOT
        / "docs"
        / "planning"
        / "2026-07-17-fix219-architecture-convergence"
        / "implementation"
        / "plan.md"
    ).read_text(encoding="utf-8")

    assert "python -m pip install -r requirements/dev.txt" in agents
    assert "requirements-dev.txt" not in agents
    assert r".venv\Scripts\python scripts\run_pytest_safe_windows.py" in agents
    assert "overlay_client/.venv/bin/python" not in implementation_plan
    assert ".venv/bin/python" in implementation_plan
