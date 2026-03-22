"""
Article Generator using chatanywhere free API
=============================================
Uses OpenAI-compatible API format with chatanywhere free endpoint.
Free tier: 200 requests/day (GPT series), 30/day (DeepSeek)
No region restrictions — works in Hong Kong & mainland China.

Get your free key: https://github.com/chatanywhere/GPT_API_free
"""

from openai import OpenAI
from config import API_KEY, API_BASE_URL, API_MODEL, ARTICLE_MIN_WORDS, ARTICLE_MAX_WORDS, LANGUAGE, TARGET_REGION


# ─────────────────────────────────────────────
#  High-authority external link sources
#  These are trusted, SEO-friendly domains that
#  Google recognises as authoritative references.
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


def generate_article(topic: dict) -> dict:
    """
    Generate a full SEO article for the given topic dict.

    topic keys expected:
        title         - Article H1 title
        category      - Site category name
        focus_keyword - Primary SEO keyword
        meta_desc     - SEO meta description (<=160 chars)

    Returns a dict with:
        title, content (HTML), meta_desc, focus_keyword, category
    """
    # OpenRouter requires HTTP-Referer and X-Title headers
    # to identify the app and avoid guardrail/privacy restrictions
    extra_headers = {}
    if "openrouter.ai" in API_BASE_URL:
        extra_headers = {
            "HTTP-Referer": "https://101healthlife.com",
            "X-Title":      "101HealthLife SEO Auto Poster",
        }

    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
        default_headers=extra_headers,
    )

    region_note = f" Target readers are primarily from {TARGET_REGION}." if TARGET_REGION != "global" else ""

    # Get authority sources relevant to this article's category
    sources = _get_sources_for_category(topic["category"])
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
- Word count: {ARTICLE_MIN_WORDS}-{ARTICLE_MAX_WORDS} words
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

3. Structure: Intro -> 5-7 H2 sections (each with 1-2 H3 sub-sections) -> FAQ (4-5 Q&As) -> Conclusion.
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

[Full article HTML here]
"""

    response = client.chat.completions.create(
        model=API_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    raw_content = response.choices[0].message.content.strip()

    # Strip optional markdown code fences if model wraps output
    if raw_content.startswith("```"):
        raw_content = raw_content.split("```", 2)[1]
        if raw_content.startswith("html"):
            raw_content = raw_content[4:]
        raw_content = raw_content.rsplit("```", 1)[0].strip()

    return {
        "title":         topic["title"],
        "content":       raw_content,
        "meta_desc":     topic["meta_desc"],
        "focus_keyword": topic["focus_keyword"],
        "category":      topic["category"],
    }
