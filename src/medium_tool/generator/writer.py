"""Generate full article content using Claude."""

from __future__ import annotations

import re

from medium_tool.generator.formatter import fix_list_spacing
from medium_tool.generator.llm import claude_generate
from medium_tool.models import Article, ImagePlaceholder, ProjectAnalysis, Topic

WRITER_SYSTEM_PROMPT = """You are an expert tech writer crafting a Medium article for the mobile app developer community.
Write in a conversational, story-driven style — like you're telling a friend about a project over coffee.

Guidelines:
- Start with a compelling hook that describes a REAL PROBLEM or frustration — no title (the title is set separately)
- Use ## for section headings (H2), ### for subsections (H3)
- STORY FIRST, CODE SECOND: Lead with the why, the pain points, the journey, the decisions and trade-offs.
  Only include short code snippets (max 10-15 lines) when they illustrate a key decision — not to document the codebase
- Cover BOTH sides: backend AND mobile (iOS/Swift/Android) perspectives. How does the mobile client experience this?
  What SDK integration pain does this solve for the mobile developer?
- Structure the narrative arc: Problem → Why existing solutions failed → Our approach → What went wrong →
  How we fixed it → What we gained → What you can learn from this
- Add [IMAGE: description] placeholders where visuals would help (3-5 per article)
  - Descriptions must be photographic or illustrative scenes that AI image generators can reliably produce
  - DO NOT request diagrams, flowcharts, architecture diagrams, before/after comparisons, or anything with text/labels — AI generators produce garbled text and broken layouts for these
  - GOOD examples: [IMAGE: A frustrated developer staring at a laptop surrounded by coffee cups late at night]
  - GOOD examples: [IMAGE: Two smartphones side by side with colorful app screens glowing]
  - BAD examples (NEVER use): [IMAGE: Architecture diagram showing...], [IMAGE: Flowchart of...], [IMAGE: Before and after comparison...]
- Write 1500-2500 words
- Keep it human: share doubts, mistakes, and "if we did it again" reflections
- End with practical takeaways that readers can apply to their own mobile projects
- Include a subtle call-to-action to check out the project
- DO NOT include the title as an H1 at the top — it's handled separately
- DO NOT include "---" horizontal rules
- AVOID excessive code dumps or API documentation style writing
- IMPORTANT: Start DIRECTLY with the article content. Do NOT include any preamble, acknowledgment, or introductory meta-text like "Here's the article" or "Sure, I'll write...". Begin immediately with the hook paragraph.

Medium-compatible formatting rules (MUST follow):
- NEVER put blank lines between list items (numbered or bulleted). List items must be consecutive with no empty lines between them.
- Keep list items on a single line — do not wrap a single list item across multiple lines
- Use single blank lines between paragraphs, headings, and other block elements
- Inline code with single backticks (`code`) is fine
- Use fenced code blocks (```) for multi-line code — always specify the language
- Do NOT use HTML tags — pure Markdown only
- Bold (**text**) and italic (*text*) are fine, but do not nest them deeply

After the main content, output a line "TAGS:" followed by 3-5 comma-separated Medium tags.
Tag rules:
- Each tag MUST be max 25 characters (Medium's hard limit — longer tags are rejected)
- Pick tags with the largest audience reach on Medium (e.g. "Programming", "iOS", "Software Development", "JavaScript", "Mobile Development")
- Prefer well-known, high-traffic tags over niche or compound ones
- Do NOT use tags like "App-to-App Communication" (too niche) — prefer "iOS Development" or "Mobile"
Then output a line "SUBTITLE:" followed by a one-line subtitle for the article."""

WRITER_USER_TEMPLATE = """Write a Medium article about this topic:

**Title:** {title}
**Hook:** {hook}
**Angle:** {angle}
**Target audience:** {audience}
**Suggested sections:** {sections}
**Language:** {language}

Here is the project analysis to reference:

{summary}"""


def _parse_image_placeholders(markdown: str) -> list[ImagePlaceholder]:
    """Find all [IMAGE: ...] placeholders in the markdown."""
    placeholders: list[ImagePlaceholder] = []
    for match in re.finditer(r'\[IMAGE:\s*(.+?)\]', markdown):
        placeholders.append(ImagePlaceholder(
            marker=match.group(0),
            description=match.group(1).strip(),
            position=match.start(),
        ))
    return placeholders


def write_article(
    topic: Topic,
    analysis: ProjectAnalysis,
    language: str = "en",
) -> Article:
    """Use Claude to write a full article."""
    user_msg = WRITER_USER_TEMPLATE.format(
        title=topic.title,
        hook=topic.hook,
        angle=topic.angle,
        audience=topic.target_audience,
        sections=", ".join(topic.estimated_sections),
        language="Turkish" if language == "tr" else "English",
        summary=analysis.summary,
    )

    raw = claude_generate(WRITER_SYSTEM_PROMPT, user_msg)

    # Parse tags and subtitle from the end
    tags: list[str] = []
    subtitle = ""
    lines = raw.split("\n")
    main_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("TAGS:"):
            tag_str = line.split("TAGS:", 1)[1].strip()
            tags = [t.strip() for t in tag_str.split(",") if t.strip()]
        elif line.strip().startswith("SUBTITLE:"):
            subtitle = line.split("SUBTITLE:", 1)[1].strip()
        else:
            main_lines.append(line)

    markdown = "\n".join(main_lines).strip()

    # Strip preamble lines before the first real content (## heading or [IMAGE:])
    md_lines = markdown.split("\n")
    first_content_idx = 0
    for i, line in enumerate(md_lines):
        stripped = line.strip()
        if stripped.startswith("##") or stripped.startswith("[IMAGE:") or (len(stripped) > 80):
            first_content_idx = i
            break
    # Only strip if the first few lines look like preamble (short, no markdown formatting)
    if first_content_idx > 0:
        preamble = md_lines[:first_content_idx]
        if all(len(l.strip()) < 80 and not l.strip().startswith("#") and not l.strip().startswith("[IMAGE:") for l in preamble if l.strip()):
            markdown = "\n".join(md_lines[first_content_idx:]).strip()

    # Fix list spacing for Medium compatibility
    markdown = fix_list_spacing(markdown)

    placeholders = _parse_image_placeholders(markdown)

    return Article(
        title=topic.title,
        subtitle=subtitle,
        markdown=markdown,
        tags=tags[:5],
        image_placeholders=placeholders,
    )
