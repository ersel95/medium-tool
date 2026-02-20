"""Shared helper to call Claude via the CLI subprocess."""

from __future__ import annotations

import os
import subprocess


def claude_generate(system_prompt: str, user_message: str) -> str:
    """Call claude CLI in print mode and return the response text."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    result = subprocess.run(
        ["claude", "-p", "--system-prompt", system_prompt],
        input=user_message,
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )

    output = result.stdout.strip()
    if not output:
        raise RuntimeError(
            f"claude CLI returned empty output.\nstderr: {result.stderr.strip()}"
        )

    return output
