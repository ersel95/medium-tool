"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medium_tool.api.db import init_db
from medium_tool.api.routes import router
from medium_tool.generator.llm import check_claude_cli

logger = logging.getLogger("medium_tool")

app = FastAPI(
    title="Medium Tool API",
    description="Web API for analyzing projects and generating Medium articles",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
    if not check_claude_cli():
        logger.warning(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  WARNING: Claude Code CLI not found!                       ║\n"
            "║                                                            ║\n"
            "║  Article generation, topic suggestions, title suggestions  ║\n"
            "║  and revision features will NOT work.                      ║\n"
            "║                                                            ║\n"
            "║  Install:  npm install -g @anthropic-ai/claude-code        ║\n"
            "║  Then run: claude  (to authenticate)                       ║\n"
            "║                                                            ║\n"
            "║  Docs: https://docs.anthropic.com/en/docs/claude-code      ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )


@app.get("/health")
def health():
    claude_ok = check_claude_cli()
    return {
        "status": "ok",
        "claude_cli": claude_ok,
        **(
            {}
            if claude_ok
            else {
                "warning": "Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code"
            }
        ),
    }
