"""Format article markdown for Medium publishing."""

from __future__ import annotations

import re

from medium_tool.models import Article, ImageInfo


def replace_image_placeholders(article: Article) -> str:
    """Replace [IMAGE: ...] placeholders with actual image markdown."""
    markdown = article.markdown

    for i, placeholder in enumerate(article.image_placeholders):
        if i < len(article.images):
            img = article.images[i]
            img_md = _format_image_markdown(img)
            markdown = markdown.replace(placeholder.marker, img_md, 1)
        else:
            # No image available – remove placeholder
            markdown = markdown.replace(placeholder.marker, "", 1)

    return markdown


def _format_image_markdown(img: ImageInfo) -> str:
    """Format a single image as markdown."""
    md = f"![{img.alt_text}]({img.url})"
    if img.attribution:
        md += f"\n*{img.attribution}*"
    return md


def finalize_article(article: Article) -> Article:
    """Produce final_markdown with images resolved and cleanup applied."""
    markdown = replace_image_placeholders(article)
    markdown = _clean_markdown(markdown)
    article.final_markdown = markdown
    return article


def _clean_markdown(markdown: str) -> str:
    """Cleanup for Medium compatibility."""
    # Remove excessive blank lines (more than 2 consecutive)
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
    # Ensure code blocks have language hints
    markdown = re.sub(r'```\s*\n', '```\n', markdown)
    # Remove blank lines between list items (Medium renders them as empty items)
    markdown = fix_list_spacing(markdown)
    return markdown.strip()


def fix_list_spacing(markdown: str) -> str:
    """Remove blank lines between consecutive list items for Medium compatibility.

    Medium interprets blank lines between numbered/bulleted list items as
    separate empty list entries (showing 2., 4., 6., etc.).
    """
    lines = markdown.split("\n")
    result: list[str] = []
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # Track code blocks — don't modify inside them
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            i += 1
            continue

        if in_code_block:
            result.append(line)
            i += 1
            continue

        # Detect if current line is a list item
        is_list = bool(re.match(r'^(\s*[-*+]|\s*\d+[.)]\s)', line))

        if is_list:
            result.append(line)
            # Skip blank lines that sit between this list item and the next
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            # If the next non-blank line is also a list item, skip the blanks
            if j < len(lines) and re.match(r'^(\s*[-*+]|\s*\d+[.)]\s)', lines[j]):
                i = j  # jump over blank lines
            else:
                i += 1
        else:
            result.append(line)
            i += 1

    return "\n".join(result)
