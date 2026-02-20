"""Unsplash API client for stock photo search."""

from __future__ import annotations

import requests

from medium_tool.models import ImageInfo

UNSPLASH_API_URL = "https://api.unsplash.com"


def search_photo(query: str, access_key: str) -> ImageInfo | None:
    """Search Unsplash for a photo matching the query. Returns the top result."""
    try:
        resp = requests.get(
            f"{UNSPLASH_API_URL}/search/photos",
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return None

        photo = results[0]
        url = photo["urls"]["regular"]  # 1080px wide
        alt = photo.get("alt_description", query)
        user_name = photo["user"]["name"]
        user_link = photo["user"]["links"]["html"]

        # Unsplash requires attribution
        attribution = f"Photo by [{user_name}]({user_link}) on [Unsplash](https://unsplash.com)"

        # Trigger download tracking per Unsplash API guidelines
        download_url = photo.get("links", {}).get("download_location")
        if download_url:
            try:
                requests.get(
                    download_url,
                    headers={"Authorization": f"Client-ID {access_key}"},
                    timeout=5,
                )
            except Exception:
                pass

        return ImageInfo(
            url=url,
            alt_text=alt or query,
            source="unsplash",
            attribution=attribution,
        )

    except Exception:
        return None
