"""Combine all analysis results into a prompt-ready summary."""

from __future__ import annotations

from pathlib import Path

from medium_tool.analyzer.extractor import (
    extract_config_snippets,
    extract_dependencies,
    extract_imports,
    extract_interesting_snippets,
    extract_readme,
)
from medium_tool.analyzer.language import assign_languages, detect_project_types
from medium_tool.analyzer.scanner import scan_project
from medium_tool.models import ProjectAnalysis


def analyze_project(root: Path) -> ProjectAnalysis:
    """Run full project analysis and return a ProjectAnalysis."""
    root = root.resolve()
    name = root.name

    # 1. Scan files
    files = scan_project(root)

    # 2. Detect languages
    lang_counts = assign_languages(files)
    primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else None

    # 3. Detect project types and frameworks
    project_types, frameworks = detect_project_types(root, files)

    # 4. Extract metadata
    readme = extract_readme(root)
    dependencies = extract_dependencies(root)
    config_snippets = extract_config_snippets(root, files)
    code_snippets = extract_interesting_snippets(files)
    imports = extract_imports(files)

    all_snippets = config_snippets + code_snippets
    total_lines = sum(f.line_count for f in files)

    analysis = ProjectAnalysis(
        root_path=root,
        name=name,
        files=files,
        languages=lang_counts,
        primary_language=primary_lang,
        project_types=project_types,
        frameworks=frameworks,
        dependencies=dependencies[:50],
        readme_content=readme,
        snippets=all_snippets,
        total_files=len(files),
        total_lines=total_lines,
    )

    # 5. Build human-readable summary
    analysis.summary = build_summary(analysis, imports)
    return analysis


def build_summary(analysis: ProjectAnalysis, imports: list[str]) -> str:
    """Build a text summary of the project for use as Claude prompt context."""
    parts: list[str] = []

    parts.append(f"# Project: {analysis.name}")
    parts.append(f"Total files: {analysis.total_files} | Total lines: {analysis.total_lines}")

    if analysis.project_types:
        types_str = ", ".join(t.value for t in analysis.project_types)
        parts.append(f"Project types: {types_str}")

    if analysis.primary_language:
        lang_breakdown = ", ".join(
            f"{lang.value}: {count}" for lang, count in
            sorted(analysis.languages.items(), key=lambda x: x[1], reverse=True)[:6]
        )
        parts.append(f"Primary language: {analysis.primary_language.value}")
        parts.append(f"Language breakdown: {lang_breakdown}")

    if analysis.frameworks:
        parts.append(f"Frameworks/Tools: {', '.join(analysis.frameworks)}")

    if analysis.dependencies:
        deps_str = ", ".join(analysis.dependencies[:30])
        parts.append(f"Dependencies: {deps_str}")

    if analysis.readme_content:
        parts.append(f"\n## README (excerpt)\n{analysis.readme_content}")

    if imports:
        parts.append(f"\n## Import statements (sample)\n" + "\n".join(imports[:40]))

    if analysis.snippets:
        parts.append("\n## Key code snippets")
        for snippet in analysis.snippets:
            lang_label = snippet.language.value if snippet.language else "text"
            parts.append(f"\n### {snippet.file_path}")
            parts.append(f"```{lang_label.lower()}")
            parts.append(snippet.content)
            parts.append("```")

    # File tree (truncated)
    parts.append("\n## File tree")
    for f in analysis.files[:80]:
        parts.append(f"  {f.relative_path}")
    if len(analysis.files) > 80:
        parts.append(f"  ... and {len(analysis.files) - 80} more files")

    return "\n".join(parts)
