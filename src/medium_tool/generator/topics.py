"""Generate article topic ideas using Claude."""

from __future__ import annotations

import json

from medium_tool.generator.llm import claude_generate
from medium_tool.models import ProjectAnalysis, Topic

TOPIC_SYSTEM_PROMPT = """You are an expert tech writer who creates engaging Medium articles for the mobile app developer community.
Given a project analysis, suggest compelling article topics that tell a STORY — not a technical walkthrough.

Each topic should have:
- A catchy, specific title that would make a mobile developer stop scrolling (not generic, not overly technical)
- A hook: the opening angle that grabs attention — a real problem, frustration, or "aha" moment
- An angle: the narrative arc — why this was built, what problem it solves, what went wrong, what was learned
- A target audience description
- 4-6 estimated section headings

IMPORTANT guidelines for topics:
- Focus on the WHY, not the HOW: Why was this built? What pain point triggered it? What was the breaking point?
- Tell the human story: What problems did the team face? What failed first? What surprising lessons emerged?
- Cover the FULL stack: Include both backend AND mobile/iOS/Android perspectives, not just one side
- Think about what the community gains: What can readers take away and apply to their own projects?
- Avoid dry technical documentation angles — instead frame topics around journeys, decisions, trade-offs, and outcomes
- Frame titles as stories a mobile developer would share with their team

Respond with a JSON array of topic objects. ONLY output valid JSON, no markdown fences."""

TOPIC_USER_TEMPLATE = """Analyze this project and suggest {count} compelling Medium article topics.
Language for the article: {language}

{summary}"""


def generate_topics(
    analysis: ProjectAnalysis,
    count: int = 5,
    language: str = "en",
) -> list[Topic]:
    """Use Claude to generate article topic ideas from project analysis."""
    user_msg = TOPIC_USER_TEMPLATE.format(
        count=count,
        language="Turkish" if language == "tr" else "English",
        summary=analysis.summary,
    )

    raw = claude_generate(TOPIC_SYSTEM_PROMPT, user_msg)
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    # Extract JSON array even if surrounded by other text
    import re
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if json_match:
        raw = json_match.group(0)

    try:
        topics_data = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Failed to parse topics JSON. Raw output:\n{raw[:500]}"
        )

    topics: list[Topic] = []
    for item in topics_data:
        topics.append(Topic(
            title=item.get("title", ""),
            hook=item.get("hook", ""),
            angle=item.get("angle", ""),
            target_audience=item.get("target_audience", ""),
            estimated_sections=item.get("estimated_sections", []),
        ))

    return topics
