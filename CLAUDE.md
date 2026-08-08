# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mastodon Monitor** is a GitHub Actions-based automation that monitors a Mastodon RSS feed and sends Telegram notifications when new posts are detected. The monitoring runs every 30 minutes via a scheduled workflow.

### Key Components
- **main.py**: Single-file Python application that fetches the Mastodon feed, detects new posts, and sends Telegram messages
- **.github/workflows/monitor.yml**: GitHub Actions workflow that runs every 30 minutes (configurable schedule)
- **seen_posts.json**: Persistent state file (auto-generated) tracking which posts have been seen

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
1. **Load State** (`load_seen_posts()`) — Read `seen_posts.json` with IDs of previously seen posts
2. **Fetch Feed** (`check_mastodon()`) — Parse Mastodon RSS feed via feedparser
3. **Detect Deltas** — Compare post links against `seen_posts` list
4. **Notify** — Send new post links to Telegram for each unseen post
5. **Persist State** (`save_seen_posts()`) — Update `seen_posts.json` with new post IDs

### Configuration
The feed URL and Telegram credentials are environment-based (see `main.py` lines 8–10). The check interval (30 minutes) is controlled by the cron schedule in `.github/workflows/monitor.yml` line 5.

## GitHub Actions Automation

The workflow (`.github/workflows/monitor.yml`):
- **Trigger**: `schedule` (every 30 minutes) + manual dispatch (`workflow_dispatch`)
- **Python**: 3.11 + pip-installed dependencies (feedparser, requests, schedule)
- **Secrets Used**: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (configure in repo Settings → Secrets and variables → Actions)

The job checks out the repo, sets up Python 3.11, installs dependencies, and runs `python main.py` once. GitHub Actions automatically persists the `seen_posts.json` file across runs (via git checkout/commit mechanisms or artifact handling, depending on workflow design—currently this relies on the state file being committed to the repo or managed externally).

### Important Note on State Persistence
Currently, `seen_posts.json` must be committed to the repo for state to persist between workflow runs. If it's not committed, every run will treat all posts as "new." Consider:
- Committing `seen_posts.json` to version control (simple, but pollutes commit history)
- Using GitHub Actions artifacts to preserve state
- Using an external database/API for persistence

## Common Tasks

### Adding a New Mastodon Feed
1. Change `MASTODON_FEED` URL in `main.py` line 8
2. Delete or reset `seen_posts.json` to avoid old posts triggering notifications

### Adjusting Check Frequency
Edit the cron schedule in `.github/workflows/monitor.yml` line 5:
- `*/30 * * * *` = every 30 minutes (current)
- `*/15 * * * *` = every 15 minutes
- `0 * * * *` = hourly

### Debugging Failed Runs
1. Go to GitHub repo → Actions → Mastodon Monitor workflow
2. Click the failed run → scroll to "Run monitor" step
3. Check console output for error messages (network issues, missing secrets, etc.)

### Testing a Workflow Run Manually
In GitHub UI: Actions → Mastodon Monitor → "Run workflow" button (uses `workflow_dispatch` trigger).

## Dependencies

- **feedparser**: Parse RSS/Atom feeds
- **requests**: HTTP client for Telegram API calls
- **schedule**: Task scheduling (currently unused in favor of GitHub Actions; kept for potential future local scheduling)

Install all with: `pip install feedparser requests schedule`
