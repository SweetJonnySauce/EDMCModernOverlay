"""Resolve latest stable Windows Python installer metadata for release builds."""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import tempfile
import urllib.request

PYTHON_FTP_INDEX = "https://www.python.org/ftp/python/"
ARCH = "amd64"


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def download_file(url: str, destination: pathlib.Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_versions(index_html: str) -> list[str]:
    versions: list[str] = []
    for match in re.finditer(r'href="(?P<ver>\d+\.\d+\.\d+)/"', index_html):
        versions.append(match.group("ver"))
    return versions


def version_key(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def filter_stable_versions(versions: list[str]) -> list[str]:
    stable: list[str] = []
    for ver in versions:
        try:
            major, minor, patch = version_key(ver)
        except Exception:
            continue
        if major != 3:
            continue
        if (major, minor) < (3, 10):
            continue
        stable.append(ver)
    stable.sort(key=version_key, reverse=True)
    return stable


def has_installer(version: str, listing_html: str) -> bool:
    filename = f"python-{version}-{ARCH}.exe"
    return filename in listing_html


def select_latest_with_installer(versions: list[str]) -> str:
    stable = filter_stable_versions(versions)
    if not stable:
        raise RuntimeError("No stable Python 3.10+ releases found in index.")
    for ver in stable:
        try:
            listing = fetch_text(f"{PYTHON_FTP_INDEX}{ver}/")
        except Exception:
            continue
        if has_installer(ver, listing):
            return ver
    raise RuntimeError("No Python release with a Windows amd64 installer was found.")


def build_table(version: str, url: str, sha256: str) -> str:
    return "\n".join(
        [
            "[tool.windows_python_install]",
            f'version = "{version}"',
            f'arch = "{ARCH}"',
            f'url = "{url}"',
            f'sha256 = "{sha256}"',
            r'target_dir_template = "%LOCALAPPDATA%\\Programs\\Python\\Python{MAJOR}{MINOR}"',
            r'python_exe_template = "%LOCALAPPDATA%\\Programs\\Python\\Python{MAJOR}{MINOR}\\python.exe"',
            "",
        ]
    )


def update_pyproject(path: pathlib.Path, table_block: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^\[tool\.windows_python_install\][\s\S]*?(?=^\[|\Z)", re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(table_block, text)
    else:
        updated = text.rstrip() + "\n\n" + table_block
    if not updated.endswith("\n"):
        updated += "\n"
    path.write_text(updated, encoding="utf-8")


def write_metadata_file(path: pathlib.Path, table_block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(table_block, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    parser.add_argument(
        "--metadata-output",
        default="windows_python_install.toml",
        help="Path to write the standalone Windows Python installer metadata file.",
    )
    args = parser.parse_args()

    pyproject_path = pathlib.Path(args.pyproject)
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    metadata_path = pathlib.Path(args.metadata_output)
    if not metadata_path.is_absolute():
        metadata_path = pyproject_path.parent / metadata_path

    index_html = fetch_text(PYTHON_FTP_INDEX)
    version = select_latest_with_installer(parse_versions(index_html))
    installer_url = f"{PYTHON_FTP_INDEX}{version}/python-{version}-{ARCH}.exe"

    with tempfile.TemporaryDirectory() as tmpdir:
        installer_path = pathlib.Path(tmpdir) / f"python-{version}-{ARCH}.exe"
        download_file(installer_url, installer_path)
        sha256 = sha256_file(installer_path)

    table_block = build_table(version, installer_url, sha256)
    update_pyproject(pyproject_path, table_block)
    write_metadata_file(metadata_path, table_block)

    print(f"Resolved Python version: {version}")
    print(f"Installer URL: {installer_url}")
    print(f"SHA-256: {sha256}")
    print(f"Wrote metadata file: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
