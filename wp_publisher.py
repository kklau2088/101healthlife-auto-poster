"""
WordPress Publisher with Pexels Image Support
===============================================

Publishes a generated article to WordPress via the REST API.
- Validates all external links before publishing (replaces broken ones)
- Searches Pexels for a relevant high-quality photo
- Uploads image to WordPress Media Library
- Sets it as the Featured Image (thumbnail)
- Inserts one inline image near the top of the article content
- Cross-checks Pexels images against history.json to prevent reuse

WordPress setup required:
1. Log in to WP Admin -> Users -> Profile
2. Scroll to "Application Passwords"
3. Enter a name (e.g. "Auto Poster") -> Click "Add New Application Password"
4. Copy the generated password into config.py -> WORDPRESS_APP_PASSWORD

Pexels API setup:
1. Sign up at https://www.pexels.com/api/
2. Copy your API key into config.py -> PEXELS_API_KEY
"""

import re
import random
import hashlib
import json
import os
import requests
import base64
import logging
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

# ───────────────────────────────────────────
# Used-photo tracking (persists across runs)
# Prevents the same Pexels photo from being
# reused across different articles.
# ───────────────────────────────────────────

_USED_PHOTOS_FILE = os.path.join(os.path.dirname(__file__), "used_photos.json")


def _load_used_photo_ids() -> set:
    """Load the set of previously used Pexels photo IDs from disk."""
    if os.path.exists(_USED_PHOTOS_FILE):
        try:
            with open(_USED_PHOTOS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_used_photo_ids(used: set) -> None:
    """Persist the set of used Pexels photo IDs to disk."""
    try:
        with open(_USED_PHOTOS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(used), f)
    except Exception as exc:
        logger.warning("Could not save used_photos.json: %s", exc)


def load_all_used_pexels_ids(published_articles: list[dict]) -> set:
    """Build a complete set of used Pexels IDs from BOTH sources:

    1. used_photos.json (primary tracking file)
    2. history["published"] records (pexels_ids field)

    This ensures that even if used_photos.json is deleted or incomplete,
    we still won't reuse photos from previously published articles.
    """
    used_ids = _load_used_photo_ids()

    # Merge IDs from history.json published records
    for rec in published_articles:
        for pid in rec.get("pexels_ids", []):
            try:
                used_ids.add(int(pid))
            except (ValueError, TypeError):
                pass

    return used_ids


# ───────────────────────────────────────────
# Fallback links by domain (used when a link
# is unreachable — swap to the site homepage)
# ───────────────────────────────────────────

DOMAIN_FALLBACKS = {
    "healthline.com": "https://www.healthline.com/nutrition",
    "mayoclinic.org": "https://www.mayoclinic.org/healthy-lifestyle",
    "nutrition.gov": "https://www.nutrition.gov",
    "hsph.harvard.edu": "https://www.hsph.harvard.edu/nutritionsource",
    "niddk.nih.gov": "https://www.niddk.nih.gov/health-information",
    "cdc.gov": "https://www.cdc.gov/healthyliving",
    "ods.od.nih.gov": "https://ods.od.nih.gov/factsheets/list-all",
    "who.int": "https://www.who.int/health-topics",
    "nhs.uk": "https://www.nhs.uk/live-well",
    "medlineplus.gov": "https://medlineplus.gov",
    "nimh.nih.gov": "https://www.nimh.nih.gov/health",
    "mind.org.uk": "https://www.mind.org.uk/information-support",
    "mentalhealth.gov": "https://www.mentalhealth.gov",
    "psychologytoday.com": "https://www.psychologytoday.com/us/basics",
    "healthcare.gov": "https://www.healthcare.gov",
    "cms.gov": "https://www.cms.gov",
    "kff.org": "https://www.kff.org/health-topics",
    "nerdwallet.com": "https://www.nerdwallet.com/health-insurance",
    "smokefree.gov": "https://smokefree.gov",
    "ncbi.nlm.nih.gov": "https://www.ncbi.nlm.nih.gov",
    "healthit.gov": "https://www.healthit.gov",
    "nature.com": "https://www.nature.com/subjects/health-sciences",
    "nia.nih.gov": "https://www.nia.nih.gov/health",
    "caregiver.org": "https://www.caregiver.org/resource/caregiver-help-start",
    "womenshealth.gov": "https://www.womenshealth.gov",
    "acog.org": "https://www.acog.org",
}

# ───────────────────────────────────────────
# External link validator
# ───────────────────────────────────────────

def _check_url(url: str, timeout: int = 8) -> bool:
    """
    Return True if *url* responds with a 2xx or 3xx status code.
    Uses HEAD first (faster), falls back to GET if HEAD is rejected.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    try:
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True
        # Some servers reject HEAD — retry with GET
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        return resp.status_code < 400
    except Exception:
        return False

def _get_fallback_for_url(url: str) -> str:
    """
    Given a broken URL, return the best fallback URL for that domain.
    If no specific fallback is known, return the domain root.
    """
    for domain, fallback in DOMAIN_FALLBACKS.items():
        if domain in url:
            return fallback
    # Generic fallback: strip path and return root domain
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def validate_and_fix_links(content: str) -> str:
    """
    Scan all external links in *content*.
    For each link:
    - If reachable → keep as-is
    - If unreachable → replace href with the domain fallback URL
    Returns the updated content string.
    """
    # Match all external href values (http/https)
    pattern = re.compile(r'href="(https?://[^"]+)"', re.IGNORECASE)
    urls = pattern.findall(content)

    # De-duplicate while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    if not unique_urls:
        logger.info("No external links found in article — skipping link check.")
        return content

    logger.info("Checking %d external link(s) before publishing...", len(unique_urls))
    replacements = 0
    for url in unique_urls:
        ok = _check_url(url)
        if ok:
            logger.info(" [OK] %s", url)
        else:
            fallback = _get_fallback_for_url(url)
            logger.warning(" [BROKEN] %s -> replacing with %s", url, fallback)
            # Replace all occurrences of this exact href in the content
            content = content.replace(f'href="{url}"', f'href="{fallback}"')
            replacements += 1

    logger.info("Link check complete — %d broken link(s) replaced.", replacements)
    return content

# ───────────────────────────────────────────
# Check 1: Paragraph length (Rank Math 14.2)
# Rank Math fails if any <p> exceeds 120 words
# ───────────────────────────────────────────

def fix_long_paragraphs(content: str, max_words: int = 120) -> str:
    """
    Find any <p>...</p> blocks exceeding max_words and split them
    at a sentence boundary into two shorter paragraphs.
    Returns the updated content string.
    """
    pattern = re.compile(r'<p>(.*?)</p>', re.DOTALL | re.IGNORECASE)
    fixes = 0

    def split_paragraph(match):
        nonlocal fixes
        inner = match.group(1)
        # Count words (strip inner tags for counting only)
        plain = re.sub(r'<[^>]+>', '', inner)
        words = plain.split()

        if len(words) <= max_words:
            return match.group(0)  # fine — leave unchanged

        # Split at sentence boundary closest to the midpoint
        sentences = re.split(r'(?<=[.!?])\s+', inner.strip())

        if len(sentences) < 2:
            # No sentence boundary found — hard split at word limit
            word_list = inner.split()
            mid = len(word_list) // 2
            part1 = " ".join(word_list[:mid])
            part2 = " ".join(word_list[mid:])
            fixes += 1
            return f"<p>{part1}</p>\n<p>{part2}</p>"

        # Group sentences into two balanced halves
        half = len(words) // 2
        count = 0
        split_at = len(sentences) // 2  # default: split in half
        for i, sent in enumerate(sentences):
            count += len(re.sub(r'<[^>]+>', '', sent).split())
            if count >= half:
                split_at = i + 1
                break

        part1 = " ".join(sentences[:split_at])
        part2 = " ".join(sentences[split_at:])

        if not part2.strip():
            return match.group(0)

        fixes += 1
        return f"<p>{part1}</p>\n<p>{part2}</p>"

    new_content = pattern.sub(split_paragraph, content)

    if fixes:
        logger.info("Paragraph check: split %d long paragraph(s) (max %d words each).", fixes, max_words)
    else:
        logger.info("Paragraph check: all paragraphs OK (max %d words).", max_words)

    return new_content

# ───────────────────────────────────────────
# Check 2: Image count (Rank Math 14.3)
# Rank Math requires at least 4 images for
# a 100% score on the media test
# ───────────────────────────────────────────

def _count_images_in_content(content: str) -> int:
    """Count <img> tags in the article content."""
    return len(re.findall(r'<img', content, re.IGNORECASE))


# ───────────────────────────────────────────
# Pexels image fetch  ← FIXED: no more
# repeated photos across articles
# ───────────────────────────────────────────

def _fetch_pexels_image(
    keyword: str,
    used_ids: set | None = None,
    slot_index: int = 0,
) -> dict | None:
    """
    Search Pexels for a landscape photo matching *keyword*.

    Changes vs. original:
    - Fetches up to 15 results (was 5) for a larger candidate pool.
    - Tries multiple pages when the first page is exhausted.
    - Skips any photo whose ID is already in *used_ids* so that
      different articles (and different image slots within the same
      article) never reuse the same photo.
    - *slot_index* shifts which page we start from so that image
      slot 0, 1, 2, 3 inside one article all come from different
      pages, further reducing collisions.

    Returns a dict with keys: url, filename, photographer, photo_url, id
    or None if no unused photo is found.
    """
    if not PEXELS_API_KEY or PEXELS_API_KEY == "YOUR-PEXELS-API-KEY-HERE":
        logger.warning("Pexels API key not configured — skipping image.")
        return None

    if used_ids is None:
        used_ids = set()

    headers = {"Authorization": PEXELS_API_KEY}

    # Try up to 5 pages before giving up
    for attempt in range(5):
        page = (slot_index + attempt) % 10 + 1   # pages 1-10, spread by slot
        params = {
            "query": keyword,
            "orientation": "landscape",
            "size": "large",
            "per_page": 15,   # wider pool than the original 5
            "page": page,
        }

        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params=params,
                timeout=15,
            )

            if not resp.ok:
                logger.warning(
                    "Pexels search failed (page %d, %s): %s",
                    page, resp.status_code, resp.text[:200],
                )
                continue

            photos = resp.json().get("photos", [])

            if not photos:
                # Fall back to a generic health query
                params["query"] = "healthy lifestyle"
                params["page"] = 1
                resp = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params=params,
                    timeout=15,
                )
                photos = resp.json().get("photos", []) if resp.ok else []

            # Pick the first photo whose ID has NOT been used before.
            # Shuffle to add extra variety within the same page.
            random.shuffle(photos)
            for photo in photos:
                if photo["id"] not in used_ids:
                    image_url = photo["src"]["large2x"]
                    safe_kw = keyword.replace(" ", "-").lower()
                    filename = f"{safe_kw}-{photo['id']}.jpg"
                    logger.info(
                        "Pexels photo selected: id=%d query='%s' page=%d",
                        photo["id"], keyword, page,
                    )
                    return {
                        "id": photo["id"],
                        "url": image_url,
                        "filename": filename,
                        "photographer": photo.get("photographer", "Pexels"),
                        "photo_url": photo.get("url", "https://www.pexels.com"),
                    }

            # All photos on this page were already used — try next page
            logger.info(
                "All %d photos on page %d already used, trying next page...",
                len(photos), page,
            )

        except Exception as exc:
            logger.warning("Pexels fetch error (attempt %d): %s", attempt + 1, exc)

    logger.warning("No unused Pexels photos found for '%s' after 5 attempts.", keyword)
    return None


def insert_extra_pexels_images(
    content: str,
    keyword: str,
    auth_header: dict,
    target_count: int = 4,
    used_ids: set | None = None,
) -> str:
    """
    If the article has fewer than target_count images, fetch additional
    Pexels photos (using related search terms) and insert them at
    evenly-spaced H2 boundaries throughout the article.
    """
    if used_ids is None:
        used_ids = set()

    current = _count_images_in_content(content)
    needed = target_count - current

    if needed <= 0:
        logger.info("Image check: %d image(s) found — no extra images needed.", current)
        return content

    logger.info(
        "Image check: %d image(s) found, need %d more to reach %d total.",
        current, needed, target_count,
    )

    # Build varied search queries so we get different photos
    base_words = keyword.split()
    search_queries = [
        keyword,
        f"{base_words[0]} health" if base_words else "healthy living",
        "healthy lifestyle",
        "wellness nutrition",
        "medical health",
    ]

    # Find all positions — we insert images after H2 headings
    h2_positions = [m.end() for m in re.finditer(r'</h2>', content, re.IGNORECASE)]

    # Skip the first H2 (already has featured image after intro)
    insert_positions = h2_positions[1:] if len(h2_positions) > 1 else h2_positions

    images_added = 0
    offset = 0  # track content length change as we insert

    for i in range(needed):
        if images_added >= needed:
            break

        query = search_queries[i % len(search_queries)]

        # slot_index = current images already in article + extras added so far
        # This ensures each slot fetches from a different Pexels page.
        image_info = _fetch_pexels_image(
            query,
            used_ids=used_ids,
            slot_index=current + images_added,
        )

        if not image_info:
            continue

        media_id, media_url = _upload_image_to_wordpress(image_info, auth_header)

        if not media_id or not media_url:
            continue

        # Mark this photo as used so it won't appear in later slots
        used_ids.add(image_info["id"])

        caption = f'Photo by {image_info["photographer"]} on <a href="{image_info["photo_url"]}" target="_blank" rel="noopener noreferrer">Pexels</a>'
        img_html = (
            f'\n'
            f'<figure class="wp-block-image aligncenter">'
            f'<img src="{media_url}" alt="{query}" />'
            f'<figcaption>{caption}</figcaption>'
            f'</figure>\n'
        )

        # Insert after an H2 heading (spread evenly through the article)
        if i < len(insert_positions):
            pos = insert_positions[i] + offset
        else:
            # Fallback: insert before the FAQ section or near the end
            faq_pos = content.find('<h2>FREQUENTLY ASKED QUESTIONS</h2>')
            pos = (faq_pos + offset) if faq_pos != -1 else len(content) + offset - 50

        content = content[:pos] + img_html + content[pos:]
        offset += len(img_html)
        images_added += 1

        logger.info("Extra image %d/%d inserted (query: '%s')", images_added, needed, query)

    logger.info(
        "Image check complete: %d total image(s) in article.",
        current + images_added,
    )
    return content

# ───────────────────────────────────────────
# Auth helpers
# ───────────────────────────────────────────

def _get_auth_header() -> dict:
    """Build Basic Auth header from WordPress credentials."""
    token = base64.b64encode(
        f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()
    ).decode("utf-8")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }

# ───────────────────────────────────────────
# WordPress media upload
# ───────────────────────────────────────────

def _upload_image_to_wordpress(image_info: dict, auth_header: dict):
    """
    Download the image from Pexels and upload it to WordPress Media Library.
    Returns (media_id, media_url) or (None, None) on failure.
    """
    try:
        img_resp = requests.get(image_info["url"], timeout=30)
        if not img_resp.ok:
            logger.warning("Failed to download image from Pexels")
            return None, None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_resp.content)
            tmp_path = tmp.name

        upload_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/media"
        upload_headers = {
            "Authorization": auth_header["Authorization"],
            "Content-Disposition": f'attachment; filename="{image_info["filename"]}"',
        }

        with open(tmp_path, "rb") as img_file:
            upload_resp = requests.post(
                upload_url,
                headers=upload_headers,
                files={"file": (image_info["filename"], img_file, "image/jpeg")},
                timeout=60,
            )

        os.unlink(tmp_path)

        if upload_resp.ok:
            media_id = upload_resp.json().get("id")
            media_url = upload_resp.json().get("source_url", "")

            caption = f'Photo by {image_info["photographer"]} on <a href="{image_info["photo_url"]}" target="_blank" rel="noopener noreferrer">Pexels</a>'

            requests.post(
                f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/media/{media_id}",
                headers=auth_header,
                json={
                    "alt_text": image_info["filename"].replace("-", " ").replace(".jpg", ""),
                    "caption": caption,
                },
                timeout=15,
            )

            logger.info("Image uploaded to WP Media Library (ID: %d)", media_id)
            return media_id, media_url

        logger.warning(
            "WP media upload failed: %s %s",
            upload_resp.status_code, upload_resp.text[:200],
        )
        return None, None

    except Exception as exc:
        logger.warning("Image upload error: %s", exc)
        return None, None

# ───────────────────────────────────────────
# Insert image into article content
# ───────────────────────────────────────────

def _insert_image_into_content(
    content: str, media_url: str, alt_text: str, caption: str
) -> str:
    """Insert a featured image block after the first <p> tag."""
    if not media_url:
        return content

    img_html = (
        f'\n'
        f'<figure class="wp-block-image aligncenter">'
        f'<img src="{media_url}" alt="{alt_text}" />'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>\n'
    )

    insert_pos = content.find("<p>")
    if insert_pos != -1:
        return content[:insert_pos + 3] + img_html + content[insert_pos + 3:]

    return img_html + content

# ───────────────────────────────────────────
# Tag helpers
# ───────────────────────────────────────────

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

# ───────────────────────────────────────────
# Main publish function
# ───────────────────────────────────────────

def publish_article(article: dict, extra_used_pexels_ids: set | None = None) -> dict:
    """
    Pre-publish pipeline:
    1. Validate & fix all external links in the article
    2. Fix paragraphs exceeding 120 words (Rank Math 14.2)
    3. Fetch + upload a unique Pexels featured image
    4. Insert extra unique images to reach at least 4 total (Rank Math 14.3)
    5. Cross-check images against published articles and replace duplicates
    6. Publish to WordPress with Rank Math SEO meta

    Parameters:
        article: dict with keys title, content, meta_desc, focus_keyword, category
        extra_used_pexels_ids: set of Pexels photo IDs from previously published
                               articles (loaded from history.json). These are
                               merged with used_photos.json to prevent any
                               photo reuse across articles.
    """
    auth_header = _get_auth_header()
    api_url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/posts"

    # Resolve category
    category_name = article.get("category", "Diet")
    category_id = CATEGORY_IDS.get(category_name, CATEGORY_IDS["Diet"])

    # Build / resolve tags from focus keyword
    tag_ids = []
    for kw in article["focus_keyword"].split():
        if len(kw) > 3:
            tag_id = _get_or_create_tag(kw, auth_header)
            if tag_id:
                tag_ids.append(tag_id)

    # Load the set of Pexels photo IDs used in previous articles so we
    # never reuse the same photo across different posts.
    # Merge BOTH sources: used_photos.json + history.json published records
    used_ids = _load_used_photo_ids()
    if extra_used_pexels_ids:
        used_ids.update(extra_used_pexels_ids)

    logger.info("Pexels dedup: %d previously used photo IDs loaded", len(used_ids))

    # ── STEP 1: Validate & fix external links ──
    logger.info("STEP 1/6 - Validating external links...")
    content = validate_and_fix_links(article["content"])

    # ── STEP 2: Fix long paragraphs (Rank Math 14.2) ──
    logger.info("STEP 2/6 - Checking paragraph lengths (Rank Math 14.2)...")
    content = fix_long_paragraphs(content)

    # ── STEP 3: Pexels featured image ─────────
    logger.info("STEP 3/6 - Fetching unique Pexels featured image...")
    media_id = None
    pexels_ids_used = []  # Track Pexels IDs used in this article

    # slot_index=0 → first image slot for this article
    image_info = _fetch_pexels_image(
        article["focus_keyword"],
        used_ids=used_ids,
        slot_index=0,
    )

    if image_info:
        media_id, media_url = _upload_image_to_wordpress(image_info, auth_header)
        if media_id and media_url:
            # Mark photo as used immediately so extra-image step won't reuse it
            used_ids.add(image_info["id"])
            pexels_ids_used.append(image_info["id"])
            caption = f'Photo by {image_info["photographer"]} on <a href="{image_info["photo_url"]}" target="_blank" rel="noopener noreferrer">Pexels</a>'
            content = _insert_image_into_content(
                content, media_url, article["focus_keyword"], caption
            )
            logger.info("Featured image inserted into article content")
        else:
            media_id = None

    # ── STEP 4: Ensure at least 4 images (Rank Math 14.3) ──
    logger.info("STEP 4/6 - Checking image count (Rank Math 14.3)...")
    # Track image count before extras
    img_count_before = _count_images_in_content(content)

    content = insert_extra_pexels_images(
        content,
        article["focus_keyword"],
        auth_header,
        target_count=4,
        used_ids=used_ids,   # pass the shared set so all slots stay unique
    )

    # Collect any new Pexels IDs added by the extra images step
    # (IDs were added to used_ids inside insert_extra_pexels_images)
    img_count_after = _count_images_in_content(content)
    # All IDs added after the featured image are extras
    new_ids = used_ids - _load_used_photo_ids() - set(pexels_ids_used)
    pexels_ids_used.extend(new_ids)

    # ── STEP 5: Final cross-check — verify no Pexels image duplicates ──
    logger.info("STEP 5/6 - Final cross-check for Pexels image duplicates...")
    content, media_id, used_ids, pexels_ids_used = _cross_check_and_replace_duplicates(
        content, article["focus_keyword"], auth_header, media_id, used_ids, pexels_ids_used
    )

    # Persist updated used-photo IDs so the next article run benefits too
    _save_used_photo_ids(used_ids)

    # ── STEP 6: Publish ──────────────────────
    logger.info("STEP 6/6 - Publishing to WordPress...")

    seo_meta = {
        "rank_math_focus_keyword": article["focus_keyword"],
        "rank_math_description": article["meta_desc"],
        "rank_math_title": f"{article['title']} - 101HEALTHLIFE",
    }

    payload = {
        "title": article["title"],
        "content": content,
        "status": "publish",
        "categories": [category_id],
        "tags": tag_ids,
        "meta": seo_meta,
        "comment_status": "open",
        "ping_status": "open",
    }

    if media_id:
        payload["featured_media"] = media_id

    resp = requests.post(api_url, json=payload, headers=auth_header, timeout=30)

    if resp.status_code in (200, 201):
        post_data = resp.json()
        result = {
            "success": True,
            "post_id": post_data.get("id"),
            "url": post_data.get("link"),
            "title": article["title"],
            "category": category_name,
            "has_image": media_id is not None,
            "pexels_ids": pexels_ids_used,  # Record Pexels IDs in history
            "published_at": datetime.utcnow().isoformat(),
        }
        logger.info(
            "Published: %s -> %s (image: %s, pexels_ids: %s)",
            article["title"], result["url"],
            "YES" if media_id else "NO",
            pexels_ids_used,
        )
        return result

    logger.error(
        "Failed to publish '%s': %s %s",
        article["title"], resp.status_code, resp.text,
    )
    return {
        "success": False,
        "title": article["title"],
        "error_code": resp.status_code,
        "error_detail": resp.text,
        "published_at": datetime.utcnow().isoformat(),
    }


# ───────────────────────────────────────────
# Cross-article image duplication check
# ───────────────────────────────────────────

def _extract_pexels_ids_from_html(content: str) -> set[int]:
    """Extract all Pexels photo IDs found in the article HTML.

    Matches patterns like:
      - pexels.com/photo/xxxx-12345/
      - filename: keyword-12345.jpg
      - pexels-photo-12345
    """
    pexels_ids = set()

    # Match Pexels photo page URLs: pexels.com/photo/anything-12345/
    for m in re.finditer(r'pexels\.com/photo/[^"]*?-(\d+)/?', content, re.IGNORECASE):
        try:
            pexels_ids.add(int(m.group(1)))
        except ValueError:
            pass

    # Match common filename patterns: keyword-12345.jpg
    for m in re.finditer(r'[\w-]+-(\d{5,})\.jpg', content, re.IGNORECASE):
        try:
            pexels_ids.add(int(m.group(1)))
        except ValueError:
            pass

    # Match pexels-photo-NNNNN class patterns
    for m in re.finditer(r'pexels[-_](?:photo[-_])?(\d+)', content, re.IGNORECASE):
        try:
            pexels_ids.add(int(m.group(1)))
        except ValueError:
            pass

    return pexels_ids


def _cross_check_and_replace_duplicates(
    content: str,
    keyword: str,
    auth_header: dict,
    featured_media_id: int | None,
    used_ids: set,
    pexels_ids_used: list,
) -> tuple[str, int | None, set, list]:
    """Final check: scan the article content for Pexels image IDs that
    appear in the previously-used set (from used_photos.json + history.json).

    If duplicates are found, replace them with fresh Pexels photos.

    Returns (content, featured_media_id, used_ids, pexels_ids_used).
    """
    # The IDs saved to disk BEFORE this run (i.e. from previous articles)
    previously_saved = _load_used_photo_ids()

    # Also add any IDs from extra_used_pexels_ids that were merged in
    # (these come from history.json and may not be in used_photos.json)
    # We already have these in used_ids, so:
    # "previously used by OTHER articles" = used_ids - pexels_ids_used (this article)
    ids_from_this_article = set(pexels_ids_used)
    previously_used_by_others = used_ids - ids_from_this_article

    # Extract Pexels IDs from the actual HTML content
    content_pexels_ids = _extract_pexels_ids_from_html(content)

    if not content_pexels_ids:
        logger.info("No Pexels IDs found in article HTML — cross-check passed.")
        return content, featured_media_id, used_ids, pexels_ids_used

    logger.info("Found %d Pexels photo ID(s) in article HTML: %s",
                len(content_pexels_ids), sorted(content_pexels_ids))

    # Find duplicates: IDs that are in the content AND were used by previous articles
    duplicates = content_pexels_ids & previously_used_by_others

    if not duplicates:
        logger.info("Cross-check passed — all Pexels images are unique across articles.")
        return content, featured_media_id, used_ids, pexels_ids_used

    logger.warning("Found %d duplicate Pexels image(s): %s — replacing...",
                   len(duplicates), sorted(duplicates))

    replacements = 0
    for pid_int in duplicates:
        pid_str = str(pid_int)

        # Fetch a replacement image
        new_image = _fetch_pexels_image(
            keyword,
            used_ids=used_ids,
            slot_index=pid_int % 10,  # Vary page selection
        )

        if not new_image:
            logger.warning("Could not find replacement for Pexels ID %d — keeping original.", pid_int)
            continue

        # Upload the replacement
        new_media_id, new_media_url = _upload_image_to_wordpress(new_image, auth_header)

        if not new_media_id or not new_media_url:
            logger.warning("Could not upload replacement for Pexels ID %d — keeping original.", pid_int)
            continue

        # Mark new photo as used
        used_ids.add(new_image["id"])

        # Update pexels_ids_used: remove old, add new
        if pid_int in pexels_ids_used:
            pexels_ids_used.remove(pid_int)
        pexels_ids_used.append(new_image["id"])

        # Replace in content — try multiple patterns
        replaced = False

        # Pattern 1: <figure>...</figure> containing the old Pexels ID
        fig_pattern = re.compile(
            r'<figure[^>]*>.*?<img[^>]*src="[^"]*' + re.escape(pid_str) + r'[^"]*"[^>]*>.*?</figure>',
            re.DOTALL | re.IGNORECASE,
        )
        if fig_pattern.search(content):
            caption = f'Photo by {new_image["photographer"]} on <a href="{new_image["photo_url"]}" target="_blank" rel="noopener noreferrer">Pexels</a>'
            new_html = (
                f'\n'
                f'<figure class="wp-block-image aligncenter">'
                f'<img src="{new_media_url}" alt="{keyword}" />'
                f'<figcaption>{caption}</figcaption>'
                f'</figure>\n'
            )
            content = fig_pattern.sub(new_html, content, count=1)
            replaced = True

        # Pattern 2: Pexels link containing the ID (in caption/figcaption)
        if not replaced:
            link_pattern = re.compile(
                r'<a[^>]*href="[^"]*pexels\.com/photo/[^"]*' + re.escape(pid_str) + r'[^"]*"[^>]*>[^<]*</a>',
                re.IGNORECASE,
            )
            if link_pattern.search(content):
                # Replace just the link, keep the figure/img structure
                new_link = f'<a href="{new_image["photo_url"]}" target="_blank" rel="noopener noreferrer">Pexels</a>'
                content = link_pattern.sub(new_link, content, count=1)
                replaced = True

        # Pattern 3: filename pattern in src attribute
        if not replaced:
            src_pattern = re.compile(
                r'(src=")([^"]*' + re.escape(pid_str) + r'[^"]*)(")',
                re.IGNORECASE,
            )
            if src_pattern.search(content):
                content = src_pattern.sub(r'\g<1>' + new_media_url + r'\3', content, count=1)
                replaced = True

        if replaced:
            replacements += 1
            logger.info("Replaced duplicate Pexels image (ID: %d -> %d)", pid_int, new_image["id"])
        else:
            logger.warning("Could not locate Pexels ID %d in HTML content — keeping original.", pid_int)

    logger.info("Cross-check complete: replaced %d duplicate Pexels image(s).", replacements)
    return content, featured_media_id, used_ids, pexels_ids_used


# ───────────────────────────────────────────
# Connection test
# ───────────────────────────────────────────

def test_connection() -> bool:
    """Quick connectivity test — returns True if credentials are valid."""
    auth_header = _get_auth_header()
    url = f"{WORDPRESS_SITE_URL}/wp-json/wp/v2/users/me"

    resp = requests.get(url, headers=auth_header, timeout=15)

    if resp.ok:
        user = resp.json()
        print(f"WordPress: Connected as {user.get('name')} ({user.get('slug')})")

        if PEXELS_API_KEY and PEXELS_API_KEY != "YOUR-PEXELS-API-KEY-HERE":
            p = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": "health", "per_page": 1},
                timeout=10,
            )
            print("Pexels API: Connected OK" if p.ok else f"Pexels API: Error {p.status_code}")
        else:
            print("Pexels API: Key not configured")

        return True

    print(f"WordPress: Connection failed {resp.status_code}")
    return False
