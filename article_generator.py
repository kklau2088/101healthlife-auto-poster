"""
Article Generator using OpenRouter / chatanywhere API
======================================================
Uses OpenAI-compatible API format.
Includes automatic word count validation — if the generated article
is shorter than ARTICLE_MIN_WORDS, the system automatically requests
the AI to expand it until the minimum is reached (up to 3 attempts).

Get your free OpenRouter key: https://openrouter.ai
Get your free chatanywhere key: https://github.com/chatanywhere/GPT_API_free
"""

import re
from openai import OpenAI
from config import API_KEY, API_BASE_URL, API_MODEL, ARTICLE_MIN_WORDS, ARTICLE_MAX_WORDS, LANGUAGE, TARGET_REGION

import logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  High-authority external link sources
# ─────────────────────────────────────────────
AUTHORITY_SOURCES = {
    "Diet": [
        "https://www.healthline.com",
        "https://www.mayoclinic.org",
        "https://www.nutrition.gov",
        "https://www.hsph.harvard.edu/nutritionsource",
    ],
    "Weight Loss": [
        "https://www.niddk.nih.gov",
        "https://www.cdc.gov/healthyweight",
        "https://www.mayoclinic.org",
        "https://www.healthline.com",
    ],
    "Nutrition": [
        "https://www.nutrition.gov",
        "https://ods.od.nih.gov",
        "https://www.hsph.harvard.edu/nutritionsource",
        "https://www.who.int/nutrition",
    ],
    "Mental Health": [
        "https://www.nimh.nih.gov",
        "https://www.mind.org.uk",
        "https://www.mentalhealth.gov",
        "https://www.psychologytoday.com",
    ],
    "Health": [
        "https://www.who.int",
        "https://www.cdc.gov",
        "https://www.nhs.uk",
        "https://www.mayoclinic.org",
        "https://medlineplus.gov",
    ],
    "Health Insurance": [
        "https://www.healthcare.gov",
        "https://www.cms.gov",
        "https://www.kff.org",
        "https://www.nerdwallet.com/health-insurance",
    ],
    "Smoking": [
        "https://www.cdc.gov/tobacco",
        "https://www.nhs.uk/live-well/quit-smoking",
        "https://smokefree.gov",
        "https://www.who.int/tobacco",
    ],
    "AI in Health": [
        "https://www.who.int/health-topics/digital-health",
        "https://www.ncbi.nlm.nih.gov",
        "https://www.healthit.gov",
        "https://www.nature.com/subjects/machine-learning",
    ],
    "Care": [
        "https://www.cdc.gov/aging",
        "https://www.nia.nih.gov",
        "https://www.caregiver.org",
        "https://www.mayoclinic.org",
    ],
}


def _get_sources_for_category(category: str) -> list:
    """Return authority source URLs for the given category."""
    return AUTHORITY_SOURCES.get(category, AUTHORITY_SOURCES["Health"])


def _count_words(html: str) -> int:
    """Strip HTML tags and count words in plain text."""
    plain = re.sub(r"<[^>]+>", " ", html)       # remove tags
    plain = re.sub(r"<!--.*?-->", " ", plain)    # remove comments
    plain = re.sub(r"\s+", " ", plain).strip()   # collapse whitespace
    return len(plain.split())


def _build_client() -> OpenAI:
    """Create the OpenAI-compatible client with correct headers."""
    extra_headers = {}
    if "openrouter.ai" in API_BASE_URL:
        extra_headers = {
            "HTTP-Referer": "https://101healthlife.com",
            "X-Title":      "101HealthLife SEO Auto Poster",
        }
    return OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
        default_headers=extra_headers,
    )


def _call_api(client: OpenAI, messages: list) -> str:
    """Send messages to the API and return stripped content string."""
    response = client.chat.completions.create(
        model=API_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=5000,   # raised to 5000 to allow longer articles
    )
    raw = response.choices[0].message.content.strip()

    # Strip optional markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("html"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    return raw


