#!/usr/bin/env python3
"""Turkey and provolone Facebook bot with AI-generated sandwich images."""

from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"
SAVED_POST_DIR = BASE_DIR / "saved_posts"
GENERATED_IMAGE_DIR = BASE_DIR / "generated_images"
SHOP_FILE = BASE_DIR / "sandwich_shops.json"

DEFAULT_TIMEOUT = (10, 60)
POLL_TIMEOUT = (10, 30)
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_CUSTOM_MESSAGE_LENGTH = 2_000
FACEBOOK_API_VERSION = "v18.0"

for directory in (LOG_DIR, REPORT_DIR, SAVED_POST_DIR, GENERATED_IMAGE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class TurkeyProvoloneBot:
    """Create sandwich captions, generate images, and publish to Facebook."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

        self.facebook_access_token = self._get_env("FACEBOOK_ACCESS_TOKEN")
        self.facebook_page_id = self._get_env("FACEBOOK_PAGE_ID")
        self.facebook_ready = False

        self.openai_api_key = self._get_env("OPENAI_API_KEY")
        self.stability_api_key = self._get_env("STABILITY_API_KEY")
        self.replicate_api_token = self._get_env("REPLICATE_API_TOKEN")
        self.openai_image_model = self._get_env("OPENAI_IMAGE_MODEL") or "dall-e-3"

        self.image_prompts = [
            "A perfectly crafted turkey and provolone sandwich on fresh sourdough bread, professional food photography, appetizing lighting, restaurant quality",
            "Close-up of a gourmet turkey and provolone sandwich with crisp lettuce and tomato, artisanal bread, food photography style",
            "A delicious turkey and provolone panini with golden crispy bread, melted cheese visible, professional food styling",
            "Fresh turkey and provolone sandwich on ciabatta bread with avocado, natural lighting, food magazine quality photo",
            "A mouth-watering turkey and provolone club sandwich with multiple layers, professional food photography",
            "Grilled turkey and provolone sandwich cut in half showing the layers, steam rising, warm lighting",
            "Turkey and provolone sandwich on a rustic wooden board with herbs, artisanal presentation, food blog style",
            "A hearty turkey and provolone sandwich on whole grain bread, fresh vegetables, clean food photography",
            "Gourmet turkey and provolone sandwich with herb aioli, professional kitchen background, chef's presentation",
            "A classic turkey and provolone sandwich on fresh white bread, simple and appetizing, deli-style photography",
        ]

        self.style_additions = [
            ", 4K high resolution, professional food photography",
            ", warm natural lighting, shallow depth of field",
            ", commercial food photography, appetizing presentation",
            ", rustic wooden background, artisanal style",
            ", clean white background, minimalist food photography",
            ", cozy cafe atmosphere, warm lighting",
            ", vintage food photography style, film grain",
            ", modern food styling, geometric plating",
        ]

        self.caption_templates = [
            "Chat, this turkey and provolone on {bread} is actually elite. {condiment} pullin up with S-tier aura. #NoCap #SandwichTok",
            "Lowkey this {bread} turkey-provolone stack got main character energy. Add {addon} and suddenly it's a certified W.",
            "POV: the {condiment} hit, the provolone melted, and the turkey sandwich started acting famous. Big lunch aura.",
            "This turkey and provolone with {addon} is bussin respectfully. Zero crumbs, maximum rizz.",
            "Not to glaze, but this {bread} situation is giving legendary. Turkey, provolone, {condiment}. Say less.",
            "The lunch meta just shifted: turkey, provolone, {addon}, {condiment}. This build is cracked.",
            "Be so for real, this turkey-provolone combo clears. {bread} plus {addon} equals instant aura farming.",
            "Skibidi sandwich check: turkey stacked, provolone locked in, {condiment} carrying the squad.",
            "This is not a regular sandwich, this is a side quest reward. {bread}, turkey, provolone, {addon}. W eats.",
            "Turkey and provolone woke up and chose rizz. {condiment} on {bread} is the final boss of lunch.",
        ]

        self.image_style_prompts = {
            "grilled_panini": "A perfectly grilled turkey and provolone panini sandwich, golden crispy bread with grill marks, melted cheese oozing out",
            "gourmet_close_up": "Extreme close-up of a gourmet turkey and provolone sandwich, focusing on the layers and textures",
            "classic_deli": "A classic deli-style turkey and provolone sandwich on fresh bread, traditional presentation",
            "gourmet_weekend": "Fresh turkey and provolone sandwich on ciabatta bread with avocado and olive oil, natural light",
            "classic_full": "A turkey and provolone sandwich with lettuce and tomato, neatly cut and plated",
        }

        self.sandwich_shops = [
            {
                "name": "Tony's Deli",
                "location": "Downtown",
                "specialty": "Classic turkey and provolone on fresh Italian bread",
                "added_by": "admin",
                "date_added": "2025-01-01",
                "status": "verified",
            },
            {
                "name": "Corner Bistro",
                "location": "Main Street",
                "specialty": "Gourmet turkey with aged provolone and herb aioli",
                "added_by": "admin",
                "date_added": "2025-01-01",
                "status": "verified",
            },
        ]

        self.bread_types = [
            "sourdough",
            "ciabatta",
            "whole wheat",
            "rye",
            "focaccia",
            "kaiser roll",
            "everything bagel",
            "french bread",
            "pumpernickel",
        ]

        self.add_ons = [
            "crisp lettuce",
            "ripe tomatoes",
            "red onion",
            "pickles",
            "avocado",
            "sprouts",
            "roasted red peppers",
            "cucumber",
        ]

        self.condiments = [
            "mayo",
            "mustard",
            "pesto",
            "olive oil",
            "balsamic glaze",
            "herb aioli",
            "honey mustard",
            "chipotle mayo",
        ]

        self.setup_facebook()
        self.load_sandwich_shops()

    @staticmethod
    def _get_env(name: str) -> str | None:
        value = os.getenv(name)
        return value.strip() if value and value.strip() else None

    @staticmethod
    def _clean_message(value: Any, limit: int = MAX_CUSTOM_MESSAGE_LENGTH) -> str:
        text = str(value or "").strip()
        text = "".join(char for char in text if char.isprintable() or char in "\n\t")
        if len(text) > limit:
            logger.warning("Custom message exceeded %s characters and was truncated", limit)
            text = text[:limit].rstrip()
        return text

    @staticmethod
    def _safe_json(response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _atomic_write_json(path: Path, payload: Any) -> None:
        temp_path = path.with_name(f"{path.name}.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")
        temp_path.replace(path)

    def _log_http_error(self, provider: str, response: requests.Response) -> None:
        data = self._safe_json(response)
        error = data.get("error") if isinstance(data.get("error"), dict) else {}
        message = error.get("message") or data.get("message") or response.reason
        trace_id = data.get("fbtrace_id")
        suffix = f" trace_id={trace_id}" if trace_id else ""
        logger.error("%s request failed: HTTP %s %s%s", provider, response.status_code, message, suffix)

    def setup_facebook(self) -> None:
        """Verify that Facebook credentials can access the configured page."""
        if not self.facebook_access_token or not self.facebook_page_id:
            logger.error("Facebook credentials not provided")
            return

        try:
            page_id = quote(self.facebook_page_id, safe="")
            response = self.session.get(
                f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/{page_id}",
                headers={"Authorization": f"Bearer {self.facebook_access_token}"},
                timeout=DEFAULT_TIMEOUT,
            )
            if response.ok:
                page_info = self._safe_json(response)
                logger.info("Connected to Facebook page: %s", page_info.get("name", "Unknown"))
                self.facebook_ready = True
            else:
                self._log_http_error("Facebook setup", response)
        except requests.RequestException as exc:
            logger.error("Error setting up Facebook API: %s", exc)

    def _decode_image(self, encoded_image: str | None, provider: str) -> bytes | None:
        if not encoded_image:
            logger.error("%s response did not include image data", provider)
            return None

        try:
            image_data = base64.b64decode(encoded_image, validate=True)
        except (ValueError, TypeError) as exc:
            logger.error("%s returned invalid base64 image data: %s", provider, exc)
            return None

        if not self._valid_image_size(image_data, provider):
            return None
        return image_data

    @staticmethod
    def _valid_image_size(image_data: bytes, provider: str) -> bool:
        size = len(image_data)
        if size == 0:
            logger.error("%s returned an empty image", provider)
            return False
        if size > MAX_IMAGE_BYTES:
            logger.error("%s image exceeded %s bytes", provider, MAX_IMAGE_BYTES)
            return False
        return True

    def generate_image_with_openai(self, prompt: str) -> bytes | None:
        """Generate an image using OpenAI Images API."""
        if not self.openai_api_key:
            return None

        try:
            response = self.session.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.openai_image_model,
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard",
                    "response_format": "b64_json",
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if not response.ok:
                self._log_http_error("OpenAI image generation", response)
                return None

            result = self._safe_json(response)
            data = result.get("data") if isinstance(result.get("data"), list) else []
            encoded_image = data[0].get("b64_json") if data and isinstance(data[0], dict) else None
            image_data = self._decode_image(encoded_image, "OpenAI")
            if image_data:
                logger.info("Generated image with OpenAI")
            return image_data
        except requests.RequestException as exc:
            logger.error("Error with OpenAI image generation: %s", exc)
            return None

    def generate_image_with_stability(self, prompt: str) -> bytes | None:
        """Generate an image using Stability AI."""
        if not self.stability_api_key:
            return None

        try:
            response = self.session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30,
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if not response.ok:
                self._log_http_error("Stability AI image generation", response)
                return None

            result = self._safe_json(response)
            artifacts = result.get("artifacts") if isinstance(result.get("artifacts"), list) else []
            encoded_image = artifacts[0].get("base64") if artifacts and isinstance(artifacts[0], dict) else None
            image_data = self._decode_image(encoded_image, "Stability AI")
            if image_data:
                logger.info("Generated image with Stability AI")
            return image_data
        except requests.RequestException as exc:
            logger.error("Error with Stability AI image generation: %s", exc)
            return None

    def generate_image_with_replicate(self, prompt: str) -> bytes | None:
        """Generate an image using Replicate API."""
        if not self.replicate_api_token:
            return None

        headers = {
            "Authorization": f"Token {self.replicate_api_token}",
            "Content-Type": "application/json",
        }

        try:
            response = self.session.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "input": {
                        "prompt": prompt,
                        "width": 1024,
                        "height": 1024,
                        "num_outputs": 1,
                        "guidance_scale": 7.5,
                        "num_inference_steps": 20,
                    },
                },
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code != 201:
                self._log_http_error("Replicate prediction create", response)
                return None

            prediction = self._safe_json(response)
            prediction_id = prediction.get("id")
            if not prediction_id:
                logger.error("Replicate response did not include a prediction id")
                return None

            for _ in range(30):
                time.sleep(10)
                status_response = self.session.get(
                    f"https://api.replicate.com/v1/predictions/{quote(str(prediction_id), safe='')}",
                    headers=headers,
                    timeout=POLL_TIMEOUT,
                )

                if not status_response.ok:
                    self._log_http_error("Replicate prediction status", status_response)
                    return None

                status_data = self._safe_json(status_response)
                status = status_data.get("status")
                if status == "succeeded":
                    output = status_data.get("output")
                    image_url = output[0] if isinstance(output, list) and output else None
                    return self._download_generated_image(image_url)
                if status in {"failed", "canceled"}:
                    logger.error("Replicate generation ended with status: %s", status)
                    return None

            logger.error("Replicate generation timed out")
            return None
        except requests.RequestException as exc:
            logger.error("Error with Replicate image generation: %s", exc)
            return None

    def _download_generated_image(self, image_url: Any) -> bytes | None:
        if not isinstance(image_url, str):
            logger.error("Replicate output did not include an image URL")
            return None

        parsed = urlparse(image_url)
        if parsed.scheme != "https" or not parsed.netloc:
            logger.error("Rejected Replicate image URL with invalid scheme or host")
            return None

        try:
            with self.session.get(image_url, timeout=DEFAULT_TIMEOUT, stream=True) as response:
                if not response.ok:
                    self._log_http_error("Replicate image download", response)
                    return None

                content_type = response.headers.get("Content-Type", "")
                if content_type and not content_type.lower().startswith("image/"):
                    logger.error("Rejected Replicate download with content type: %s", content_type)
                    return None

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_IMAGE_BYTES:
                    logger.error("Rejected Replicate image larger than %s bytes", MAX_IMAGE_BYTES)
                    return None

                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        logger.error("Replicate image download exceeded %s bytes", MAX_IMAGE_BYTES)
                        return None
                    chunks.append(chunk)

            image_data = b"".join(chunks)
            if self._valid_image_size(image_data, "Replicate"):
                logger.info("Generated image with Replicate")
                return image_data
        except (requests.RequestException, ValueError) as exc:
            logger.error("Error downloading Replicate image: %s", exc)
        return None

    def generate_sandwich_image(self, post_content: dict[str, Any] | None = None) -> Path | None:
        """Generate a sandwich image using the first configured provider that works."""
        image_style = post_content.get("image_style") if post_content else None
        base_prompt = self.image_style_prompts.get(str(image_style), random.choice(self.image_prompts))
        full_prompt = base_prompt + random.choice(self.style_additions)

        logger.info("Generating image with prompt: %s...", full_prompt[:100])

        image_data = None
        if self.openai_api_key:
            image_data = self.generate_image_with_openai(full_prompt)
        if not image_data and self.stability_api_key:
            image_data = self.generate_image_with_stability(full_prompt)
        if not image_data and self.replicate_api_token:
            image_data = self.generate_image_with_replicate(full_prompt)

        if not image_data:
            logger.warning("Failed to generate image with any configured service")
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = GENERATED_IMAGE_DIR / f"sandwich_{timestamp}_{random.randrange(1000):03d}.jpg"
        filename.write_bytes(image_data)
        logger.info("Saved generated image: %s", filename)
        return filename

    def format_caption(self, post_content: dict[str, Any]) -> str:
        custom_message = self._clean_message(os.getenv("CUSTOM_MESSAGE"))
        if custom_message:
            return custom_message
        return self._clean_message(post_content.get("text"))

    def post_to_facebook_with_image(self, post_content: dict[str, Any], image_path: Path | None = None) -> str | bool:
        """Post content to Facebook page with an optional image."""
        if not self.facebook_ready:
            logger.error("Facebook API not available")
            return False

        full_message = self.format_caption(post_content)
        if not full_message:
            logger.error("Refusing to post an empty Facebook message")
            return False

        try:
            page_id = quote(str(self.facebook_page_id), safe="")
            if image_path and image_path.is_file():
                post_url = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/{page_id}/photos"
                with image_path.open("rb") as image_file:
                    response = self.session.post(
                        post_url,
                        headers={"Authorization": f"Bearer {self.facebook_access_token}"},
                        data={"message": full_message},
                        files={"source": image_file},
                        timeout=DEFAULT_TIMEOUT,
                    )
            else:
                post_url = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/{page_id}/feed"
                response = self.session.post(
                    post_url,
                    headers={"Authorization": f"Bearer {self.facebook_access_token}"},
                    data={"message": full_message},
                    timeout=DEFAULT_TIMEOUT,
                )

            if response.ok:
                response_data = self._safe_json(response)
                post_id = response_data.get("post_id") or response_data.get("id")
                if not post_id:
                    logger.error("Facebook success response did not include a post id")
                    return False
                logger.info("Posted to Facebook: %s", post_id)
                logger.info("Content: %s...", full_message[:60])
                if image_path:
                    logger.info("With image: %s", image_path)
                self.log_activity(f"POST CREATED: {post_id} - {full_message[:50]}...")
                return str(post_id)

            self._log_http_error("Facebook post", response)
            return False
        except requests.RequestException as exc:
            logger.error("Error posting to Facebook: %s", exc)
            return False

    def create_and_post(self) -> None:
        """Generate and post a random turkey and provolone post with an AI image."""
        logger.info("Creating post at %s", datetime.now(timezone.utc).isoformat())

        post_content = self.generate_random_sandwich_post()
        image_path = self.generate_sandwich_image(post_content)
        post_id = self.post_to_facebook_with_image(post_content, image_path)

        if post_id:
            logger.info("Post successful")
            self.store_recent_post(str(post_id))
        else:
            logger.error("Post failed; content saved for later")
            self.save_failed_post(post_content)

    def load_sandwich_shops(self) -> None:
        """Load sandwich shops from a local JSON file."""
        if not SHOP_FILE.exists():
            return

        try:
            with SHOP_FILE.open("r", encoding="utf-8") as file:
                loaded_shops = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Error loading shops: %s", exc)
            return

        if not isinstance(loaded_shops, list):
            logger.warning("Ignoring sandwich shop file because it does not contain a list")
            return

        existing_names = {shop["name"].lower() for shop in self.sandwich_shops}
        new_shops = []
        for shop in loaded_shops:
            if not isinstance(shop, dict) or not isinstance(shop.get("name"), str):
                continue
            name = shop["name"].strip()
            if not name or name.lower() in existing_names:
                continue
            cleaned_shop = {str(key): str(value) for key, value in shop.items() if value is not None}
            cleaned_shop["name"] = name
            new_shops.append(cleaned_shop)
            existing_names.add(name.lower())

        self.sandwich_shops.extend(new_shops)
        logger.info("Loaded %s shops from file", len(new_shops))

    def generate_random_sandwich_post(self) -> dict[str, Any]:
        """Generate a brainrot/Gen Alpha sandwich caption."""
        bread = random.choice(self.bread_types)
        addon = random.choice(self.add_ons)
        condiment = random.choice(self.condiments)
        template = random.choice(self.caption_templates)
        caption = template.format(bread=bread, addon=addon, condiment=condiment)

        return {
            "text": caption,
            "image_style": random.choice(list(self.image_style_prompts)),
            "ingredients": {
                "bread": bread,
                "addon": addon,
                "condiment": condiment,
            },
        }

    def log_activity(self, message: str) -> None:
        """Log activities to a file."""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = f"[{timestamp}] {self._clean_message(message, limit=500)}\n"
            with (LOG_DIR / "sandwich_shop_activity.log").open("a", encoding="utf-8") as file:
                file.write(log_entry)
            logger.info("%s", message)
        except OSError as exc:
            logger.error("Error logging activity: %s", exc)

    def store_recent_post(self, post_id: str) -> None:
        """Store recent post ID for comment monitoring."""
        recent_posts_file = LOG_DIR / "recent_posts.json"
        recent_posts: list[dict[str, Any]] = []

        if recent_posts_file.exists():
            try:
                with recent_posts_file.open("r", encoding="utf-8") as file:
                    loaded_posts = json.load(file)
                if isinstance(loaded_posts, list):
                    recent_posts = [post for post in loaded_posts if isinstance(post, dict)]
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Ignoring unreadable recent posts file: %s", exc)

        recent_posts.append(
            {
                "post_id": post_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checked": False,
            }
        )
        self._atomic_write_json(recent_posts_file, recent_posts[-10:])

    def save_failed_post(self, post_content: dict[str, Any]) -> None:
        """Save failed posts to a file for later review."""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = SAVED_POST_DIR / f"failed_post_{timestamp}.json"
            payload = {
                "text": self._clean_message(post_content.get("text")),
                "image_style": post_content.get("image_style"),
                "ingredients": post_content.get("ingredients"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._atomic_write_json(filename, payload)
            logger.info("Post saved to: %s", filename)
        except OSError as exc:
            logger.error("Error saving post: %s", exc)

    def run_single_post(self) -> None:
        """Run a single post, which is suitable for GitHub Actions."""
        logger.info("Turkey and Provolone Bot - Single Post Mode with AI Images")
        logger.info("=" * 60)
        self.create_and_post()
        logger.info("Single post execution completed")


def main() -> int:
    """CLI entry point."""
    print("Turkey and Provolone Facebook Bot with AI Images")
    print("=" * 50)

    required_vars = ["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"]
    optional_vars = ["OPENAI_API_KEY", "STABILITY_API_KEY", "REPLICATE_API_TOKEN"]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    available_ai_services = [var for var in optional_vars if os.getenv(var)]

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return 1

    if not available_ai_services:
        print("No AI image generation services configured.")
        print("The bot will post text-only content without images.")
    else:
        print("Available AI services:")
        for var in available_ai_services:
            print(f"   - {var}")

    bot = TurkeyProvoloneBot()
    if not bot.facebook_ready:
        print("Cannot start bot because Facebook API is not ready")
        return 1

    run_mode = os.getenv("RUN_MODE", "single").strip().lower()
    if run_mode != "single":
        print("Scheduled mode is not implemented in this version; running one post.")

    bot.run_single_post()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
