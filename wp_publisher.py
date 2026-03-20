"""
WordPress Publisher with Pexels Image Support
===============================================
Publishes a generated article to WordPress via the REST API.
- Searches Pexels for a relevant high-quality photo
- Uploads image to WordPress Media Library
- Sets it as the Featured Image (thumbnail)
- Inserts one inline image near the top of the article content

WordPress setup required:
    1. Log in to WP Admin -> Users -> Profile
    2. Scroll to "Application Passwords"
    3. Enter a name (e.g. "Auto Poster") -> Click "Add New Application Password"
    4. Copy the generated password into config.py -> WORDPRESS_APP_PASSWORD

Pexels API setup:
    1. Sign up at https://www.pexels.com/api/
    2. Copy your API key into config.py -> PEXELS_API_KEY
"""

import requests
import base64
import logging
import mimetypes
import os
import tempfile
from datetime import datetime
from config import (
    WORDPRESS_SITE_URL,
    WORDPRESS_USERNAME,
    WORDPRESS_APP_PASSWORD,
    CATEGORY_IDS,
    PEXELS_API_KEY,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Auth helpers
# ─────────────────────────────────────────────
def _get_auth_header() -> dict:
    """Build Basic Auth header from WordPress credentials."""
    token = base64.b64encode(
        f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()
    ).decode("utf-8")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type":  "application/json",
    }


# ─────────────────────────────────────────────
#  Pexels image fetch
# ─────────────────────────────────────────────
def _fetch_pexels_image(keyword: str) -> dict | None:
    """
    Search Pexels for a landscape photo matching *keyword*.
    Returns a dict with keys: url, filename, photographer, photo_url
    or None if the search fails.
    """
    if not PEXELS_API_KEY or PEXELS_API_KEY == "your-pexels-api-key-here":
        logger.warning("Pexels API key not configured — skipping image.")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    params  = {
        "query":       keyword,
        "orientation": "landscape",
        "size":        "large",
        "per_page":    5,
    }

    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        if not resp.ok:
            logger.warning("Pexels search failed (%s): %s", resp.status_code, resp.text[:200])
            return None

        photos = resp.json().get("photos", [])
        if not photos:
            # Fallback: try a more generic health keyword
            params["query"] = "healthy lifestyle"
            resp = requests.get("https://api.pexels.com/v1/search",
                                headers=headers, params=params, timeout=15)
            photos = resp.json().get("photos", []) if resp.ok else []

        if not photos:
            logger.warning("No Pexels photos found for '%s'", keyword)
            return None

        photo = photos[0]
        image_url = photo["src"]["large2x"]   # 2560px wide
        filename  = f"{keyword.replace(' ', '-').lower()}-{photo['id']}.jpg"

        return {
            "url":          image_url,
            "filename":     filename,
            "photographer": photo.get("photographer", "Pexels"),
            "photo_url":    photo.get("url", "https://www.pexels.com"),
        }

    except Exception as exc:
        logger.warning("Pexels fetch error: %s", exc)
        return None


# ─────────────────────────────────────────────
#  WordPress media upload
# ─────────────────────────────────────────────
def _upload_image_to_wordpress(image_info: dict, auth_header: dict) -> int | None:
    """
    Download the image from Pexels and upload it to WordPress media library.
    Returns the WordPress media attachment ID, or None on failure.
    """
    try:
        # Download image to a temp file
        img_resp = requests.get(image_info["url"], timeout=30)
        if not img_resp.ok:
            logger.warning("Failed to download image from Pexels")
            return None

        suffix = ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(img_resp.content)
            tmp_path = tmp.name

        # Upload to WordPress
        upload_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/media"
        upload_headers = {
            "Authorization":       auth_header["Authorization"],
            "Content-Disposition": f'attachment; filename="{image_info["filename"]}"',
        }

        with open(tmp_path, "rb") as img_file:
            upload_resp = requests.post(
                upload_url,
                headers=upload_headers,
                files={"file": (image_info["filename"], img_file, "image/jpeg")},
                timeout=60,
            )

        os.unlink(tmp_path)  # Clean up temp file

        if upload_resp.ok:
            media_id = upload_resp.json().get("id")
            media_url = upload_resp.json().get("source_url", "")

            # Add photographer credit to alt text and caption
            caption = (f'Photo by <a href="{image_info["photo_url"]}" '
                       f'target="_blank">{image_info["photographer"]}</a> on '
                       f'<a href="https://www.pexels.com" target="_blank">Pexels</a>')

            # Update media metadata
            requests.post(
                f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/media/{media_id}",
                headers=auth_header,
                json={
                    "alt_text": image_info["filename"].replace("-", " ").replace(".jpg", ""),
                    "caption":  caption,
                },
                timeout=15,
            )

            logger.info("Image uploaded to WP media library (ID: %d)", media_id)
            return media_id, media_url

        logger.warning("WP media upload failed: %s %s",
                       upload_resp.status_code, upload_resp.text[:200])
        return None, None

    except Exception as exc:
        logger.warning("Image upload error: %s", exc)
        return None, None


