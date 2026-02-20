"""OpenAI DALL-E image generation client."""

from __future__ import annotations

import tempfile
from pathlib import Path

import requests
from openai import OpenAI

from medium_tool.models import ImageInfo

STYLE_PREFIX = (
    "Create a clean, modern technical illustration suitable for a Medium blog post. "
    "Minimalist style, professional color palette, no text overlays. "
)


def generate_image(description: str, api_key: str) -> ImageInfo | None:
    """Generate an image with DALL-E (gpt-image-1) and download to a temp file."""
    try:
        client = OpenAI(api_key=api_key)

        prompt = STYLE_PREFIX + description

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1536x1024",
            quality="medium",
        )

        image_url = result.data[0].url
        if not image_url:
            # gpt-image-1 may return b64_json instead of url
            import base64
            b64 = result.data[0].b64_json
            if b64:
                img_bytes = base64.b64decode(b64)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(img_bytes)
                tmp.close()
                return ImageInfo(
                    url="",
                    alt_text=description,
                    source="dalle",
                    local_path=tmp.name,
                )
            return None

        # Download image to temp file
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(resp.content)
        tmp.close()

        return ImageInfo(
            url=image_url,
            alt_text=description,
            source="dalle",
            local_path=tmp.name,
        )

    except Exception:
        return None
