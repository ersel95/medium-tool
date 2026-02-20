"""Upload DALL-E generated images to Medium and update URLs."""

from __future__ import annotations

import os

from medium_tool.models import Article
from medium_tool.publisher.medium_client import MediumClient


def upload_dalle_images(article: Article, client: MediumClient) -> Article:
    """Upload locally-stored DALL-E images to Medium, replacing local URLs with Medium URLs."""
    for img in article.images:
        if img.source == "dalle" and img.local_path:
            try:
                medium_url = client.upload_image(img.local_path)
                img.url = medium_url
                # Clean up temp file
                try:
                    os.unlink(img.local_path)
                except OSError:
                    pass
                img.local_path = None
            except Exception:
                # If upload fails, remove the image so it won't break the article
                img.url = ""

    return article
