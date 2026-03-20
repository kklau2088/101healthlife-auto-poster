"""
Configuration file for 101healthlife.com Auto SEO Poster
=========================================================
Fill in your WordPress credentials and Groq API key below.
"""

# ─────────────────────────────────────────────
#  WordPress Credentials
# ─────────────────────────────────────────────
WORDPRESS_SITE_URL = "https://101healthlife.com"
WORDPRESS_USERNAME = "your_wordpress_username"   # e.g. "admin"
WORDPRESS_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"  # WordPress Application Password

# ─────────────────────────────────────────────
#  Groq API Key  (100% FREE — no credit card needed)
#  Get your free key at: https://console.groq.com/keys
# ─────────────────────────────────────────────
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ─────────────────────────────────────────────
#  Groq Model Selection  (all FREE)
# ─────────────────────────────────────────────
# Recommended models (all free, no region restriction):
#   "llama-3.3-70b-versatile"   — Best quality, 14,400 req/day  (recommended)
#   "llama-3.1-8b-instant"      — Fastest, 14,400 req/day
#   "mixtral-8x7b-32768"        — Good quality, large context
GROQ_MODEL = "llama-3.3-70b-versatile"

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
