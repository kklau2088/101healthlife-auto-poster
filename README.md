# 101healthlife.com Daily SEO Auto-Poster

## System Overview

A complete, production-ready automation system that **generates and publishes one SEO-optimised article per day** to [101healthlife.com](https://101healthlife.com) via the WordPress REST API, powered by a free AI API (chatanywhere — works in Hong Kong & mainland China).

---

## File Structure

```
101healthlife-auto-poster/
├── config.py               ← Your credentials & settings (edit this first)
├── topics.py               ← 50+ pre-planned SEO article topics
├── article_generator.py    ← AI article writer
├── wp_publisher.py         ← WordPress REST API publisher (Rank Math SEO support)
├── main.py                 ← Main scheduler & CLI entry point
├── requirements.txt        ← Python dependencies
├── install_windows.bat     ← Windows one-click installer
├── run_now.bat             ← Publish one article immediately
├── setup_scheduler.bat     ← Windows Task Scheduler setup
└── README.md               ← This file
```

---

## Step-by-Step Setup Guide

### Step 1 — Get Your WordPress Application Password

WordPress Application Passwords allow secure API access **without** sharing your main login password.

1. Log in to your WordPress admin panel: `https://101healthlife.com/wp-admin/`
2. Go to **Users → Profile**
3. Scroll down to the **"Application Passwords"** section
4. In the "New Application Password Name" field, type: `Auto SEO Poster`
5. Click **"Add New Application Password"**
6. WordPress will show you a password like: `AbCd EfGh IjKl MnOp QrSt UvWx`
7. **Copy this password immediately** — it will only be shown once

> **Security note:** Application Passwords can be revoked at any time from the same page, without changing your main password.

---

### Step 2 — Get a Free AI API Key

This system uses [chatanywhere](https://github.com/chatanywhere/GPT_API_free) — a free OpenAI-compatible API that works in Hong Kong and mainland China with no credit card required.

1. Visit [github.com/chatanywhere/GPT_API_free](https://github.com/chatanywhere/GPT_API_free)
2. Click the link to apply for a free API key (requires GitHub account)
3. Copy your key (starts with `sk-`)

> **Free tier:** 200 requests/day for GPT series — more than enough for 1 article/day.

---

### Step 3 — Configure `config.py`

Open `config.py` with Notepad and fill in your details:

```python
WORDPRESS_USERNAME     = "admin"                              # Your WP username
WORDPRESS_APP_PASSWORD = "AbCd EfGh IjKl MnOp QrSt UvWx"   # From Step 1
API_KEY                = "sk-xxxxxxxxxx"                      # From Step 2
```

Optional settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `API_MODEL` | `"gpt-4o-mini"` | AI model to use |
| `POSTS_PER_DAY` | `1` | How many articles to publish per day |
| `POST_TIME` | `"08:00"` | Time to post (UTC+8 Hong Kong time) |
| `ARTICLE_MIN_WORDS` | `1200` | Minimum article length |
| `ARTICLE_MAX_WORDS` | `2000` | Maximum article length |

---

### Step 4 — Install Python Dependencies

```powershell
pip install -r requirements.txt
```

---

### Step 5 — Test Your Connection

```powershell
python main.py --test-connection
```

Expected output:
```
Connected as: Admin (admin)
```

---

### Step 6 — Run a Test Post

```powershell
python main.py --now
```

Check your WordPress site — a new published article should appear within ~60 seconds.

> **Tip:** To review before publishing, open `wp_publisher.py` and change `"status": "publish"` to `"status": "draft"`.

---

## Scheduling — Windows Task Scheduler (PowerShell)

Set up the system to post automatically every day at 08:00 using Windows Task Scheduler.

### Option A — One-Click Setup Script (Recommended)

A ready-made PowerShell script is included: **`setup_scheduler.ps1`**

1. Right-click `setup_scheduler.ps1`
2. Select **"Run with PowerShell"** (or open PowerShell as Administrator and run it)
3. The script automatically detects your Python path and working directory — no manual editing needed

The script will output:
```
============================================
  101HealthLife Auto Poster — Scheduler Setup
============================================
Python path : C:\Users\...\python.exe
Script path : C:\...\main.py
Working dir : C:\...\101healthlife-auto-poster-main
Post time   : 08:00AM (daily)

============================================
  Scheduler set up successfully!
============================================
  Task name  : 101HealthLife Auto Post
  Status     : Ready
  Next run   : 08:00:00 tomorrow
```

---

### Option B — Manual PowerShell Setup

**Step 1 — Open PowerShell as Administrator**

Press `Windows key` → Search `PowerShell` → Right-click → **Run as Administrator**

**Step 2 — Run the following command**

> The script auto-detects your Python path. Replace only the `$scriptPath` if your folder is in a different location.

```powershell
$taskName   = "101HealthLife Auto Post"
$scriptPath = "C:\Users\Administrator\Downloads\101healthlife-auto-poster-main\main.py"
$pythonPath = (where.exe python | Select-Object -First 1).Trim()
$workDir    = Split-Path $scriptPath

$action   = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory $workDir
$trigger  = New-ScheduledTaskTrigger -Daily -At "08:00AM"
$settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
                -RestartCount 3 `
                -RestartInterval (New-TimeSpan -Minutes 5) `
                -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
Write-Host "Done. Python: $pythonPath"
```

> **`-StartWhenAvailable`** — if the computer is off at 08:00, the task will run automatically as soon as it powers on.

**Step 3 — Verify**

```powershell
Get-ScheduledTaskInfo -TaskName "101HealthLife Auto Post" | Select LastRunTime, LastTaskResult, NextRunTime
```

`LastTaskResult: 0` = success ✅

---

### Troubleshooting — LastTaskResult Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `0` | Success | — |
| `2147942402` | File not found | Python or script path is wrong — re-run `setup_scheduler.ps1` |
| `2147942405` | Access denied | Run PowerShell as Administrator |
| `1` | General error | Check `poster.log` for details |

**If you get `2147942402`**, delete and recreate the task:
```powershell
Unregister-ScheduledTask -TaskName "101HealthLife Auto Post" -Confirm:$false
# Then re-run setup_scheduler.ps1
```

---

### Managing the Scheduled Task

**Run immediately (manual trigger):**
```powershell
Start-ScheduledTask -TaskName "101HealthLife Auto Post"
```

**Check last run time and status:**
```powershell
Get-ScheduledTaskInfo -TaskName "101HealthLife Auto Post" | Select LastRunTime, LastTaskResult, NextRunTime
```

**Change posting time (e.g. to 9:00 AM):**
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"
Set-ScheduledTask -TaskName "101HealthLife Auto Post" -Trigger $trigger
```

**Temporarily disable (pause posting):**
```powershell
Disable-ScheduledTask -TaskName "101HealthLife Auto Post"
```

**Re-enable after pausing:**
```powershell
Enable-ScheduledTask -TaskName "101HealthLife Auto Post"
```

**Delete the task permanently:**
```powershell
Unregister-ScheduledTask -TaskName "101HealthLife Auto Post" -Confirm:$false
```

> **Note:** The computer must be powered on at the scheduled time for the task to run. If the computer is off, that day's article will be skipped, but the next day will run normally.

---

## Scheduling — Linux / VPS (Cron)

If running on a Linux server or VPS, use cron instead:

```bash
# Open crontab editor
crontab -e

# Add this line to post every day at 08:00 HKT (UTC+8)
0 0 * * * TZ=Asia/Hong_Kong /usr/bin/python3 /path/to/main.py >> /path/to/poster.log 2>&1
```

---

## How the System Works

```
Every day at 08:00 (HKT)
        |
        v
  Pick next topic from topics.py  (cycles through 50+ topics)
        |
        v
  AI generates full SEO article
  - Proper H1 / H2 / H3 structure
  - Focus keyword integrated naturally
  - FAQ section for featured snippets
  - 1,200 to 2,000 words
        |
        v
  Publish to WordPress REST API
  - Correct category assigned
  - Tags created automatically
  - Rank Math SEO fields auto-filled
  - Focus Keyword set automatically
        |
        v
  Log result to poster.log + history.json
```

---

## Monitoring & Logs

| File | Purpose |
|------|---------|
| `poster.log` | Full activity log with timestamps |
| `history.json` | Published article history (title, URL, date) |

**View recent logs (PowerShell):**
```powershell
Get-Content poster.log -Tail 50
```

**View published article history (PowerShell):**
```powershell
python -c "import json; h = json.load(open('history.json')); [print(p['date'][:10], p['title']) for p in h['published']]"
```

---

## Article Topics Included

The system includes **50 pre-planned SEO topics** across all site categories:

| Category | Topics |
|----------|--------|
| Diet | 7 topics (Mediterranean, intermittent fasting, gut health, budget eating…) |
| Weight Loss | 7 topics (calorie deficit, plateau, Ozempic, sleep & weight…) |
| Nutrition | 7 topics (vitamins, protein, sugar, omega-3, magnesium, vitamin D…) |
| Mental Health | 6 topics (anxiety, depression, mindfulness, gut-brain axis…) |
| Health | 9 topics (immune system, blood pressure, diabetes, heart, sleep, inflammation…) |
| Health Insurance | 4 topics (plan selection, HMO vs PPO, self-employed…) |
| Smoking | 4 topics (quit methods, body timeline, vaping vs smoking…) |
| AI in Health | 3 topics (AI in healthcare, fitness apps, nutrition assistants) |
| Care | 3 topics (preventive care, elder care, chronic disease management) |

After cycling through all topics, the system restarts from the beginning. Add more topics to `topics.py` at any time.

---

## Adding Custom Topics

Open `topics.py` and add a new entry to the `TOPIC_BANK` list:

```python
{"title":         "Your Article Title Here",
 "category":      "Health",
 "focus_keyword": "your seo keyword",
 "meta_desc":     "Your meta description — keep it under 160 characters."},
```

---

## Frequently Asked Questions

**Q: Does publishing AI articles hurt SEO?**
No — articles are fully structured, properly formatted, and keyword-optimised. Regular fresh content is one of the most effective SEO strategies.

**Q: What if the API fails one day?**
The error is caught and logged. The failed topic index is not incremented, so the same topic will be retried the next day.

**Q: Can I pause posting for a few days?**
Yes — run `Disable-ScheduledTask -TaskName "101HealthLife Auto Post"` to pause, and `Enable-ScheduledTask` to resume.

**Q: Can I publish more than one article per day?**
Yes — change `POSTS_PER_DAY = 1` to `POSTS_PER_DAY = 3` in `config.py`.

---

## Support & References

- [WordPress REST API documentation](https://developer.wordpress.org/rest-api/)
- [WordPress Application Passwords guide](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)
- [chatanywhere free API](https://github.com/chatanywhere/GPT_API_free)
- [Rank Math SEO plugin](https://rankmath.com/)
