"""
Daily SEO Auto-Poster — Main Scheduler
========================================
Run this script once and it will:
  1. Pick the next unused topic from topics.py
  2. Generate a full SEO article via OpenAI GPT-4o
  3. Publish it to 101healthlife.com via WordPress REST API
  4. Log all activity to poster.log and history.json

Scheduling options:
  • Cron (recommended):  0 8 * * * /usr/bin/python3 /path/to/main.py
  • OR keep-alive loop:   python3 main.py --daemon
"""

import argparse
import json
import logging
import os
import schedule
import time
from datetime import datetime
from pathlib import Path

from config import POSTS_PER_DAY, POST_TIME
from topics import TOPIC_BANK
from article_generator import generate_article
from wp_publisher import publish_article, test_connection

# ─────────────────────────────────────────────
#  Logging setup
# ─────────────────────────────────────────────
LOG_FILE     = Path(__file__).parent / "poster.log"
HISTORY_FILE = Path(__file__).parent / "history.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  History helpers
# ─────────────────────────────────────────────
def load_history() -> dict:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": [], "next_topic_index": 0}


def save_history(history: dict) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_next_topic(history: dict) -> tuple[dict, int]:
    """Return the next topic and its index, cycling back when exhausted."""
    idx = history.get("next_topic_index", 0) % len(TOPIC_BANK)
    return TOPIC_BANK[idx], idx


# ─────────────────────────────────────────────
#  Core posting job
# ─────────────────────────────────────────────
def run_posting_job() -> None:
    logger.info("═" * 60)
    logger.info("Starting daily posting job — %s", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

    history = load_history()
    posts_today = 0

    for _ in range(POSTS_PER_DAY):
        topic, idx = get_next_topic(history)
        logger.info("Topic #%d: %s [%s]", idx, topic["title"], topic["category"])

        try:
            logger.info("Generating article...")
            article = generate_article(topic)
            word_count = len(article["content"].split())
            logger.info("Article generated — approx. %d words", word_count)

            logger.info("Publishing to WordPress...")
            result = publish_article(article)

            if result["success"]:
                history["published"].append({
                    "topic_index": idx,
                    "title":       result["title"],
                    "url":         result["url"],
                    "post_id":     result["post_id"],
                    "category":    result["category"],
                    "date":        result["published_at"],
                })
                history["next_topic_index"] = (idx + 1) % len(TOPIC_BANK)
                posts_today += 1
                logger.info("✅ Success: %s → %s", result["title"], result["url"])
            else:
                logger.error("❌ Failed: %s — %s", result["title"], result.get("error_detail", ""))

        except Exception as exc:
            logger.exception("Unexpected error processing topic %d: %s", idx, exc)

    save_history(history)
    logger.info("Job complete — %d/%d post(s) published today.", posts_today, POSTS_PER_DAY)
    logger.info("═" * 60)


# ─────────────────────────────────────────────
#  Entry points
# ─────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="101healthlife.com Auto SEO Poster")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Keep running as a background daemon, posting at the configured time each day.",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run one posting job immediately (useful for testing).",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test WordPress API credentials without posting.",
    )
    args = parser.parse_args()

    if args.test_connection:
        test_connection()
        return

    if args.now:
        run_posting_job()
        return

    if args.daemon:
        logger.info("Daemon mode: scheduling daily post at %s", POST_TIME)
        schedule.every().day.at(POST_TIME).do(run_posting_job)
        logger.info("Scheduler started — waiting for next run at %s...", POST_TIME)
        while True:
            schedule.run_pending()
            time.sleep(30)

    else:
        # Default: run once immediately
        run_posting_job()


if __name__ == "__main__":
    main()
