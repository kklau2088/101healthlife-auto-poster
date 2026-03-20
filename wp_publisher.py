"""
WordPress Publisher
====================
Publishes a generated article to WordPress via the REST API
using Application Password authentication.

WordPress setup required:
    1. Log in to WP Admin → Users → Profile
    2. Scroll to "Application Passwords"
    3. Enter a name (e.g. "Auto Poster") → Click "Add New Application Password"
    4. Copy the generated password into config.py → WORDPRESS_APP_PASSWORD
"""

import requests
import base64
import json
import logging
from datetime import datetime
from config import (
    WORDPRESS_SITE_URL,
    WORDPRESS_USERNAME,
    WORDPRESS_APP_PASSWORD,
    CATEGORY_IDS,
)

logger = logging.getLogger(__name__)


def _get_auth_header() -> dict:
    """Build Basic Auth header from WordPress credentials."""
    token = base64.b64encode(
        f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()
    ).decode("utf-8")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type":  "application/json",
    }


def _get_or_create_tag(tag_name: str, headers: dict) -> int | None:
    """Return the tag ID for *tag_name*, creating it if it doesn't exist."""
    api_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/tags"

    # Try to find existing tag
    resp = requests.get(api_url, params={"search": tag_name}, headers=headers, timeout=15)
    if resp.ok and resp.json():
        return resp.json()[0]["id"]

    # Create new tag
    resp = requests.post(api_url, json={"name": tag_name}, headers=headers, timeout=15)
    if resp.ok:
        return resp.json().get("id")

    logger.warning("Could not create tag '%s': %s", tag_name, resp.text)
    return None


def publish_article(article: dict) -> dict:
    """
    Post the article to WordPress and return a result dict.

    article keys expected:
        title, content, meta_desc, focus_keyword, category
    """
    headers = _get_auth_header()
    api_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/posts"

    # Resolve category
    category_name = article.get("category", "Health")
    category_id   = CATEGORY_IDS.get(category_name, CATEGORY_IDS["Health"])

    # Build / resolve tags from focus keyword
    tag_ids = []
    for kw in article["focus_keyword"].split():
        if len(kw) > 3:  # skip short stop-words
            tag_id = _get_or_create_tag(kw, headers)
            if tag_id:
                tag_ids.append(tag_id)

    # Rank Math SEO meta fields
    # rank_math_focus_keyword — comma-separated keywords
    # rank_math_description   — meta description
    # rank_math_title         — SEO title (optional)
    seo_meta = {
        "rank_math_focus_keyword": article["focus_keyword"],
        "rank_math_description":   article["meta_desc"],
        "rank_math_title":         f"{article['title']} - 101HealthLife",
    }

    payload = {
        "title":      article["title"],
        "content":    article["content"],
        "status":     "publish",           # Change to "draft" to review before publishing
        "categories": [category_id],
        "tags":       tag_ids,
        "meta":       seo_meta,
        "comment_status": "open",
        "ping_status":    "open",
    }

    logger.info("Publishing: %s  [%s]", article["title"], category_name)

    resp = requests.post(api_url, json=payload, headers=headers, timeout=30)

    if resp.status_code in (200, 201):
        post_data = resp.json()
        result = {
            "success":  True,
            "post_id":  post_data.get("id"),
            "url":      post_data.get("link"),
            "title":    article["title"],
            "category": category_name,
            "published_at": datetime.utcnow().isoformat(),
        }
        logger.info("✅ Published: %s  → %s", article["title"], result["url"])
        return result

    # Handle failure
    logger.error("❌ Failed to publish '%s': %s %s", article["title"], resp.status_code, resp.text)
    return {
        "success":      False,
        "title":        article["title"],
        "error_code":   resp.status_code,
        "error_detail": resp.text,
        "published_at": datetime.utcnow().isoformat(),
    }


def test_connection() -> bool:
    """Quick connectivity test — returns True if credentials are valid."""
    headers = _get_auth_header()
    url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/users/me"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.ok:
        user = resp.json()
        print(f"✅ Connected as: {user.get('name')} ({user.get('slug')})")
        return True
    print(f"❌ Connection failed: {resp.status_code} — {resp.text}")
    return False
