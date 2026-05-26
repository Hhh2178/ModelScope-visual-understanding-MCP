from __future__ import annotations

import re
from pathlib import Path


PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]+"),
    re.compile("(?<![\\w.-])" + "/" + "home" + "/"),
    re.compile("(?<![\\w.-])" + "/" + "mnt" + "/"),
    re.compile(r"~/\.hermes"),
]

SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", "state"}


def scan(root: Path | str = ".") -> list[tuple[Path, int, str]]:
    project_root = Path(root)
    findings: list[tuple[Path, int, str]] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == "portability_check.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in PATH_PATTERNS):
                findings.append((path, line_no, line.strip()))
    return findings


def main() -> None:
    findings = scan(Path.cwd())
    if not findings:
        print("PASS: no machine-specific absolute paths found")
        return
    for path, line_no, line in findings:
        print(f"{path}:{line_no}: {line}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