def generate_article(topic: dict) -> dict:
    """
    Generate a full SEO article, then verify word count.
    If the article is shorter than ARTICLE_MIN_WORDS, automatically
    ask the AI to expand it — up to MAX_EXPAND_ATTEMPTS times.

    topic keys expected:
        title, category, focus_keyword, meta_desc
    """
    MAX_EXPAND_ATTEMPTS = 3

    client       = _build_client()
    region_note  = (f" Target readers are primarily from {TARGET_REGION}."
                    if TARGET_REGION != "global" else "")
    sources      = _get_sources_for_category(topic["category"])
    sources_list = "\n".join(f"  - {s}" for s in sources)

    system_prompt = (
        "You are an expert health & wellness content writer and SEO specialist. "
        "You write authoritative, engaging, and well-researched articles for a health blog. "
        "Your writing style is professional yet accessible, using clear language that a general audience can understand. "
        "You always back claims with references to studies or expert consensus. "
        "You output ONLY valid WordPress HTML — no markdown fences, no extra commentary."
    )

    user_prompt = f"""Write a comprehensive, SEO-optimised health article for a WordPress blog.

ARTICLE REQUIREMENTS:
- Title (H1): {topic['title']}
- Focus keyword: {topic['focus_keyword']}
- Category: {topic['category']}
- Language: {LANGUAGE}{region_note}
- Word count: MINIMUM {ARTICLE_MIN_WORDS} words, TARGET {ARTICLE_MAX_WORDS} words
  IMPORTANT: The article MUST contain at least {ARTICLE_MIN_WORDS} words.
  Do NOT stop writing until you have reached this minimum.
  Each H2 section should contain at least 150-200 words of body text.
- Tone: Professional, authoritative, empathetic

SEO REQUIREMENTS:
1. KEYWORD DENSITY — keep the focus keyword density at approximately 1% of total word count.
   Place the focus keyword ONLY in these 4 locations:
     a) The H1 title
     b) The first paragraph (intro) — use it once naturally
     c) ONE H2 heading only (choose the most relevant section)
     d) The final conclusion paragraph — use it once
   Do NOT repeat the focus keyword anywhere else in the article.

2. SYNONYM & PRONOUN STRATEGY — in all other sections replace the focus keyword with:
   - Natural synonyms        (e.g. "this eating approach", "this dietary pattern", "the regimen")
   - Descriptive phrases     (e.g. "this way of eating", "this nutritional strategy", "the plan")
   - Pronouns & references   (e.g. "it", "this approach", "the method described above")
   - LSI / semantic keywords (related terms Google associates with the topic, NOT the exact phrase)
   This produces naturally flowing prose and avoids any keyword-stuffing penalty.

3. Structure: Intro -> 5-7 H2 sections (each with 1-2 H3 sub-sections, min 150 words per section)
   -> FAQ (4-5 Q&As, each answer at least 60 words) -> Conclusion (at least 100 words).
4. FAQ section must use <h2>Frequently Asked Questions</h2> and <h3>Q: ...</h3> / <p>A: ...</p> format.
5. Include the meta description as an HTML comment at the very top.

EXTERNAL LINKS REQUIREMENTS (IMPORTANT):
- Include 3-5 external links to authoritative sources throughout the article body.
- Link anchor text must be natural and descriptive (e.g. "according to the World Health Organization").
- All external links must use target="_blank" rel="noopener noreferrer" attributes.
- Use ONLY these trusted domains as your external link sources:
{sources_list}
- Place links naturally within sentences where they add credibility — NOT in a separate reference list.
- Example format: <a href="https://www.who.int/nutrition" target="_blank" rel="noopener noreferrer">World Health Organization</a>

OUTPUT FORMAT — return ONLY valid WordPress HTML (no markdown fences, no extra commentary):

<!-- meta_description: {topic['meta_desc']} -->
<h1>{topic['title']}</h1>

[Full article HTML here — remember MINIMUM {ARTICLE_MIN_WORDS} words]
"""

    # ── Initial generation ────────────────────
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    logger.info("Generating article: %s", topic["title"])
    raw_content = _call_api(client, messages)
    word_count  = _count_words(raw_content)
    logger.info("Initial generation: %d words", word_count)

    # ── Auto-expand if too short ──────────────
    attempt = 0
    while word_count < ARTICLE_MIN_WORDS and attempt < MAX_EXPAND_ATTEMPTS:
        attempt += 1
        shortfall = ARTICLE_MIN_WORDS - word_count
        logger.warning(
            "Article too short (%d words, minimum %d). "
            "Expanding... (attempt %d/%d)",
            word_count, ARTICLE_MIN_WORDS, attempt, MAX_EXPAND_ATTEMPTS
        )

        expand_prompt = (
            f"The article you wrote is only {word_count} words, "
            f"but it must be at least {ARTICLE_MIN_WORDS} words. "
            f"It is {shortfall} words too short.\n\n"
            f"Please expand the existing article by:\n"
            f"1. Adding more detail and explanation to each H2 section (at least 100 more words per section)\n"
            f"2. Expanding each FAQ answer to be more thorough (at least 80 words each)\n"
            f"3. Adding practical tips, examples, or evidence-based information\n"
            f"4. Expanding the conclusion to at least 120 words\n\n"
            f"Return the COMPLETE expanded article as valid WordPress HTML. "
            f"Do NOT summarise — return the full article from start to finish."
        )

        messages.append({"role": "assistant", "content": raw_content})
        messages.append({"role": "user",      "content": expand_prompt})

        raw_content = _call_api(client, messages)
        word_count  = _count_words(raw_content)
        logger.info("After expansion attempt %d: %d words", attempt, word_count)

    if word_count < ARTICLE_MIN_WORDS:
        logger.warning(
            "Could not reach minimum word count after %d attempts. "
            "Publishing with %d words.",
            MAX_EXPAND_ATTEMPTS, word_count
        )
    else:
        logger.info("Word count OK: %d words (min: %d)", word_count, ARTICLE_MIN_WORDS)

    return {
        "title":         topic["title"],
        "content":       raw_content,
        "meta_desc":     topic["meta_desc"],
        "focus_keyword": topic["focus_keyword"],
        "category":      topic["category"],
        "word_count":    word_count,
    }
