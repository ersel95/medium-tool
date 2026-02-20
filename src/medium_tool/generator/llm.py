"""Shared helper to call Claude via the CLI subprocess."""

from __future__ import annotations

import os
import shutil
import subprocess


class ClaudeNotFoundError(RuntimeError):
    """Raised when the Claude Code CLI is not installed or not in PATH."""

    def __init__(self) -> None:
        super().__init__(
            "Claude Code CLI not found. "
            "This tool requires Claude Code to be installed and authenticated.\n\n"
            "Install it with:  npm install -g @anthropic-ai/claude-code\n"
            "Then run:          claude  (to authenticate)\n\n"
            "More info: https://docs.anthropic.com/en/docs/claude-code"
        )


def check_claude_cli() -> bool:
    """Return True if the claude CLI is available in PATH."""
    return shutil.which("claude") is not None


def claude_generate(system_prompt: str, user_message: str) -> str:
    """Call claude CLI in print mode and return the response text."""
    if not check_claude_cli():
        raise ClaudeNotFoundError()

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            ["claude", "-p", "--system-prompt", system_prompt],
            input=user_message,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        raise ClaudeNotFoundError()

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not authenticated" in stderr.lower() or "login" in stderr.lower():
            raise RuntimeError(
                "Claude Code CLI is installed but not authenticated.\n"
                "Run `claude` in your terminal to log in, then try again."
            )
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}):\n{stderr}"
        )

    output = result.stdout.strip()
    if not output:
        raise RuntimeError(
            f"claude CLI returned empty output.\nstderr: {result.stderr.strip()}"
        )

    return output
