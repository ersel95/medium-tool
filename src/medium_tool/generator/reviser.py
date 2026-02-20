"""Revise an article based on user instructions using Claude."""

from __future__ import annotations

from medium_tool.generator.llm import claude_generate

REVISER_SYSTEM_PROMPT = """You are an expert tech article editor.
The user will provide an existing Medium article in Markdown and a revision instruction.
Apply the requested changes and return the FULL revised article in Markdown.

Rules:
- Return ONLY the revised markdown content — no preamble, no explanation, no code fences
- Preserve the overall structure (## headings, [IMAGE: ...] placeholders) unless asked to change them
- Keep TAGS: and SUBTITLE: lines out — they are managed separately
- Start directly with the article content"""


def revise_article(markdown: str, instruction: str, language: str = "en") -> str:
    """Revise an article according to the given instruction."""
    lang_label = "Turkish" if language == "tr" else "English"
    user_msg = f"""Language: {lang_label}

## Current Article

{markdown}

## Revision Instruction

{instruction}

Please return the full revised article in Markdown."""

    return claude_generate(REVISER_SYSTEM_PROMPT, user_msg)
