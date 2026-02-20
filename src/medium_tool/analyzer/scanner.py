"""Scan project directory tree, respecting .gitignore."""

from __future__ import annotations

from pathlib import Path

import pathspec

from medium_tool.models import FileInfo

# Always skip these directories regardless of .gitignore
ALWAYS_SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "venv", ".venv",
    "env", ".env", "dist", "build", ".next", ".nuxt", "target",
    ".gradle", ".idea", ".vscode", "vendor", "Pods",
    ".eggs", "*.egg-info",
}

# Binary / non-text extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pyc", ".pyo", ".class", ".o", ".obj",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}

MAX_FILE_SIZE = 512 * 1024  # 512 KB – skip huge files


def _load_gitignore(root: Path) -> pathspec.PathSpec | None:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None
    patterns = gitignore_path.read_text(errors="replace").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def _should_skip_dir(name: str) -> bool:
    return name in ALWAYS_SKIP_DIRS or name.startswith(".")


def scan_project(root: Path) -> list[FileInfo]:
    """Walk the project tree and return a list of FileInfo for text source files."""
    root = root.resolve()
    gitignore = _load_gitignore(root)
    results: list[FileInfo] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(root)
        parts = rel.parts

        # Skip hidden / always-skip directories
        if any(_should_skip_dir(p) for p in parts[:-1]):
            continue

        # Skip binary extensions
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Respect .gitignore
        if gitignore and gitignore.match_file(str(rel)):
            continue

        # Skip oversized files
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_SIZE or size == 0:
            continue

        # Count lines
        try:
            content = path.read_text(errors="replace")
            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        except Exception:
            continue

        results.append(FileInfo(
            path=path,
            relative_path=str(rel),
            extension=path.suffix.lower(),
            line_count=line_count,
            size_bytes=size,
        ))

    return results
