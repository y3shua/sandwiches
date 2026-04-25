# Turkey & Provolone Facebook Bot

A quirky Facebook bot that posts turkey and provolone sandwich captions with optional AI-generated images.

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

3. Optionally configure one or more image providers:

```bash
export OPENAI_API_KEY="your_openai_key"
export STABILITY_API_KEY="your_stability_key"
export REPLICATE_API_TOKEN="your_replicate_token"
```

## Usage

Single post, suitable for GitHub Actions:

```bash
python sandwiches.py
```

## Features

- Posts one sandwich caption per run
- Generates brainrot/Gen Alpha style captions
- Generates optional sandwich images with OpenAI, Stability AI, or Replicate
- Saves failed posts for retry/review
- Uses bounded downloads, request timeouts, safer logging, and local JSON validation

## Dependencies

- requests - Facebook and image provider API calls
