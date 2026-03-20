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
    (If on Linux VPS, set TZ first:  TZ=Asia/Hong_Kong crontab -e)
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
from zoneinfo import ZoneInfo

from config import POSTS_PER_DAY, POST_TIME, TIMEZONE
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
    tz = ZoneInfo(TIMEZONE)
    now_local = datetime.now(tz)
    logger.info("Starting daily posting job — %s (%s)",
                now_local.strftime("%Y-%m-%d %H:%M"), TIMEZONE)

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
        # Convert POST_TIME from TIMEZONE to local machine time for the scheduler
        tz      = ZoneInfo(TIMEZONE)
        utc     = ZoneInfo("UTC")
        h, m    = map(int, POST_TIME.split(":"))
        # Build a today-date aware time in the target timezone, then convert to local
        from datetime import date, time as dtime
        import datetime as dt_module
        naive_target = dt_module.datetime.combine(date.today(), dtime(h, m))
        aware_target = naive_target.replace(tzinfo=tz)
        local_time   = aware_target.astimezone().strftime("%H:%M")

        logger.info("Daemon mode: posting at %s %s (= %s local machine time)",
                    POST_TIME, TIMEZONE, local_time)
        schedule.every().day.at(local_time).do(run_posting_job)
        logger.info("Scheduler started — next run at %s (local) / %s (%s)…",
                    local_time, POST_TIME, TIMEZONE)
        while True:
            schedule.run_pending()
            time.sleep(30)

    else:
        # Default: run once immediately
        run_posting_job()


if __name__ == "__main__":
    main()
