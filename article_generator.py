"""
Article Generator using Groq API (FREE)
========================================
Generates fully SEO-optimised WordPress articles with:
  - Proper H1 / H2 / H3 structure
  - Focus keyword integration
  - Meta description
  - Compelling introduction + conclusion
  - FAQ section (boosts featured-snippet chances)

Groq free tier limits:
  llama-3.3-70b-versatile — 14,400 requests/day, 6,000 tokens/min
  No credit card required, no region restrictions.
"""

from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, ARTICLE_MIN_WORDS, ARTICLE_MAX_WORDS, LANGUAGE, TARGET_REGION


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
    client = Groq(api_key=GROQ_API_KEY)

    region_note = f" Target readers are primarily from {TARGET_REGION}." if TARGET_REGION != "global" else ""

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
1. Use the focus keyword naturally in: the first 100 words, at least 2 H2 headings, and the conclusion.
2. Use related LSI keywords throughout (do NOT keyword-stuff).
3. Structure: Intro -> 5-7 H2 sections (each with 1-2 H3 sub-sections) -> FAQ (4-5 Q&As) -> Conclusion.
4. FAQ section must use <h2>Frequently Asked Questions</h2> and <h3>Q: ...</h3> / <p>A: ...</p> format.
5. Include the meta description as an HTML comment at the very top.

OUTPUT FORMAT — return ONLY valid WordPress HTML (no markdown fences, no extra commentary):

<!-- meta_description: {topic['meta_desc']} -->
<h1>{topic['title']}</h1>

[Full article HTML here]
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
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
