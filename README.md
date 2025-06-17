# Turkey & Provolone Facebook Bot 🦃🧀

A quirky Facebook bot that posts random turkey and provolone sandwich content and tracks community sandwich shop recommendations.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FACEBOOK_ACCESS_TOKEN="your_token"
export FACEBOOK_PAGE_ID="your_page_id"
```

## Usage

Single post (perfect for GitHub Actions):
```bash
python main.py
```

Scheduled mode (local testing):
```bash
RUN_MODE=scheduled python main.py
```

## Features

- Posts random sandwich content every 6 hours
- Monitors comments for shop recommendations (5+ likes = auto-featured)
- Generates daily reports of tracked sandwich shops
- Saves failed posts for retry

## Dependencies

- requests - Facebook API calls
- schedule - Post scheduling