"""Generate social media sharing posts for a published article."""

from __future__ import annotations

import json

from medium_tool.generator.llm import claude_generate

SOCIAL_SYSTEM_PROMPT = """You are a social media copywriting expert. Given an article's title, subtitle, and content summary, generate sharing posts for different platforms and tones.

Return a JSON object with this exact structure:
{
  "twitter": [
    {"tone": "professional", "text": "..."},
    {"tone": "casual", "text": "..."},
    {"tone": "provocative", "text": "..."}
  ],
  "linkedin": [
    {"tone": "professional", "text": "..."},
    {"tone": "storytelling", "text": "..."}
  ],
  "hackernews": [
    {"tone": "technical", "text": "..."}
  ]
}

Rules:
- Twitter/X posts: max 280 characters including the URL placeholder {url}
- LinkedIn posts: 1-3 short paragraphs, can be longer
- Hacker News: just a concise title/description, technical audience
- Include {url} placeholder where the article link should go
- Match the article's language (if article is Turkish, write Turkish posts; if English, write English posts)
- Do NOT use hashtags on LinkedIn or HN
- Twitter: use 2-3 relevant hashtags max
- Return ONLY the JSON object, no markdown fences, no explanation"""


def generate_social_posts(
    title: str,
    subtitle: str,
    markdown: str,
    article_url: str,
    language: str = "en",
) -> dict:
    """Generate social media posts for different platforms and tones."""
    lang_label = "Turkish" if language == "tr" else "English"
    # Send first 1500 chars of article for context
    user_msg = f"""Generate social media sharing posts in {lang_label} for this article.

Title: {title}
Subtitle: {subtitle}
Article URL: {article_url}

Article excerpt:
{markdown[:1500]}"""

    raw = claude_generate(SOCIAL_SYSTEM_PROMPT, user_msg)

    # Parse JSON
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        posts = json.loads(raw)
        # Replace {url} placeholder with actual URL
        _replace_url(posts, article_url)
        return posts
    except json.JSONDecodeError:
        return {
            "twitter": [{"tone": "default", "text": f"{title} {article_url}"}],
            "linkedin": [{"tone": "default", "text": f"{title}\n\n{subtitle}\n\n{article_url}"}],
        }


def _replace_url(obj: dict | list | str, url: str) -> None:
    """Recursively replace {url} in all string values."""
    if isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], str):
                obj[key] = obj[key].replace("{url}", url)
            else:
                _replace_url(obj[key], url)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                obj[i] = item.replace("{url}", url)
            else:
                _replace_url(item, url)
