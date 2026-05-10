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
import io
import json
import logging
import os
import sys
import schedule
import time
from datetime import datetime
from pathlib import Path

# Fix Windows console Unicode encoding (handles special chars like = - >)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from config import POSTS_PER_DAY, POST_TIME, TIMEZONE
from topics import TOPIC_BANK
from article_generator import generate_article
from wp_publisher import publish_article, test_connection, load_all_used_pexels_ids

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


def get_next_topic(history: dict) -> tuple[dict, int] | None:
    """Return the next unpublished topic and its index.

    Scans from next_topic_index forward, skipping topics whose title
    already appears in history["published"].  Returns None when ALL
    topics have been published (no duplicates).
    """
    published_titles = {rec.get("title", "") for rec in history.get("published", []) if rec.get("title")}
    start = history.get("next_topic_index", 0)
    n = len(TOPIC_BANK)

    # Scan forward from start index, wrapping around once
    for offset in range(n):
        idx = (start + offset) % n
        topic = TOPIC_BANK[idx]
        if topic["title"] not in published_titles:
            return topic, idx

    # All topics have been published — no unused topic left
    return None


# ─────────────────────────────────────────────
#  Core posting job
# ─────────────────────────────────────────────
def run_posting_job() -> None:
    logger.info("=" * 60)
    try:
        tz = ZoneInfo(TIMEZONE)
    except Exception:
        import datetime as _dt
        tz = _dt.timezone(_dt.timedelta(hours=8))
    now_local = datetime.now(tz)
    logger.info("Starting daily posting job - %s (%s)",
                now_local.strftime("%Y-%m-%d %H:%M"), TIMEZONE)

    history = load_history()
    posts_today = 0

    # Build the complete set of Pexels IDs used across all published articles
    # This is passed to publish_article() to prevent image reuse
    extra_pexels_ids = load_all_used_pexels_ids(history.get("published", []))
    logger.info("Loaded %d previously used Pexels photo IDs from history", len(extra_pexels_ids))

    for _ in range(POSTS_PER_DAY):
        next_topic = get_next_topic(history)

        if next_topic is None:
            logger.warning(
                "⚠️  All %d topics have been published — no new topic available. "
                "Add more topics to topics.py or clear history.json to re-post.",
                len(TOPIC_BANK),
            )
            break

        topic, idx = next_topic
        logger.info("Topic #%d: %s [%s]", idx, topic["title"], topic["category"])

        try:
            logger.info("Generating article...")
            article = generate_article(topic)
            word_count = len(article["content"].split())
            logger.info("Article generated — approx. %d words", word_count)

            logger.info("Publishing to WordPress...")
            pub_result = publish_article(article, extra_used_pexels_ids=extra_pexels_ids)

            if pub_result["success"]:
                record = {
                    "topic_index": idx,
                    "title":       pub_result["title"],
                    "url":         pub_result["url"],
                    "post_id":     pub_result["post_id"],
                    "category":    pub_result["category"],
                    "date":        pub_result["published_at"],
                }
                # Record Pexels IDs used in this article for future dedup
                if pub_result.get("pexels_ids"):
                    record["pexels_ids"] = pub_result["pexels_ids"]
                    extra_pexels_ids.update(pub_result["pexels_ids"])

                history["published"].append(record)
                history["next_topic_index"] = (idx + 1) % len(TOPIC_BANK)
                posts_today += 1
                logger.info("✅ Success: %s → %s", pub_result["title"], pub_result["url"])
                # Save immediately after each successful publish to prevent data loss
                save_history(history)
            else:
                logger.error("❌ Failed: %s — %s", pub_result["title"], pub_result.get("error_detail", ""))

        except Exception as exc:
            logger.exception("Unexpected error processing topic %d: %s", idx, exc)

    logger.info("Job complete - %d/%d post(s) published today.", posts_today, POSTS_PER_DAY)
    logger.info("Progress: %d/%d topics published", len(history.get("published", [])), len(TOPIC_BANK))
    logger.info("=" * 60)


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
        try:
            tz = ZoneInfo(TIMEZONE)
        except Exception:
            import datetime as _dt
            tz = _dt.timezone(_dt.timedelta(hours=8))
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
        logger.info("Scheduler started - next run at %s (local) / %s (%s)",
                    local_time, POST_TIME, TIMEZONE)
        while True:
            schedule.run_pending()
            time.sleep(30)

    else:
        # Default: run once immediately
        run_posting_job()


if __name__ == "__main__":
    main()
