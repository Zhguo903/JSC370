#!/usr/bin/env python3
"""Copy project docs/ to the Git repository root docs/ for GitHub Pages."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def git_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(out)


def main() -> int:
    project_dir = Path.cwd()
    src = project_dir / "docs"
    if not src.exists():
        raise FileNotFoundError("Could not find project docs/. Run quarto render first.")
    root = git_root()
    dst = root / "docs"
    if src.resolve() == dst.resolve():
        print("Project docs/ is already at the Git root docs/.")
        return 0
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Copied website from {src} to {dst}")
    print("Then run: git add docs && git commit -m 'Add final project website'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
