# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mastodon Monitor** is a GitHub Actions-based automation that monitors multiple Mastodon RSS feeds and sends Telegram notifications when new posts are detected. The monitoring runs every 30 minutes via a scheduled workflow and automatically persists state via git commits.

### Key Components
- **main.py**: Single-file Python application that monitors multiple Mastodon profiles/hashtags, detects new posts, and sends Telegram messages
- **.github/workflows/monitor.yml**: GitHub Actions workflow that runs every 30 minutes (configurable schedule) and auto-commits state
- **seen_posts.json**: Persistent state file tracking which posts have been seen (auto-generated and auto-committed)

## Development Commands

### Local Setup
```bash
# Install dependencies
pip install feedparser requests schedule

# Set environment variables for local testing
export TELEGRAM_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Run the monitor (single check)
python main.py
```

### Testing
The script runs a single feed check and exits. To test locally:
1. Set `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
2. Run `python main.py`
3. Check console output for ✅/❌ messages
4. Verify Telegram received the notification (if new posts exist)

To test without sending real Telegram messages, temporarily comment out the `send_telegram_message()` call in the `check_mastodon()` function.

## Architecture & Data Flow

### Single Responsibility
The application follows a simple linear flow:
1. **Load State** (`load_seen_posts()`) — Read `seen_posts.json` with IDs of previously seen posts per feed
2. **Cleanup** (`cleanup_old_posts()`) — Keep only the last 500 posts per feed to limit file growth
3. **Fetch Feeds** (`check_mastodon()`) — Parse multiple Mastodon RSS feeds via feedparser
4. **Detect Deltas** — Compare post links against `seen_posts` list for each feed
5. **Notify** — Send new post links to Telegram for each unseen post
6. **Persist State** (`save_seen_posts()`) — Update `seen_posts.json` with new post IDs

### Configuration
- **Multiple Feeds**: Configured in `main.py` lines 8–30 as a list of dictionaries with `url` and `handle`
  - @jef@norden.social
  - @underdarkGIS@fosstodon.org
  - #qgis (hashtag feed)
  - @qgis@fosstodon.org (QGIS official account)
  - #qgisuc2026 (QGIS User Conference 2026)
- **Telegram Credentials**: Environment-based (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`)
- **Check Interval**: Controlled by cron schedule in `.github/workflows/monitor.yml` line 5 (default: every 12 hours)
- **State Persistence**: Automatic via GitHub Actions workflow that commits `seen_posts.json` after each run

## GitHub Actions Automation

The workflow (`.github/workflows/monitor.yml`):
- **Trigger**: `schedule` (every 30 minutes) + manual dispatch (`workflow_dispatch`)
- **Python**: 3.11 + pip-installed dependencies (feedparser, requests, schedule)
- **Secrets Used**: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (configure in repo Settings → Secrets and variables → Actions)

The job:
1. Checks out the repo
2. Sets up Python 3.11 and installs dependencies
3. Runs `python main.py` (monitors all feeds in `MASTODON_FEEDS`)
4. Automatically commits and pushes updated `seen_posts.json` using `GITHUB_TOKEN`

### State Persistence (Resolved)
✅ **State is now automatically persisted!**
- After each run, the workflow commits `seen_posts.json` via git
- Uses `${{ github.token }}` for authentication (no manual token needed)
- File is kept small (~6-10 KB) via automatic cleanup of posts older than 500 per feed
- No need to manually manage state; it just works across workflow runs

## Common Tasks

### Adding a New Mastodon Feed
1. Edit `main.py` and add a new entry to the `MASTODON_FEEDS` list:
   ```python
   {
       "url": "https://instance.social/@username.rss",
       "handle": "@username@instance.social"
   }
   ```
2. For hashtags, use:
   ```python
   {
       "url": "https://instance.social/tags/hashtag.rss",
       "handle": "#hashtag"
   }
   ```
3. Commit and push (workflow auto-commits state, so new feeds integrate seamlessly)

**Note**: No need to reset `seen_posts.json`—new feeds are auto-initialized with empty lists

### Adjusting Check Frequency
Edit the cron schedule in `.github/workflows/monitor.yml` line 5:
- `0 */12 * * *` = every 12 hours (current)
- `*/30 * * * *` = every 30 minutes
- `*/15 * * * *` = every 15 minutes
- `0 * * * *` = hourly

### Debugging Failed Runs
1. Go to GitHub repo → Actions → Mastodon Monitor workflow
2. Click the failed run → scroll to "Run monitor" step
3. Check console output for error messages (network issues, missing secrets, etc.)

### Testing a Workflow Run Manually
In GitHub UI: Actions → Mastodon Monitor → "Run workflow" button (uses `workflow_dispatch` trigger).

## File Management

### seen_posts.json Growth Control
The `cleanup_old_posts()` function automatically manages file size:
- Keeps max 500 posts per feed
- Runs on every check (no separate cleanup needed)
- Prevents unbounded file growth while maintaining reliable tracking
- With 5 feeds: ~2,500 posts max (~6-10 KB file size)

This means you can run the monitor indefinitely without worrying about file bloat.

## Dependencies

- **feedparser**: Parse RSS/Atom feeds
- **requests**: HTTP client for Telegram API calls
- **schedule**: Task scheduling (currently unused in favor of GitHub Actions; kept for potential future local scheduling)

Install all with: `pip install feedparser requests schedule`
