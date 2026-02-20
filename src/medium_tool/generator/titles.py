"""Generate title suggestions for an article using Claude."""

from __future__ import annotations

import json

from medium_tool.generator.llm import claude_generate

TITLES_SYSTEM_PROMPT = """You are an expert copywriter specializing in Medium article headlines.
Given an article's markdown content, generate exactly 5 compelling title alternatives.
Return ONLY a JSON array of 5 strings. No explanation, no markdown fences, just the JSON array.
Example: ["Title One", "Title Two", "Title Three", "Title Four", "Title Five"]"""


def generate_titles(markdown: str, language: str = "en") -> list[str]:
    """Generate 5 title suggestions for the given article content."""
    lang_label = "Turkish" if language == "tr" else "English"
    user_msg = f"Generate 5 title suggestions in {lang_label} for this article:\n\n{markdown[:3000]}"

    raw = claude_generate(TITLES_SYSTEM_PROMPT, user_msg)

    # Try to parse JSON array from the response
    raw = raw.strip()
    # Handle potential markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        titles = json.loads(raw)
        if isinstance(titles, list):
            return [str(t) for t in titles[:5]]
    except json.JSONDecodeError:
        pass

    # Fallback: split by newlines if JSON fails
    lines = [l.strip().strip('"').strip("'").lstrip("0123456789.-) ") for l in raw.split("\n") if l.strip()]
    return lines[:5]
