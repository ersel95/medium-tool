"""Medium API client for authentication, posting, and image upload."""

from __future__ import annotations

from pathlib import Path

import requests

from medium_tool.models import PublishResult

MEDIUM_API_URL = "https://api.medium.com/v1"


class MediumClient:
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })
        self._user_id: str | None = None

    @property
    def user_id(self) -> str:
        if not self._user_id:
            self._user_id = self.get_user_id()
        return self._user_id

    def get_user_id(self) -> str:
        """GET /me to retrieve the authenticated user's ID."""
        resp = self.session.get(f"{MEDIUM_API_URL}/me", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["id"]

    def upload_image(self, file_path: str, content_type: str = "image/png") -> str:
        """Upload an image to Medium and return its URL.

        POST /images with multipart form data.
        """
        path = Path(file_path)
        with open(path, "rb") as f:
            resp = self.session.post(
                f"{MEDIUM_API_URL}/images",
                files={"image": (path.name, f, content_type)},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["url"]

    def create_post(
        self,
        title: str,
        content_markdown: str,
        tags: list[str] | None = None,
        publish_status: str = "draft",
    ) -> PublishResult:
        """Create a post on Medium.

        POST /users/{userId}/posts
        """
        payload = {
            "title": title,
            "contentFormat": "markdown",
            "content": content_markdown,
            "publishStatus": publish_status,
        }
        if tags:
            payload["tags"] = tags[:5]  # Medium allows max 5 tags

        try:
            resp = self.session.post(
                f"{MEDIUM_API_URL}/users/{self.user_id}/posts",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return PublishResult(
                success=True,
                url=data.get("url", ""),
                post_id=data.get("id", ""),
            )
        except requests.HTTPError as e:
            return PublishResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            return PublishResult(success=False, error=str(e))
