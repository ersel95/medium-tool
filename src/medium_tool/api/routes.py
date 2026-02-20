"""API endpoints for medium-tool web UI."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from medium_tool.api.db import (
    delete_article,
    get_article,
    list_articles,
    save_article,
    update_article,
)

router = APIRouter(prefix="/api")

# In-memory session store
_sessions: dict[str, dict[str, Any]] = {}


# ── Request Models ──────────────────────────────────────


class AnalyzeRequest(BaseModel):
    path: str


class TopicsRequest(BaseModel):
    session_id: str
    language: str = "en"
    topic_count: int = 5


class WriteRequest(BaseModel):
    session_id: str
    topic_index: int
    language: str = "en"


class SaveRequest(BaseModel):
    markdown: str
    output_path: str


class TitlesRequest(BaseModel):
    markdown: str
    language: str = "en"


class ReviseRequest(BaseModel):
    markdown: str
    instruction: str
    language: str = "en"


class ArticleUpdateRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    markdown: str | None = None
    tags: list[str] | None = None
    image_prompts: list[dict[str, str]] | None = None


class SocialPostsRequest(BaseModel):
    title: str
    subtitle: str = ""
    markdown: str
    article_url: str
    language: str = "en"


# ── Helpers ─────────────────────────────────────────────


def _analysis_to_dict(analysis) -> dict:
    return {
        "name": analysis.name,
        "total_files": analysis.total_files,
        "total_lines": analysis.total_lines,
        "primary_language": analysis.primary_language.value if analysis.primary_language else None,
        "languages": {
            lang.value: count
            for lang, count in sorted(
                analysis.languages.items(), key=lambda x: x[1], reverse=True
            )
        },
        "project_types": [pt.value for pt in analysis.project_types],
        "frameworks": analysis.frameworks,
        "dependencies": analysis.dependencies[:20],
        "readme_preview": analysis.readme_content[:500] if analysis.readme_content else "",
    }


def _topic_to_dict(topic) -> dict:
    return {
        "title": topic.title,
        "hook": topic.hook,
        "angle": topic.angle,
        "target_audience": topic.target_audience,
        "estimated_sections": topic.estimated_sections,
    }


def _article_to_dict(article) -> dict:
    return {
        "title": article.title,
        "subtitle": article.subtitle,
        "markdown": article.markdown,
        "tags": article.tags,
        "image_prompts": [
            {
                "marker": p.marker,
                "description": p.description,
            }
            for p in article.image_placeholders
        ],
    }


# ── Helpers: Git clone ──────────────────────────────────

def _is_git_url(path: str) -> bool:
    return (
        path.startswith("https://")
        or path.startswith("http://")
        or path.startswith("git@")
    ) and (
        "github.com" in path
        or "gitlab.com" in path
        or "bitbucket.org" in path
        or path.endswith(".git")
    )


def _clone_repo(url: str) -> Path:
    """Shallow-clone a git repo to a temp directory and return the path."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="medium-tool-"))
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(tmp_dir / "repo")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
    return tmp_dir / "repo"


# ── Endpoints ───────────────────────────────────────────


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    """Analyze a project path or git URL. Returns session_id + analysis."""
    from medium_tool.analyzer.summarizer import analyze_project

    cloned_path: Path | None = None

    if _is_git_url(req.path):
        try:
            cloned_path = _clone_repo(req.path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Git clone failed: {e}")
        project_path = cloned_path
    else:
        project_path = Path(req.path)
        if not project_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {req.path}")

    session_id = str(uuid.uuid4())

    try:
        analysis = analyze_project(project_path)
    except Exception as e:
        if cloned_path:
            shutil.rmtree(cloned_path.parent, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Keep cloned path in session for cleanup later; store project name from URL
    if cloned_path:
        _sessions[session_id] = {"analysis": analysis, "_cloned_path": cloned_path}
    else:
        _sessions[session_id] = {"analysis": analysis}

    return {
        "session_id": session_id,
        "analysis": _analysis_to_dict(analysis),
    }


@router.post("/topics")
def topics(req: TopicsRequest):
    """Generate topic ideas (slow, calls Claude). Returns topics list."""
    from medium_tool.generator.topics import generate_topics

    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analysis = session["analysis"]

    try:
        topic_list = generate_topics(
            analysis,
            count=req.topic_count,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic generation failed: {e}")

    session["topics"] = topic_list
    session["language"] = req.language

    return {
        "topics": [_topic_to_dict(t) for t in topic_list],
    }


@router.post("/write")
def write(req: WriteRequest):
    """Write an article for a selected topic (slow, calls Claude)."""
    from medium_tool.generator.writer import write_article

    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    topic_list = session.get("topics")
    if not topic_list:
        raise HTTPException(status_code=400, detail="No topics generated yet")

    if req.topic_index < 0 or req.topic_index >= len(topic_list):
        raise HTTPException(
            status_code=400,
            detail=f"Topic index {req.topic_index} out of range (0-{len(topic_list) - 1})",
        )

    analysis = session["analysis"]
    topic = topic_list[req.topic_index]

    try:
        article = write_article(
            topic=topic,
            analysis=analysis,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Article writing failed: {e}")

    session["article"] = article

    # Auto-save to DB
    article_dict = _article_to_dict(article)
    article_id = save_article(
        title=article.title,
        subtitle=article.subtitle,
        markdown=article.markdown,
        tags=article.tags,
        image_prompts=article_dict["image_prompts"],
        project_name=analysis.name,
    )

    return {"article": article_dict, "article_id": article_id}


@router.post("/save")
def save(req: SaveRequest):
    """Save article markdown to a file."""
    try:
        out_path = Path(req.output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(req.markdown, encoding="utf-8")
        return {"success": True, "path": str(out_path.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Article History Endpoints ──────────────────────────


@router.get("/articles")
def articles_list():
    """List all saved articles."""
    return {"articles": list_articles()}


@router.get("/articles/{article_id}")
def articles_get(article_id: str):
    """Get a single article by ID."""
    article = get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"article": article}


@router.put("/articles/{article_id}")
def articles_update(article_id: str, req: ArticleUpdateRequest):
    """Update an article."""
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    ok = update_article(article_id, **fields)
    if not ok:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True}


@router.delete("/articles/{article_id}")
def articles_delete(article_id: str):
    """Delete an article."""
    ok = delete_article(article_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True}


# ── Title Suggestions ──────────────────────────────────


@router.post("/titles")
def titles(req: TitlesRequest):
    """Generate title suggestions for an article."""
    from medium_tool.generator.titles import generate_titles

    try:
        title_list = generate_titles(req.markdown, language=req.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Title generation failed: {e}")

    return {"titles": title_list}


# ── Article Revision ───────────────────────────────────


@router.post("/revise")
def revise(req: ReviseRequest):
    """Revise an article based on an instruction."""
    from medium_tool.generator.reviser import revise_article

    try:
        revised = revise_article(
            markdown=req.markdown,
            instruction=req.instruction,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revision failed: {e}")

    return {"markdown": revised}


# ── Social Media Posts ─────────────────────────────────


@router.post("/social-posts")
def social_posts(req: SocialPostsRequest):
    """Generate social media sharing posts for a published article."""
    from medium_tool.generator.social import generate_social_posts

    try:
        posts = generate_social_posts(
            title=req.title,
            subtitle=req.subtitle,
            markdown=req.markdown,
            article_url=req.article_url,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Social post generation failed: {e}")

    return {"posts": posts}
