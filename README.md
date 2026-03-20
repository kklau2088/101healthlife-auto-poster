# 101healthlife.com Daily SEO Auto-Poster

## System Overview

A complete, production-ready automation system that **generates and publishes one SEO-optimised article per day** to [101healthlife.com](https://101healthlife.com) via the WordPress REST API, powered by OpenAI GPT-4o.

---

## File Structure

```
101healthlife-auto-poster/
├── config.py               ← ⚙️  Your credentials & settings (edit this first)
├── topics.py               ← 📋  50+ pre-planned SEO article topics
├── article_generator.py    ← 🤖  OpenAI GPT-4o article writer
├── wp_publisher.py         ← 🚀  WordPress REST API publisher
├── main.py                 ← ▶️  Main scheduler & CLI entry point
├── requirements.txt        ← 📦  Python dependencies
└── README.md               ← 📖  This file
```

---

## Step-by-Step Setup Guide

### Step 1 — Get Your WordPress Application Password

WordPress Application Passwords allow secure API access **without** sharing your main login password.

1. Log in to your WordPress admin panel: `https://101healthlife.com/wp-admin/`
2. Go to **Users → Profile** (top-right of screen)
3. Scroll down to the **"Application Passwords"** section
4. In the "New Application Password Name" field, type: `Auto SEO Poster`
5. Click **"Add New Application Password"**
6. WordPress will show you a password like: `AbCd EfGh IjKl MnOp QrSt UvWx`
7. **Copy this password immediately** — it will only be shown once!

> **Security note:** Application Passwords can be revoked at any time from the same page, without changing your main password.

---

### Step 2 — Get an OpenAI API Key

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign in or create a free account
3. Go to **API → API Keys → Create new secret key**
4. Copy the key (starts with `sk-`)

> **Cost estimate:** GPT-4o generates one article (~1,500 words) for approximately **$0.03–0.06 USD**. Running daily = ~$1–2/month.

---

### Step 3 — Configure `config.py`

Open `config.py` and fill in your details:

```python
WORDPRESS_SITE_URL    = "https://101healthlife.com"
WORDPRESS_USERNAME    = "admin"           # Your WP username
WORDPRESS_APP_PASSWORD = "AbCd EfGh IjKl MnOp QrSt UvWx"  # From Step 1
OPENAI_API_KEY         = "sk-xxxxxxxxxx"  # From Step 2
```

Optional settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `POSTS_PER_DAY` | `1` | How many articles to publish per day |
| `POST_TIME` | `"08:00"` | Time to post (24-hour, server local time) |
| `ARTICLE_MIN_WORDS` | `1200` | Minimum article length |
| `ARTICLE_MAX_WORDS` | `2000` | Maximum article length |
| `TARGET_REGION` | `"global"` | Change to `"UK"`, `"US"`, `"AU"` etc. |

---

### Step 4 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Test Your Connection

Before running the scheduler, verify your WordPress credentials work:

```bash
python3 main.py --test-connection
```

Expected output:
```
✅ Connected as: Admin (admin)
```

If you see an error, double-check your `WORDPRESS_USERNAME` and `WORDPRESS_APP_PASSWORD` in `config.py`.

---

### Step 6 — Run a Test Post (Recommended)

Publish one article immediately to confirm the full pipeline works:

```bash
python3 main.py --now
```

Then check your WordPress site — a new published article should appear within ~30 seconds.

> **Tip:** To publish as a **draft** instead of going live immediately, open `wp_publisher.py` and change `"status": "publish"` to `"status": "draft"`.

---

## Running the Scheduler

### Option A: Cron Job (Recommended for servers/VPS)

Add this line to your crontab (`crontab -e`):

```cron
0 8 * * * /usr/bin/python3 /path/to/101healthlife-auto-poster/main.py >> /path/to/poster.log 2>&1
```

This runs the script every day at **08:00 AM** server time.

### Option B: Daemon Mode (Recommended for always-on computers)

```bash
python3 main.py --daemon
```

This keeps the script running in the background and posts at the time set in `POST_TIME`.

To run it persistently (even after rebooting):

```bash
# Using nohup
nohup python3 main.py --daemon > poster.log 2>&1 &

# Or using screen
screen -S auto-poster
python3 main.py --daemon
# Press Ctrl+A then D to detach
```

---

## How the System Works

```
Every day at POST_TIME
        │
        ▼
  Pick next topic from topics.py  (cycles through 50+ topics)
        │
        ▼
  GPT-4o generates full SEO article
  - Proper H1/H2/H3 structure
  - Focus keyword integrated naturally
  - FAQ section for featured snippets
  - 1,200–2,000 words
        │
        ▼
  Publish to WordPress REST API
  - Correct category assigned
  - Tags created automatically
  - Yoast SEO meta fields set
        │
        ▼
  Log result to poster.log + history.json
```

---

## Monitoring & Logs

Two files track all activity:

| File | Purpose |
|------|---------|
| `poster.log` | Full activity log with timestamps |
| `history.json` | Published article history (title, URL, date) |

View recent activity:
```bash
tail -50 poster.log
```

View published article history:
```bash
python3 -c "import json; h = json.load(open('history.json')); [print(p['date'][:10], p['title'], p['url']) for p in h['published']]"
```

---

## Article Topics Included

The system comes with **50+ pre-planned SEO topics** across all site categories:

| Category | Topics Included |
|----------|----------------|
| Diet | 7 topics (Mediterranean, intermittent fasting, gut health, budget eating…) |
| Weight Loss | 7 topics (calorie deficit, plateau, Ozempic, sleep & weight…) |
| Nutrition | 7 topics (vitamins, protein, sugar, omega-3, magnesium, vitamin D…) |
| Mental Health | 6 topics (anxiety, depression, mindfulness, gut-brain axis…) |
| Health | 9 topics (immune system, blood pressure, diabetes, heart, sleep, inflammation…) |
| Health Insurance | 4 topics (plan selection, HMO vs PPO, self-employed…) |
| Smoking | 4 topics (quit methods, body timeline, vaping vs smoking…) |
| AI in Health | 3 topics (AI in healthcare, fitness apps, nutrition assistants) |
| Care | 3 topics (preventive care, elder care, chronic disease management) |

After cycling through all topics, the system starts again — you can add more topics to `topics.py` at any time.

---

## Adding Custom Topics

Open `topics.py` and add entries to the `TOPIC_BANK` list:

```python
{"title":         "Your Article Title Here",
 "category":      "Health",    # Must match a key in CATEGORY_IDS in config.py
 "focus_keyword": "your seo keyword",
 "meta_desc":     "Your meta description under 160 characters."},
```

---

## Frequently Asked Questions

**Q: Will this affect my site's SEO negatively?**
No — the articles are human-quality, fully structured, keyword-optimised pieces. Publishing fresh content regularly is one of the most effective SEO strategies.

**Q: What if OpenAI is temporarily unavailable?**
The error is caught and logged. The failed topic index is NOT incremented, so the same topic will be retried on the next run.

**Q: Can I pause posting for a few days?**
Yes — simply stop the cron job or daemon. The `history.json` remembers where you left off.

**Q: Can I use a different AI model to save cost?**
Yes — in `article_generator.py`, change `model="gpt-4o"` to `model="gpt-4o-mini"` for ~10x lower cost with slightly reduced quality.

---

## Support

For help, refer to:
- [WordPress REST API documentation](https://developer.wordpress.org/rest-api/)
- [OpenAI API documentation](https://platform.openai.com/docs)
- [WordPress Application Passwords guide](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)
