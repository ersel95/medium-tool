"""CLI entry point – orchestrates the full pipeline."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from medium_tool.config import load_config
from medium_tool.models import ImageStyle

console = Console()


@click.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--language", "-l", type=click.Choice(["en", "tr"]), default="en", help="Article language")
@click.option("--topic-count", "-n", type=int, default=5, help="Number of topics to generate")
@click.option("--image-style", type=click.Choice(["unsplash", "dalle", "both"]), default="both", help="Image source")
@click.option("--topic-index", "-t", type=int, default=None, help="Select a topic by index (0-based)")
@click.option("--output", "-o", type=click.Path(), default=None, help="Save article to file")
@click.option("--dry-run", is_flag=True, default=False, help="Only analyze + generate topics, skip article writing")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose logging")
def cli(
    path: str,
    language: str,
    topic_count: int,
    image_style: str,
    topic_index: int | None,
    output: str | None,
    dry_run: bool,
    verbose: bool,
):
    """Analyze a code project and generate a Medium article."""
    project_path = Path(path)
    img_style = ImageStyle(image_style)

    # ── Config ──────────────────────────────────────────────
    config = load_config()

    # ── Step 1: Analyze ────────────────────────────────────
    from medium_tool.analyzer.summarizer import analyze_project

    with _spinner("Analyzing project..."):
        analysis = analyze_project(project_path)

    _show_analysis_summary(analysis, verbose)

    # ── Step 2: Generate Topics ────────────────────────────
    from medium_tool.generator.topics import generate_topics

    with _spinner("Generating topic ideas..."):
        topics = generate_topics(
            analysis,
            count=topic_count,
            language=language,
        )

    _show_topics(topics)

    if dry_run:
        console.print("\n[yellow]--dry-run[/yellow]: stopping after topic generation.")
        return

    # ── Step 3: Select Topic ───────────────────────────────
    if topic_index is not None:
        if topic_index < 0 or topic_index >= len(topics):
            console.print(f"[red]✗[/red] Topic index {topic_index} out of range (0-{len(topics)-1})")
            raise SystemExit(1)
        selected = topics[topic_index]
    else:
        # Interactive selection
        console.print("\n[bold]Select a topic (enter number):[/bold]")
        choice = click.prompt("Topic number", type=int, default=0)
        if choice < 0 or choice >= len(topics):
            console.print(f"[red]✗[/red] Invalid choice")
            raise SystemExit(1)
        selected = topics[choice]

    console.print(f"\n[green]✓[/green] Selected: [bold]{selected.title}[/bold]\n")

    # ── Step 4: Write Article ──────────────────────────────
    from medium_tool.generator.writer import write_article

    with _spinner("Writing article..."):
        article = write_article(
            topic=selected,
            analysis=analysis,
            language=language,
        )

    console.print(f"[green]✓[/green] Article written ({len(article.markdown.split())} words)")
    console.print(f"  Subtitle: {article.subtitle}")
    console.print(f"  Tags: {', '.join(article.tags)}")
    console.print(f"  Image placeholders: {len(article.image_placeholders)}")

    # ── Step 5: Resolve Images ─────────────────────────────
    has_image_keys = config.has_unsplash or config.has_openai

    if article.image_placeholders and has_image_keys:
        from medium_tool.images.manager import resolve_images

        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Resolving images...", total=len(article.image_placeholders))

            def on_img_progress(idx, total, desc):
                progress.update(task, description=f"Image {idx+1}/{total}: {desc[:50]}...")
                progress.advance(task)

            resolve_images(
                article,
                image_style=img_style,
                unsplash_key=config.unsplash_access_key,
                openai_key=config.openai_api_key,
                on_progress=on_img_progress,
            )

        resolved = sum(1 for img in article.images if img.url)
        console.print(f"[green]✓[/green] Images resolved: {resolved}/{len(article.image_placeholders)}")
    else:
        if not has_image_keys:
            console.print("[yellow]⚠[/yellow] No image API keys configured – skipping images")

    # ── Step 6: Format ─────────────────────────────────────
    from medium_tool.generator.formatter import finalize_article

    article = finalize_article(article)

    # ── Step 7: Output ─────────────────────────────────────
    if output:
        out_path = Path(output)
        out_path.write_text(article.final_markdown, encoding="utf-8")
        console.print(f"\n[green]✓[/green] Article saved to [bold]{out_path}[/bold]")
    else:
        # Show preview
        console.print(Panel(
            Markdown(article.final_markdown[:2000] + ("\n\n..." if len(article.final_markdown) > 2000 else "")),
            title=article.title,
            subtitle="Preview (first 2000 chars)",
        ))

    console.print("\n[green]Done![/green]")


def _spinner(message: str):
    """Simple Rich spinner context manager."""
    return console.status(message, spinner="dots")


def _show_analysis_summary(analysis, verbose: bool):
    """Display project analysis results."""
    console.print()
    table = Table(title=f"Project Analysis: {analysis.name}", show_lines=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Files", str(analysis.total_files))
    table.add_row("Lines", f"{analysis.total_lines:,}")

    if analysis.primary_language:
        table.add_row("Primary Language", analysis.primary_language.value)

    if analysis.languages:
        lang_str = ", ".join(
            f"{l.value} ({c})" for l, c in
            sorted(analysis.languages.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        table.add_row("Languages", lang_str)

    if analysis.project_types:
        table.add_row("Project Types", ", ".join(t.value for t in analysis.project_types))

    if analysis.frameworks:
        table.add_row("Frameworks", ", ".join(analysis.frameworks))

    if analysis.dependencies:
        deps_preview = ", ".join(analysis.dependencies[:10])
        if len(analysis.dependencies) > 10:
            deps_preview += f" (+{len(analysis.dependencies) - 10} more)"
        table.add_row("Dependencies", deps_preview)

    console.print(table)

    if verbose and analysis.readme_content:
        console.print(Panel(
            analysis.readme_content[:500],
            title="README Preview",
        ))


def _show_topics(topics):
    """Display generated topic ideas."""
    console.print()
    for i, topic in enumerate(topics):
        console.print(f"[bold cyan]{i}.[/bold cyan] [bold]{topic.title}[/bold]")
        console.print(f"   [dim]Hook:[/dim] {topic.hook}")
        console.print(f"   [dim]Angle:[/dim] {topic.angle}")
        console.print(f"   [dim]Audience:[/dim] {topic.target_audience}")
        if topic.estimated_sections:
            console.print(f"   [dim]Sections:[/dim] {', '.join(topic.estimated_sections)}")
        console.print()
