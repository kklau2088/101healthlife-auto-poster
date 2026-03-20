"""
Configuration file for 101healthlife.com Auto SEO Poster
=========================================================
Fill in your WordPress credentials and API key below.
"""

# ─────────────────────────────────────────────
#  WordPress Credentials
# ─────────────────────────────────────────────
WORDPRESS_SITE_URL = "https://101healthlife.com"
WORDPRESS_USERNAME = "your_wordpress_username"   # e.g. "admin"
WORDPRESS_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"  # WordPress Application Password

# ─────────────────────────────────────────────
#  AI API Settings
#  Using chatanywhere free API (compatible with OpenAI format)
#  Get free key: https://github.com/chatanywhere/GPT_API_free
# ─────────────────────────────────────────────
API_KEY      = "your-api-key-here"                    # Paste your sk-... key here
API_BASE_URL = "https://api.chatanywhere.tech/v1"     # Domestic: chatanywhere.tech
                                                       # Overseas: chatanywhere.org

# ─────────────────────────────────────────────
#  Model Selection
# ─────────────────────────────────────────────
# Free models available (200 req/day for GPT series, 30/day for DeepSeek):
#   "gpt-4o-mini"      — Best balance of quality & speed (recommended)
#   "gpt-3.5-turbo"    — Faster, higher daily limit
#   "deepseek-v3"      — Excellent quality, 30 req/day free
API_MODEL = "gpt-4o-mini"

# ─────────────────────────────────────────────
#  Posting Schedule
# ─────────────────────────────────────────────
POSTS_PER_DAY = 1          # Number of articles to publish per day
POST_TIME = "08:00"        # Time to publish (24-hour format, UTC+8 Hong Kong/Taiwan time)
TIMEZONE = "Asia/Hong_Kong"  # Timezone for scheduling — change if needed

# ─────────────────────────────────────────────
#  WordPress Category IDs  (from your site)
# ─────────────────────────────────────────────
CATEGORY_IDS = {
    "Diet":            1,
    "Weight Loss":     16,
    "Health":          17,
    "Nutrition":       19,
    "Smoking":         21,
    "Care":            22,
    "Health Insurance":23,
    "Mental Health":   73,
    "AI in Health":    39,
}

# ─────────────────────────────────────────────
#  Article Generation Settings
# ─────────────────────────────────────────────
ARTICLE_MIN_WORDS = 1200   # Minimum word count per article
ARTICLE_MAX_WORDS = 2000   # Maximum word count per article
LANGUAGE = "English"       # Article language
TARGET_REGION = "global"   # "global", "UK", "US", "AU", etc.
