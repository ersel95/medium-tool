"""Detect programming languages and project types."""

from __future__ import annotations

from pathlib import Path

from medium_tool.models import FileInfo, Language, ProjectType

# Extension → Language mapping
EXTENSION_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    ".h": Language.C,
    ".c": Language.C,
    ".cs": Language.CSHARP,
    ".rb": Language.RUBY,
    ".php": Language.PHP,
    ".swift": Language.SWIFT,
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    ".scala": Language.SCALA,
    ".dart": Language.DART,
    ".lua": Language.LUA,
    ".sh": Language.SHELL,
    ".bash": Language.SHELL,
    ".zsh": Language.SHELL,
    ".html": Language.HTML,
    ".htm": Language.HTML,
    ".css": Language.CSS,
    ".scss": Language.CSS,
    ".less": Language.CSS,
    ".sql": Language.SQL,
}

# Marker files → (ProjectType, frameworks)
MARKER_FILES: dict[str, tuple[ProjectType | None, list[str]]] = {
    "package.json": (None, []),  # detect from content
    "requirements.txt": (None, []),
    "pyproject.toml": (None, []),
    "setup.py": (Language.PYTHON, []),
    "Cargo.toml": (None, ["Rust/Cargo"]),
    "go.mod": (None, ["Go Modules"]),
    "pom.xml": (None, ["Maven"]),
    "build.gradle": (None, ["Gradle"]),
    "Gemfile": (None, ["Ruby/Bundler"]),
    "composer.json": (None, ["PHP/Composer"]),
    "Dockerfile": (ProjectType.DEVOPS, ["Docker"]),
    "docker-compose.yml": (ProjectType.DEVOPS, ["Docker Compose"]),
    "docker-compose.yaml": (ProjectType.DEVOPS, ["Docker Compose"]),
    "Makefile": (None, ["Make"]),
    "CMakeLists.txt": (None, ["CMake"]),
    "terraform.tf": (ProjectType.DEVOPS, ["Terraform"]),
    "serverless.yml": (ProjectType.API, ["Serverless Framework"]),
    "Podfile": (ProjectType.MOBILE, ["CocoaPods"]),
    "pubspec.yaml": (ProjectType.MOBILE, ["Flutter"]),
}

# Content-based framework detection for package.json
PACKAGE_JSON_FRAMEWORKS: dict[str, tuple[ProjectType, str]] = {
    "react": (ProjectType.WEB_FRONTEND, "React"),
    "next": (ProjectType.FULLSTACK, "Next.js"),
    "vue": (ProjectType.WEB_FRONTEND, "Vue.js"),
    "nuxt": (ProjectType.FULLSTACK, "Nuxt.js"),
    "angular": (ProjectType.WEB_FRONTEND, "Angular"),
    "svelte": (ProjectType.WEB_FRONTEND, "Svelte"),
    "express": (ProjectType.WEB_BACKEND, "Express.js"),
    "fastify": (ProjectType.WEB_BACKEND, "Fastify"),
    "nestjs": (ProjectType.WEB_BACKEND, "NestJS"),
    "electron": (ProjectType.OTHER, "Electron"),
    "react-native": (ProjectType.MOBILE, "React Native"),
    "expo": (ProjectType.MOBILE, "Expo"),
}

# Content-based framework detection for Python
PYTHON_FRAMEWORKS: dict[str, tuple[ProjectType, str]] = {
    "django": (ProjectType.WEB_BACKEND, "Django"),
    "flask": (ProjectType.WEB_BACKEND, "Flask"),
    "fastapi": (ProjectType.API, "FastAPI"),
    "starlette": (ProjectType.API, "Starlette"),
    "celery": (ProjectType.WEB_BACKEND, "Celery"),
    "pandas": (ProjectType.DATA_SCIENCE, "Pandas"),
    "numpy": (ProjectType.DATA_SCIENCE, "NumPy"),
    "tensorflow": (ProjectType.DATA_SCIENCE, "TensorFlow"),
    "pytorch": (ProjectType.DATA_SCIENCE, "PyTorch"),
    "torch": (ProjectType.DATA_SCIENCE, "PyTorch"),
    "scikit-learn": (ProjectType.DATA_SCIENCE, "scikit-learn"),
    "click": (ProjectType.CLI, "Click"),
    "typer": (ProjectType.CLI, "Typer"),
    "argparse": (ProjectType.CLI, "argparse"),
}


def detect_language(file_info: FileInfo) -> Language | None:
    """Assign a Language to a FileInfo based on its extension."""
    return EXTENSION_MAP.get(file_info.extension)


def assign_languages(files: list[FileInfo]) -> dict[Language, int]:
    """Detect languages for all files, return language → count mapping."""
    counts: dict[Language, int] = {}
    for f in files:
        lang = detect_language(f)
        f.language = lang
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return counts


def detect_project_types(root: Path, files: list[FileInfo]) -> tuple[list[ProjectType], list[str]]:
    """Detect project types and frameworks from marker files and dependency files."""
    project_types: set[ProjectType] = set()
    frameworks: list[str] = []
    rel_paths = {f.relative_path for f in files}

    for marker, (ptype, fws) in MARKER_FILES.items():
        if marker in rel_paths or (root / marker).exists():
            if ptype:
                project_types.add(ptype)
            frameworks.extend(fws)

    # Inspect package.json for JS/TS frameworks
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            content = pkg_json.read_text(errors="replace").lower()
            for key, (ptype, fw_name) in PACKAGE_JSON_FRAMEWORKS.items():
                if f'"{key}"' in content:
                    project_types.add(ptype)
                    frameworks.append(fw_name)
        except Exception:
            pass

    # Inspect Python dependency files
    for dep_file in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile"):
        dep_path = root / dep_file
        if dep_path.exists():
            try:
                content = dep_path.read_text(errors="replace").lower()
                for key, (ptype, fw_name) in PYTHON_FRAMEWORKS.items():
                    if key in content:
                        project_types.add(ptype)
                        frameworks.append(fw_name)
            except Exception:
                pass

    # Deduplicate frameworks while preserving order
    seen = set()
    unique_frameworks = []
    for fw in frameworks:
        if fw not in seen:
            seen.add(fw)
            unique_frameworks.append(fw)

    return sorted(project_types, key=lambda t: t.value), unique_frameworks
