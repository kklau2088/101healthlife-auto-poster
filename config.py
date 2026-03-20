"""
Configuration file for 101healthlife.com Auto SEO Poster
=========================================================
Fill in your WordPress credentials and OpenAI API key below.
"""

# ─────────────────────────────────────────────
#  WordPress Credentials
# ─────────────────────────────────────────────
WORDPRESS_SITE_URL = "https://101healthlife.com"
WORDPRESS_USERNAME = "your_wordpress_username"   # e.g. "admin"
WORDPRESS_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"  # WordPress Application Password

# ─────────────────────────────────────────────
#  OpenAI API Key  (for article generation)
# ─────────────────────────────────────────────
OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

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

# ─────────────────────────────────────────────
#  OpenAI Model Selection
# ─────────────────────────────────────────────
# Choose ONE of the following models:
#   "gpt-4o"          — Best quality, requires paid OpenAI account (~$0.05/article)
#   "gpt-4o-mini"     — Good quality, cheaper (~$0.005/article), requires paid account
#   "gpt-3.5-turbo"   — Basic quality, works on free/new accounts
OPENAI_MODEL = "gpt-4o-mini"  # <-- Change this if you get a 403 model_not_found error
