"""Manage image selection and placement – alternating Unsplash and DALL-E."""

from __future__ import annotations

from medium_tool.images.dalle import generate_image
from medium_tool.images.unsplash import search_photo
from medium_tool.models import Article, ImageInfo, ImagePlaceholder, ImageStyle


def resolve_images(
    article: Article,
    image_style: ImageStyle = ImageStyle.BOTH,
    unsplash_key: str = "",
    openai_key: str = "",
    on_progress: callable = None,
) -> list[ImageInfo]:
    """Resolve all image placeholders into actual images.

    When style is BOTH, alternates: first Unsplash, then DALL-E, then Unsplash, etc.
    Falls back gracefully if one source fails.
    """
    images: list[ImageInfo] = []

    for i, placeholder in enumerate(article.image_placeholders):
        if on_progress:
            on_progress(i, len(article.image_placeholders), placeholder.description)

        img = _resolve_single(
            placeholder=placeholder,
            index=i,
            style=image_style,
            unsplash_key=unsplash_key,
            openai_key=openai_key,
        )
        if img:
            images.append(img)
        else:
            # Placeholder with no image – will be removed during formatting
            images.append(None)

    # Filter out None but keep index alignment
    article.images = [img if img else ImageInfo(url="", alt_text="", source="none") for img in images]
    return article.images


def _resolve_single(
    placeholder: ImagePlaceholder,
    index: int,
    style: ImageStyle,
    unsplash_key: str,
    openai_key: str,
) -> ImageInfo | None:
    """Resolve a single placeholder to an image."""
    use_unsplash = style in (ImageStyle.UNSPLASH, ImageStyle.BOTH) and unsplash_key
    use_dalle = style in (ImageStyle.DALLE, ImageStyle.BOTH) and openai_key

    if style == ImageStyle.BOTH:
        # Alternate: even index → Unsplash first, odd → DALL-E first
        if index % 2 == 0:
            return _try_unsplash_then_dalle(placeholder.description, unsplash_key, openai_key, use_unsplash, use_dalle)
        else:
            return _try_dalle_then_unsplash(placeholder.description, unsplash_key, openai_key, use_unsplash, use_dalle)
    elif style == ImageStyle.UNSPLASH:
        if use_unsplash:
            return search_photo(placeholder.description, unsplash_key)
        return None
    elif style == ImageStyle.DALLE:
        if use_dalle:
            return generate_image(placeholder.description, openai_key)
        return None

    return None


def _try_unsplash_then_dalle(
    desc: str, unsplash_key: str, openai_key: str,
    use_unsplash: bool, use_dalle: bool,
) -> ImageInfo | None:
    if use_unsplash:
        img = search_photo(desc, unsplash_key)
        if img:
            return img
    if use_dalle:
        return generate_image(desc, openai_key)
    return None


def _try_dalle_then_unsplash(
    desc: str, unsplash_key: str, openai_key: str,
    use_unsplash: bool, use_dalle: bool,
) -> ImageInfo | None:
    if use_dalle:
        img = generate_image(desc, openai_key)
        if img:
            return img
    if use_unsplash:
        return search_photo(desc, unsplash_key)
    return None
