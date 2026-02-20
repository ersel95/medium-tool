"""Extract code snippets, patterns, and metadata from project files."""

from __future__ import annotations

import re
from pathlib import Path

from medium_tool.models import CodeSnippet, FileInfo, Language

# Files to always read in full (or partially) for context
IMPORTANT_FILES = {
    "README.md", "README.rst", "README.txt", "README",
    "CHANGELOG.md", "CONTRIBUTING.md",
}

CONFIG_FILES = {
    "package.json", "tsconfig.json", "pyproject.toml", "setup.cfg",
    "setup.py", "Cargo.toml", "go.mod", "build.gradle", "pom.xml",
    "Gemfile", "composer.json", "pubspec.yaml", ".eslintrc.json",
    "webpack.config.js", "vite.config.ts", "vite.config.js",
    "next.config.js", "next.config.mjs",
}

MAX_SNIPPET_LINES = 60
MAX_README_CHARS = 3000
MAX_CONFIG_CHARS = 2000


def extract_readme(root: Path) -> str:
    """Read README content, truncated if needed."""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        readme_path = root / name
        if readme_path.exists():
            try:
                content = readme_path.read_text(errors="replace")
                return content[:MAX_README_CHARS]
            except Exception:
                continue
    return ""


def extract_dependencies(root: Path) -> list[str]:
    """Extract top-level dependency names from common dep files."""
    deps: list[str] = []

    # package.json
    pkg = root / "package.json"
    if pkg.exists():
        try:
            content = pkg.read_text(errors="replace")
            # Simple regex extraction of dependency names
            for match in re.finditer(r'"(dependencies|devDependencies)"\s*:\s*\{([^}]*)\}', content):
                block = match.group(2)
                for dep_match in re.finditer(r'"([^"]+)"\s*:', block):
                    deps.append(dep_match.group(1))
        except Exception:
            pass

    # requirements.txt
    req = root / "requirements.txt"
    if req.exists():
        try:
            for line in req.read_text(errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    name = re.split(r"[>=<!\[;]", line)[0].strip()
                    if name:
                        deps.append(name)
        except Exception:
            pass

    # pyproject.toml dependencies
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(errors="replace")
            in_deps = False
            for line in content.splitlines():
                if re.match(r'\s*dependencies\s*=\s*\[', line):
                    in_deps = True
                    continue
                if in_deps:
                    if "]" in line:
                        in_deps = False
                        continue
                    m = re.search(r'"([^"]+)"', line)
                    if m:
                        name = re.split(r"[>=<!\[;]", m.group(1))[0].strip()
                        if name:
                            deps.append(name)
        except Exception:
            pass

    return deps


def _read_head(path: Path, max_lines: int = MAX_SNIPPET_LINES) -> str:
    """Read up to max_lines from a file."""
    try:
        lines = path.read_text(errors="replace").splitlines()[:max_lines]
        return "\n".join(lines)
    except Exception:
        return ""


def extract_config_snippets(root: Path, files: list[FileInfo]) -> list[CodeSnippet]:
    """Extract content from config files."""
    snippets: list[CodeSnippet] = []
    seen = set()

    for f in files:
        name = Path(f.relative_path).name
        if name in CONFIG_FILES and name not in seen:
            seen.add(name)
            content = _read_head(f.path)
            if content:
                snippets.append(CodeSnippet(
                    file_path=f.relative_path,
                    language=f.language or Language.OTHER,
                    content=content[:MAX_CONFIG_CHARS],
                    description=f"Config file: {name}",
                ))
    return snippets


def _score_file(f: FileInfo) -> float:
    """Score a file for 'interestingness' – higher = more interesting snippet candidate."""
    score = 0.0
    # Prefer medium-sized files (not too small, not too large)
    if 20 <= f.line_count <= 300:
        score += 10
    elif f.line_count > 300:
        score += 3
    # Prefer source files in src/ or lib/ or app/
    rp = f.relative_path.lower()
    if any(rp.startswith(d) for d in ("src/", "lib/", "app/", "pkg/", "cmd/")):
        score += 5
    # Prefer entry points
    name = Path(f.relative_path).name.lower()
    if name in ("main.py", "app.py", "index.ts", "index.js", "main.go", "main.rs", "server.py", "server.ts"):
        score += 15
    # Prefer files with certain patterns in name
    for kw in ("handler", "service", "controller", "router", "model", "schema", "api", "core", "engine"):
        if kw in name:
            score += 8
            break
    return score


def extract_interesting_snippets(
    files: list[FileInfo],
    max_snippets: int = 8,
) -> list[CodeSnippet]:
    """Select the most interesting source files and extract snippets."""
    # Filter to actual source files
    source_files = [f for f in files if f.language and f.language not in (Language.HTML, Language.CSS, Language.SQL)]
    source_files.sort(key=_score_file, reverse=True)

    snippets: list[CodeSnippet] = []
    for f in source_files[:max_snippets]:
        content = _read_head(f.path, MAX_SNIPPET_LINES)
        if content.strip():
            snippets.append(CodeSnippet(
                file_path=f.relative_path,
                language=f.language or Language.OTHER,
                content=content,
                description=f"Source: {f.relative_path} ({f.line_count} lines)",
            ))
    return snippets


def extract_imports(files: list[FileInfo], max_files: int = 20) -> list[str]:
    """Extract unique import/require statements across top files."""
    imports: set[str] = set()
    source_files = [f for f in files if f.language and f.line_count > 5]
    source_files.sort(key=lambda f: f.line_count, reverse=True)

    for f in source_files[:max_files]:
        try:
            content = f.path.read_text(errors="replace")
        except Exception:
            continue

        for line in content.splitlines()[:100]:
            line = line.strip()
            # Python imports
            if line.startswith("import ") or line.startswith("from "):
                imports.add(line)
            # JS/TS imports
            elif line.startswith("import ") or ("require(" in line):
                imports.add(line)
            # Go imports
            elif line.startswith("import (") or (line.startswith('"') and f.language == Language.GO):
                imports.add(line)
            # Rust use
            elif line.startswith("use "):
                imports.add(line)

        if len(imports) > 200:
            break

    return sorted(imports)[:100]