# ─────────────────────────────────────────────
#  Insert image into article content
# ─────────────────────────────────────────────
def _insert_image_into_content(content: str, media_url: str,
                                alt_text: str, caption: str) -> str:
    """
    Insert a featured image block after the first </p> tag in the article.
    """
    if not media_url:
        return content

    img_html = (
        f'\n<figure class="wp-block-image size-large">'
        f'<img src="{media_url}" alt="{alt_text}" class="wp-image" />'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>\n'
    )

    # Insert after the first closing </p> (end of intro paragraph)
    insert_pos = content.find("</p>")
    if insert_pos != -1:
        return content[:insert_pos + 4] + img_html + content[insert_pos + 4:]

    # Fallback: prepend to content
    return img_html + content


# ─────────────────────────────────────────────
#  Tag helpers
# ─────────────────────────────────────────────
def _get_or_create_tag(tag_name: str, headers: dict) -> int | None:
    """Return the tag ID for *tag_name*, creating it if it doesn't exist."""
    api_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/tags"

    resp = requests.get(api_url, params={"search": tag_name}, headers=headers, timeout=15)
    if resp.ok and resp.json():
        return resp.json()[0]["id"]

    resp = requests.post(api_url, json={"name": tag_name}, headers=headers, timeout=15)
    if resp.ok:
        return resp.json().get("id")

    logger.warning("Could not create tag '%s': %s", tag_name, resp.text)
    return None


# ─────────────────────────────────────────────
#  Main publish function
# ─────────────────────────────────────────────
def publish_article(article: dict) -> dict:
    """
    Post the article to WordPress and return a result dict.

    article keys expected:
        title, content, meta_desc, focus_keyword, category
    """
    auth_header = _get_auth_header()
    api_url     = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/posts"

    # Resolve category
    category_name = article.get("category", "Health")
    category_id   = CATEGORY_IDS.get(category_name, CATEGORY_IDS["Health"])

    # Build / resolve tags from focus keyword
    tag_ids = []
    for kw in article["focus_keyword"].split():
        if len(kw) > 3:
            tag_id = _get_or_create_tag(kw, auth_header)
            if tag_id:
                tag_ids.append(tag_id)

    # ── Pexels image ──────────────────────────
    content    = article["content"]
    media_id   = None

    logger.info("Searching Pexels for: %s", article["focus_keyword"])
    image_info = _fetch_pexels_image(article["focus_keyword"])

    if image_info:
        media_id, media_url = _upload_image_to_wordpress(image_info, auth_header)
        if media_id and media_url:
            # Insert inline image into article body
            caption = (f'Photo by <a href="{image_info["photo_url"]}" '
                       f'target="_blank">{image_info["photographer"]}</a> on Pexels')
            alt_text = article["focus_keyword"]
            content = _insert_image_into_content(content, media_url, alt_text, caption)
            logger.info("Image inserted into article content")
        else:
            media_id = None
    # ──────────────────────────────────────────

    # Rank Math SEO meta
    seo_meta = {
        "rank_math_focus_keyword": article["focus_keyword"],
        "rank_math_description":   article["meta_desc"],
        "rank_math_title":         f"{article['title']} - 101HealthLife",
    }

    payload = {
        "title":            article["title"],
        "content":          content,
        "status":           "publish",
        "categories":       [category_id],
        "tags":             tag_ids,
        "meta":             seo_meta,
        "comment_status":   "open",
        "ping_status":      "open",
    }

    # Set featured image if upload succeeded
    if media_id:
        payload["featured_media"] = media_id

    logger.info("Publishing: %s  [%s]", article["title"], category_name)
    resp = requests.post(api_url, json=payload, headers=auth_header, timeout=30)

    if resp.status_code in (200, 201):
        post_data = resp.json()
        result = {
            "success":      True,
            "post_id":      post_data.get("id"),
            "url":          post_data.get("link"),
            "title":        article["title"],
            "category":     category_name,
            "has_image":    media_id is not None,
            "published_at": datetime.utcnow().isoformat(),
        }
        logger.info("Published: %s -> %s (image: %s)",
                    article["title"], result["url"],
                    "yes" if media_id else "no")
        return result

    logger.error("Failed to publish '%s': %s %s",
                 article["title"], resp.status_code, resp.text)
    return {
        "success":      False,
        "title":        article["title"],
        "error_code":   resp.status_code,
        "error_detail": resp.text,
        "published_at": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────
#  Connection test
# ─────────────────────────────────────────────
def test_connection() -> bool:
    """Quick connectivity test — returns True if credentials are valid."""
    auth_header = _get_auth_header()
    url  = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/users/me"
    resp = requests.get(url, headers=auth_header, timeout=15)
    if resp.ok:
        user = resp.json()
        print(f"WordPress: Connected as {user.get('name')} ({user.get('slug')})")

        # Also test Pexels
        if PEXELS_API_KEY and PEXELS_API_KEY != "your-pexels-api-key-here":
            p = requests.get("https://api.pexels.com/v1/search",
                             headers={"Authorization": PEXELS_API_KEY},
                             params={"query": "health", "per_page": 1}, timeout=10)
            if p.ok:
                print("Pexels API: Connected OK")
            else:
                print(f"Pexels API: Error {p.status_code}")
        else:
            print("Pexels API: Key not configured")
        return True

    print(f"WordPress: Connection failed {resp.status_code}")
    return False
