#!/usr/bin/env python3
"""
Turkey & Provolone Facebook Bot with AI-Generated Images
Generates random turkey and provolone sandwich posts with AI images for Facebook
"""
import os
import random
import requests
import schedule
import time
from datetime import datetime, timedelta
import json
import logging
import base64
from io import BytesIO

# make dirs
os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("saved_posts", exist_ok=True)
os.makedirs("generated_images", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TurkeyProvoloneBot:
    def __init__(self):
        
        # Facebook API credentials
        self.facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.facebook_ready = False
        
        # AI Image Generation APIs (choose one or have fallbacks)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # For DALL-E
        self.stability_api_key = os.getenv('STABILITY_API_KEY')  # For Stable Diffusion
        self.replicate_api_token = os.getenv('REPLICATE_API_TOKEN')  # For various models
        
        # Initialize APIs
        self.setup_facebook()
        
        # Image generation prompts for sandwiches
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
            "A classic turkey and provolone sandwich on fresh white bread, simple and appetizing, deli-style photography"
        ]
        
        # Style variations for prompts
        self.style_additions = [
            ", 4K high resolution, professional food photography",
            ", warm natural lighting, shallow depth of field",
            ", commercial food photography, appetizing presentation",
            ", rustic wooden background, artisanal style",
            ", clean white background, minimalist food photography",
            ", cozy café atmosphere, warm lighting",
            ", vintage food photography style, film grain",
            ", modern food styling, geometric plating"
        ]
        
        # Random sandwich descriptions (existing content)
        self.sandwich_posts = [
            {
                "text": "🦃 Today's special: Thick-cut turkey with aged provolone on fresh sourdough. Simple perfection! #TurkeyProvolone #Sandwich",
                "emoji": "🥪",
                "image_style": "classic_deli"
            },
            {
                "text": "Nothing beats the classic combo - premium turkey breast and creamy provolone. What's your go-to bread choice? 🍞",
                "emoji": "🦃",
                "image_style": "gourmet_close_up"
            },
            {
                "text": "Pro tip: Let your provolone come to room temperature before assembling. It makes ALL the difference! 🧀✨",
                "emoji": "💡",
                "image_style": "instructional"
            },
            {
                "text": "Turkey and provolone with a touch of mayo, lettuce, and tomato. Sometimes the classics are classic for a reason! 🍅",
                "emoji": "🥬",
                "image_style": "classic_full"
            },
            {
                "text": "Friday feeling: Grilled turkey and provolone panini. Crispy outside, melty inside. Pure bliss! 🔥",
                "emoji": "🍳",
                "image_style": "grilled_panini"
            },
            {
                "text": "Weekend vibes: Turkey, provolone, avocado, and a drizzle of olive oil on ciabatta. Living the dream! 🥑",
                "emoji": "🌟",
                "image_style": "gourmet_weekend"
            }
        ]
        
        # Rest of your existing initialization code...
        self.sandwich_shops = [
            {
                "name": "Tony's Deli",
                "location": "Downtown",
                "specialty": "Classic turkey and provolone on fresh Italian bread",
                "added_by": "admin",
                "date_added": "2025-01-01",
                "status": "verified"
            },
            {
                "name": "Corner Bistro",
                "location": "Main Street",
                "specialty": "Gourmet turkey with aged provolone and herb aioli",
                "added_by": "admin", 
                "date_added": "2025-01-01",
                "status": "verified"
            }
        ]
        
        self.load_sandwich_shops()
        
        # Additional elements...
        self.bread_types = [
            "sourdough", "ciabatta", "whole wheat", "rye", "focaccia", 
            "kaiser roll", "everything bagel", "french bread", "pumpernickel"
        ]
        
        self.add_ons = [
            "crisp lettuce", "ripe tomatoes", "red onion", "pickles", 
            "avocado", "sprouts", "roasted red peppers", "cucumber"
        ]
        
        self.condiments = [
            "mayo", "mustard", "pesto", "olive oil", "balsamic glaze", 
            "herb aioli", "honey mustard", "chipotle mayo"
        ]
    
    def setup_facebook(self):
        """Initialize Facebook API connection"""
        try:
            if self.facebook_access_token and self.facebook_page_id:
                test_url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}"
                test_params = {'access_token': self.facebook_access_token}
                response = requests.get(test_url, params=test_params)
                
                if response.status_code == 200:
                    page_info = response.json()
                    logger.info(f"✅ Connected to Facebook page: {page_info.get('name', 'Unknown')}")
                    self.facebook_ready = True
                else:
                    logger.error(f"❌ Facebook API test failed: {response.status_code}")
                    self.facebook_ready = False
            else:
                logger.error("❌ Facebook credentials not provided")
                self.facebook_ready = False
        except Exception as e:
            logger.error(f"❌ Error setting up Facebook API: {e}")
            self.facebook_ready = False
    
    def generate_image_with_openai(self, prompt):
        """Generate image using OpenAI DALL-E"""
        if not self.openai_api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
                "response_format": "b64_json"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                image_b64 = result['data'][0]['b64_json']
                image_data = base64.b64decode(image_b64)
                logger.info("✅ Generated image with OpenAI DALL-E")
                return image_data
            else:
                logger.error(f"❌ OpenAI API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error with OpenAI image generation: {e}")
            return None
    
    def generate_image_with_stability(self, prompt):
        """Generate image using Stability AI"""
        if not self.stability_api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.stability_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            }
            
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                image_b64 = result['artifacts'][0]['base64']
                image_data = base64.b64decode(image_b64)
                logger.info("✅ Generated image with Stability AI")
                return image_data
            else:
                logger.error(f"❌ Stability AI error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error with Stability AI image generation: {e}")
            return None
    
    def generate_image_with_replicate(self, prompt):
        """Generate image using Replicate API"""
        if not self.replicate_api_token:
            return None
        
        try:
            headers = {
                "Authorization": f"Token {self.replicate_api_token}",
                "Content-Type": "application/json"
            }
            
            # Using SDXL model (you can change this)
            data = {
                "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                "input": {
                    "prompt": prompt,
                    "width": 1024,
                    "height": 1024,
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 20
                }
            }
            
            # Start the prediction
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                prediction = response.json()
                prediction_id = prediction['id']
                
                # Poll for completion
                for _ in range(30):  # Wait up to 5 minutes
                    time.sleep(10)
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data['status'] == 'succeeded':
                            image_url = status_data['output'][0]
                            # Download the image
                            img_response = requests.get(image_url)
                            if img_response.status_code == 200:
                                logger.info("✅ Generated image with Replicate")
                                return img_response.content
                        elif status_data['status'] == 'failed':
                            logger.error("❌ Replicate generation failed")
                            return None
                
                logger.error("❌ Replicate generation timed out")
                return None
            else:
                logger.error(f"❌ Replicate API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error with Replicate image generation: {e}")
            return None
    
    def generate_sandwich_image(self, post_content=None):
        """Generate a sandwich image using available AI services"""
        
        # Create a detailed prompt
        if post_content and post_content.get('image_style'):
            style = post_content['image_style']
            if style == "grilled_panini":
                base_prompt = "A perfectly grilled turkey and provolone panini sandwich, golden crispy bread with grill marks, melted cheese oozing out"
            elif style == "gourmet_close_up":
                base_prompt = "Extreme close-up of a gourmet turkey and provolone sandwich, focusing on the layers and textures"
            elif style == "classic_deli":
                base_prompt = "A classic deli-style turkey and provolone sandwich on fresh bread, traditional presentation"
            else:
                base_prompt = random.choice(self.image_prompts)
        else:
            base_prompt = random.choice(self.image_prompts)
        
        # Add random style elements
        style_addition = random.choice(self.style_additions)
        full_prompt = base_prompt + style_addition
        
        logger.info(f"🎨 Generating image with prompt: {full_prompt[:100]}...")
        
        # Try different AI services in order of preference
        image_data = None
        
        # Try OpenAI first (usually highest quality)
        if self.openai_api_key and not image_data:
            image_data = self.generate_image_with_openai(full_prompt)
        
        # Try Stability AI as fallback
        if self.stability_api_key and not image_data:
            image_data = self.generate_image_with_stability(full_prompt)
        
        # Try Replicate as final fallback
        if self.replicate_api_token and not image_data:
            image_data = self.generate_image_with_replicate(full_prompt)
        
        if image_data:
            # Save the generated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_images/sandwich_{timestamp}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"💾 Saved generated image: {filename}")
            return filename
        else:
            logger.warning("❌ Failed to generate image with any service")
            return None
    
    def post_to_facebook_with_image(self, post_content, image_path=None):
        """Post content to Facebook page with optional image"""
        if not self.facebook_ready:
            logger.error("❌ Facebook API not available")
            return False
        
        try:
            # Handle custom message from workflow input
            custom_message = os.getenv('CUSTOM_MESSAGE')
            if custom_message:
                full_message = custom_message
            else:
                full_message = f"{post_content['emoji']} {post_content['text']}"
            
            if image_path and os.path.exists(image_path):
                # Post with image
                post_url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/photos"
                
                with open(image_path, 'rb') as image_file:
                    files = {'source': image_file}
                    data = {
                        'message': full_message,
                        'access_token': self.facebook_access_token
                    }
                    
                    response = requests.post(post_url, data=data, files=files)
            else:
                # Post text only (fallback)
                post_url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/feed"
                post_data = {
                    'message': full_message,
                    'access_token': self.facebook_access_token
                }
                response = requests.post(post_url, data=post_data)
            
            if response.status_code == 200:
                post_data = response.json()
                post_id = post_data['id']
                logger.info(f"✅ Posted to Facebook: {post_id}")
                logger.info(f"📝 Content: {full_message[:60]}...")
                if image_path:
                    logger.info(f"🖼️ With image: {image_path}")
                
                self.log_activity(f"POST CREATED: {post_id} - {full_message[:50]}...")
                return post_id
            else:
                logger.error(f"❌ Failed to post: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error posting to Facebook: {e}")
            return False
    
    def create_and_post(self):
        """Generate and post a random turkey and provolone post with AI image"""
        logger.info(f"\n🕐 Creating post at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate random post content
        post_content = self.generate_random_sandwich_post()
        
        # Generate AI image
        image_path = self.generate_sandwich_image(post_content)
        
        # Post to Facebook with image
        post_id = self.post_to_facebook_with_image(post_content, image_path)
        
        if post_id:
            logger.info("🎉 Post successful!")
            self.store_recent_post(post_id)
        else:
            logger.error("😞 Post failed - content saved for later")
            self.save_failed_post(post_content)
    
    # Include all your existing methods here...
    # (load_sandwich_shops, save_sandwich_shops, add_sandwich_shop, etc.)
    
    def load_sandwich_shops(self):
        """Load sandwich shops from file"""
        try:
            if os.path.exists('sandwich_shops.json'):
                with open('sandwich_shops.json', 'r') as f:
                    loaded_shops = json.load(f)
                    existing_names = {shop['name'].lower() for shop in self.sandwich_shops}
                    new_shops = [shop for shop in loaded_shops if shop['name'].lower() not in existing_names]
                    self.sandwich_shops.extend(new_shops)
                    logger.info(f"📂 Loaded {len(new_shops)} shops from file")
        except Exception as e:
            logger.warning(f"⚠️ Error loading shops: {e}")
    
    def generate_random_sandwich_post(self):
        """Generate a random sandwich-focused post"""
        return random.choice(self.sandwich_posts)
    
    def log_activity(self, message):
        """Log activities to a file"""
        try:
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            with open("logs/sandwich_shop_activity.log", "a") as f:
                f.write(log_entry)
            
            logger.info(f"📝 {message}")
        except Exception as e:
            logger.error(f"⚠️ Error logging: {e}")
    
    def store_recent_post(self, post_id):
        """Store recent post ID for comment monitoring"""
        try:
            os.makedirs("logs", exist_ok=True)
            recent_posts_file = "logs/recent_posts.json"
            
            recent_posts = []
            if os.path.exists(recent_posts_file):
                with open(recent_posts_file, 'r') as f:
                    recent_posts = json.load(f)
            
            recent_posts.append({
                "post_id": post_id,
                "timestamp": datetime.now().isoformat(),
                "checked": False
            })
            
            recent_posts = recent_posts[-10:]
            
            with open(recent_posts_file, 'w') as f:
                json.dump(recent_posts, f, indent=2)
                
        except Exception as e:
            logger.error(f"⚠️ Error storing post ID: {e}")
    
    def save_failed_post(self, post_content):
        """Save failed posts to a file"""
        try:
            os.makedirs("saved_posts", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"saved_posts/failed_post_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"{post_content['emoji']} {post_content['text']}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
            
            logger.info(f"💾 Post saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving post: {e}")
    
    def run_single_post(self):
        """Run a single post (perfect for GitHub Actions)"""
        logger.info("🚀 Turkey & Provolone Bot - Single Post Mode with AI Images")
        logger.info("=" * 60)
        
        # Create and post new content with AI image
        self.create_and_post()
        
        logger.info("✅ Single post execution completed")

def main():
    """Main function"""
    print("🦃 Turkey & Provolone Facebook Bot with AI Images")
    print("=" * 50)
    
    # Check for required environment variables
    required_vars = ['FACEBOOK_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID']
    optional_vars = ['OPENAI_API_KEY', 'STABILITY_API_KEY', 'REPLICATE_API_TOKEN']
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    available_ai_services = [var for var in optional_vars if os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        return
    
    if not available_ai_services:
        print("⚠️ No AI image generation services configured!")
        print("Add at least one of these environment variables:")
        for var in optional_vars:
            print(f"   • {var}")
        print("\nThe bot will post text-only content without images.")
    else:
        print("✅ Available AI services:")
        for var in available_ai_services:
            print(f"   • {var}")
    
    # Create and run the bot
    bot = TurkeyProvoloneBot()
    
    if bot.facebook_ready:
        run_mode = os.getenv('RUN_MODE', 'single')
        
        if run_mode == 'single':
            bot.run_single_post()
        else:
            print("Scheduled mode not implemented in this version")
    else:
        print("❌ Cannot start bot - Facebook API not ready")
        exit(1)

if __name__ == "__main__":
    main()
