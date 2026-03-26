"""
WordPress Publisher with Pexels Image Support
===============================================
Publishes a generated article to WordPress via the REST API.
- Validates all external links before publishing (replaces broken ones)
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

import re
import requests
import base64
import logging
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
#  Fallback links by domain  (used when a link
#  is unreachable — swap to the site homepage)
# ─────────────────────────────────────────────
DOMAIN_FALLBACKS = {
    "healthline.com":          "https://www.healthline.com/nutrition",
    "mayoclinic.org":          "https://www.mayoclinic.org/healthy-lifestyle",
    "nutrition.gov":           "https://www.nutrition.gov",
    "hsph.harvard.edu":        "https://www.hsph.harvard.edu/nutritionsource",
    "niddk.nih.gov":           "https://www.niddk.nih.gov/health-information",
    "cdc.gov":                 "https://www.cdc.gov/healthyliving",
    "ods.od.nih.gov":          "https://ods.od.nih.gov/factsheets/list-all",
    "who.int":                 "https://www.who.int/health-topics",
    "nhs.uk":                  "https://www.nhs.uk/live-well",
    "medlineplus.gov":         "https://medlineplus.gov",
    "nimh.nih.gov":            "https://www.nimh.nih.gov/health",
    "mind.org.uk":             "https://www.mind.org.uk/information-support",
    "mentalhealth.gov":        "https://www.mentalhealth.gov",
    "psychologytoday.com":     "https://www.psychologytoday.com/us/basics",
    "healthcare.gov":          "https://www.healthcare.gov",
    "cms.gov":                 "https://www.cms.gov",
    "kff.org":                 "https://www.kff.org/health-topics",
    "nerdwallet.com":          "https://www.nerdwallet.com/health-insurance",
    "smokefree.gov":           "https://smokefree.gov",
    "ncbi.nlm.nih.gov":        "https://www.ncbi.nlm.nih.gov",
    "healthit.gov":            "https://www.healthit.gov",
    "nature.com":              "https://www.nature.com/subjects/health-sciences",
    "nia.nih.gov":             "https://www.nia.nih.gov/health",
    "caregiver.org":           "https://www.caregiver.org/resource/caregiver-help-start",
}


# ─────────────────────────────────────────────
#  External link validator
# ─────────────────────────────────────────────
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
        resp = requests.head(url, headers=headers, timeout=timeout,
                             allow_redirects=True)
        if resp.status_code < 400:
            return True
        # Some servers reject HEAD — retry with GET
        resp = requests.get(url, headers=headers, timeout=timeout,
                            allow_redirects=True, stream=True)
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
    Scan all <a href="..."> external links in *content*.
    For each link:
      - If reachable   → keep as-is
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
            logger.info("  [OK]     %s", url)
        else:
            fallback = _get_fallback_for_url(url)
            logger.warning("  [BROKEN] %s  ->  replacing with  %s", url, fallback)
            # Replace all occurrences of this exact href in the content
            content = content.replace(f'href="{url}"', f'href="{fallback}"')
            replacements += 1

    logger.info("Link check complete — %d broken link(s) replaced.", replacements)
    return content


# ─────────────────────────────────────────────
#  Check 1: Paragraph length (Rank Math 14.2)
#  Rank Math fails if any <p> exceeds 120 words
# ─────────────────────────────────────────────
def fix_long_paragraphs(content: str, max_words: int = 120) -> str:
    """
    Find any <p>...</p> blocks exceeding max_words and split them
    at a sentence boundary into two shorter paragraphs.
    Returns the updated content string.
    """
    pattern = re.compile(r'<p>(.*?)</p>', re.DOTALL | re.IGNORECASE)
    fixes   = 0

    def split_paragraph(match):
        nonlocal fixes
        inner = match.group(1)
        # Count words (strip inner tags for counting only)
        plain = re.sub(r'<[^>]+>', '', inner)
        words = plain.split()
        if len(words) <= max_words:
            return match.group(0)   # fine — leave unchanged

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
        half      = len(words) // 2
        count     = 0
        split_at  = len(sentences) // 2   # default: split in half
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
        logger.info("Paragraph check: split %d long paragraph(s) (max %d words each).",
                    fixes, max_words)
    else:
        logger.info("Paragraph check: all paragraphs OK (max %d words).", max_words)
    return new_content


# ─────────────────────────────────────────────
#  Check 2: Image count (Rank Math 14.3)
#  Rank Math requires at least 4 images for
#  a 100% score on the media test
# ─────────────────────────────────────────────
def _count_images_in_content(content: str) -> int:
    """Count <img> tags in the article content."""
    return len(re.findall(r'<img\s', content, re.IGNORECASE))


def insert_extra_pexels_images(content: str, keyword: str,
                                auth_header: dict,
                                target_count: int = 4) -> str:
    """
    If the article has fewer than target_count images, fetch additional
    Pexels photos (using related search terms) and insert them at
    evenly-spaced H2 boundaries throughout the article.
    """
    current = _count_images_in_content(content)
    needed  = target_count - current

    if needed <= 0:
        logger.info("Image check: %d image(s) found — no extra images needed.", current)
        return content

    logger.info("Image check: %d image(s) found, need %d more to reach %d total.",
                current, needed, target_count)

    # Build varied search queries so we get different photos
    base_words = keyword.split()
    search_queries = [
        keyword,
        f"{base_words[0]} health" if base_words else "healthy living",
        "healthy lifestyle",
        "wellness nutrition",
        "medical health",
    ]

    # Find all </h2> positions — we insert images after H2 headings
    h2_positions = [m.end() for m in re.finditer(r'</h2>', content, re.IGNORECASE)]

    # Skip the first H2 (already has featured image after intro)
    insert_positions = h2_positions[1:] if len(h2_positions) > 1 else h2_positions

    images_added = 0
    offset       = 0   # track content length change as we insert

    for i in range(needed):
        if images_added >= needed:
            break

        query      = search_queries[i % len(search_queries)]
        image_info = _fetch_pexels_image(query)
        if not image_info:
            continue

        # Use a different photo ID by requesting page 2 for variety
        if i > 0:
            try:
                headers_p = {"Authorization": PEXELS_API_KEY}
                resp = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers_p,
                    params={"query": query, "orientation": "landscape",
                            "size": "large", "per_page": 5, "page": i + 1},
                    timeout=15,
                )
                if resp.ok and resp.json().get("photos"):
                    photo       = resp.json()["photos"][0]
                    image_info  = {
                        "url":          photo["src"]["large2x"],
                        "filename":     f"{query.replace(' ','-')}-{photo['id']}.jpg",
                        "photographer": photo.get("photographer", "Pexels"),
                        "photo_url":    photo.get("url", "https://www.pexels.com"),
                    }
            except Exception:
                pass

        media_id, media_url = _upload_image_to_wordpress(image_info, auth_header)
        if not media_id or not media_url:
            continue

        caption  = (f'Photo by <a href="{image_info["photo_url"]}" '
                    f'target="_blank">{image_info["photographer"]}</a> on Pexels')
        img_html = (
            f'\n<figure class="wp-block-image size-large">'
            f'<img src="{media_url}" alt="{query}" class="wp-image" />'
            f'<figcaption>{caption}</figcaption>'
            f'</figure>\n'
        )

        # Insert after an H2 heading (spread evenly through the article)
        if i < len(insert_positions):
            pos = insert_positions[i] + offset
        else:
            # Fallback: insert before the FAQ section or near the end
            faq_pos = content.find('<h2>Frequently Asked Questions')
            pos = (faq_pos + offset) if faq_pos != -1 else len(content) + offset - 50

        content  = content[:pos] + img_html + content[pos:]
        offset  += len(img_html)
        images_added += 1
        logger.info("Extra image %d/%d inserted (query: '%s')", images_added, needed, query)

    logger.info("Image check complete: %d total image(s) in article.",
                current + images_added)
    return content


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
            params["query"] = "healthy lifestyle"
            resp = requests.get("https://api.pexels.com/v1/search",
                                headers=headers, params=params, timeout=15)
            photos = resp.json().get("photos", []) if resp.ok else []

        if not photos:
            logger.warning("No Pexels photos found for '%s'", keyword)
            return None

        photo     = photos[0]
        image_url = photo["src"]["large2x"]
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
def _upload_image_to_wordpress(image_info: dict, auth_header: dict):
    """
    Download the image from Pexels and upload it to WordPress media library.
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

        os.unlink(tmp_path)

        if upload_resp.ok:
            media_id  = upload_resp.json().get("id")
            media_url = upload_resp.json().get("source_url", "")

            caption = (f'Photo by <a href="{image_info["photo_url"]}" '
                       f'target="_blank">{image_info["photographer"]}</a> on '
                       f'<a href="https://www.pexels.com" target="_blank">Pexels</a>')

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
    """Insert a featured image block after the first </p> tag."""
    if not media_url:
        return content

    img_html = (
        f'\n<figure class="wp-block-image size-large">'
        f'<img src="{media_url}" alt="{alt_text}" class="wp-image" />'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>\n'
    )

    insert_pos = content.find("</p>")
    if insert_pos != -1:
        return content[:insert_pos + 4] + img_html + content[insert_pos + 4:]
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
    Pre-publish pipeline:
      1. Validate & fix all external links in the article
      2. Fix paragraphs exceeding 120 words (Rank Math 14.2)
      3. Fetch + upload a Pexels featured image
      4. Insert extra images to reach at least 4 total (Rank Math 14.3)
      5. Publish to WordPress with Rank Math SEO meta
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

    # ── Step 1: Validate & fix external links ──
    logger.info("Step 1/5 - Validating external links...")
    content = validate_and_fix_links(article["content"])

    # ── Step 2: Fix long paragraphs (Rank Math 14.2) ──
    logger.info("Step 2/5 - Checking paragraph lengths (Rank Math 14.2)...")
    content = fix_long_paragraphs(content)

    # ── Step 3: Pexels featured image ─────────
    logger.info("Step 3/5 - Fetching Pexels featured image...")
    media_id = None
    image_info = _fetch_pexels_image(article["focus_keyword"])

    if image_info:
        media_id, media_url = _upload_image_to_wordpress(image_info, auth_header)
        if media_id and media_url:
            caption  = (f'Photo by <a href="{image_info["photo_url"]}" '
                        f'target="_blank">{image_info["photographer"]}</a> on Pexels')
            content  = _insert_image_into_content(
                content, media_url, article["focus_keyword"], caption)
            logger.info("Featured image inserted into article content")
        else:
            media_id = None

    # ── Step 4: Ensure at least 4 images (Rank Math 14.3) ──
    logger.info("Step 4/5 - Checking image count (Rank Math 14.3)...")
    content = insert_extra_pexels_images(
        content, article["focus_keyword"], auth_header, target_count=4
    )

    # ── Step 5: Publish ────────────────────────
    logger.info("Step 5/5 - Publishing to WordPress...")

    seo_meta = {
        "rank_math_focus_keyword": article["focus_keyword"],
        "rank_math_description":   article["meta_desc"],
        "rank_math_title":         f"{article['title']} - 101HealthLife",
    }

    payload = {
        "title":          article["title"],
        "content":        content,
        "status":         "publish",
        "categories":     [category_id],
        "tags":           tag_ids,
        "meta":           seo_meta,
        "comment_status": "open",
        "ping_status":    "open",
    }

    if media_id:
        payload["featured_media"] = media_id

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

        if PEXELS_API_KEY and PEXELS_API_KEY != "your-pexels-api-key-here":
            p = requests.get("https://api.pexels.com/v1/search",
                             headers={"Authorization": PEXELS_API_KEY},
                             params={"query": "health", "per_page": 1}, timeout=10)
            print("Pexels API: Connected OK" if p.ok else f"Pexels API: Error {p.status_code}")
        else:
            print("Pexels API: Key not configured")
        return True

    print(f"WordPress: Connection failed {resp.status_code}")
    return False
