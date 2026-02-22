"""Generate tag suggestions for an article using Claude."""

from __future__ import annotations

import json

from medium_tool.generator.llm import claude_generate

TAGS_SYSTEM_PROMPT = """You are a Medium tag strategist who deeply understands which tags drive the most traffic on Medium.

Given an article's markdown content, suggest 10-15 tags that would maximize the article's visibility on Medium.

Rules:
- Each tag must be max 25 characters
- Use tags that actually exist and are popular on Medium
- Mix high-traffic broad tags with medium-traffic niche tags for best reach
- Consider the article's topic, technology stack, and target audience

Return ONLY a JSON array of objects. No explanation, no markdown fences, just the JSON array.
Each object must have:
- "name": the tag string (max 25 chars)
- "reason": brief explanation why this tag (max 80 chars)
- "traffic": estimated traffic level ("high", "medium", or "low")

Example:
[{"name": "Programming", "reason": "Broad tech tag with massive readership", "traffic": "high"}, {"name": "Python", "reason": "Matches the article's primary language", "traffic": "high"}]"""


def generate_tag_suggestions(markdown: str, language: str = "en") -> list[dict]:
    """Generate 10-15 tag suggestions for the given article content."""
    lang_label = "Turkish" if language == "tr" else "English"
    user_msg = f"Suggest Medium tags in {lang_label} for this article:\n\n{markdown[:3000]}"

    raw = claude_generate(TAGS_SYSTEM_PROMPT, user_msg)

    # Try to parse JSON array from the response
    raw = raw.strip()
    # Handle potential markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        tags = json.loads(raw)
        if isinstance(tags, list):
            return [
                {
                    "name": str(t.get("name", ""))[:25],
                    "reason": str(t.get("reason", "")),
                    "traffic": t.get("traffic", "medium") if t.get("traffic") in ("high", "medium", "low") else "medium",
                }
                for t in tags[:15]
                if isinstance(t, dict) and t.get("name")
            ]
    except json.JSONDecodeError:
        pass

    return []
