"""Package the Dify plugin into a distributable zip archive.

Creates dist/botos3-<version>.zip containing required runtime files.
"""

from __future__ import annotations

import os
import zipfile
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"

INCLUDE_PATTERNS = {
    "manifest.yaml",
    "README.md",
    "PRIVACY.md",
    "GUIDE.md",
    "main.py",
    "requirements.txt",
    "icon.svg",
}

INCLUDE_DIRS = {
    "provider",
    "tools",
    "_assets",  # if present
}

EXCLUDE_NAME_PREFIXES = {".git", ".venv", "__pycache__"}


def read_version() -> str:
    manifest = (ROOT / "manifest.yaml").read_text(encoding="utf-8")
    m = re.search(r"^version:\s*([\w\.\-]+)", manifest, re.MULTILINE)
    if not m:
        print("Unable to find version in manifest.yaml", file=sys.stderr)
        return "0.0.0"
    return m.group(1)


def should_include_file(path: pathlib.Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    # Explicit file patterns
    if rel in INCLUDE_PATTERNS:
        return True
    # Directory contents
    parts = rel.split("/")
    if parts[0] in INCLUDE_DIRS:
        # exclude caches
        if any(p.startswith(tuple(EXCLUDE_NAME_PREFIXES)) for p in parts):
            return False
        return True
    return False


def build_zip():
    version = read_version()
    DIST.mkdir(exist_ok=True)
    out_path = DIST / f"botos3-{version}.zip"
    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_NAME_PREFIXES]
            for name in files:
                fpath = pathlib.Path(root) / name
                if should_include_file(fpath):
                    arcname = fpath.relative_to(ROOT).as_posix()
                    zf.write(fpath, arcname)
    print(f"Created {out_path}")


if __name__ == "__main__":
    build_zip()
