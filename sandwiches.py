#!/usr/bin/env python3
"""
Turkey & Provolone Facebook Bot
Generates random turkey and provolone sandwich posts for Facebook
"""

import os
import random
import requests
import schedule
import time
from datetime import datetime, timedelta
import json
import logging

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
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        os.makedirs("saved_posts", exist_ok=True)
        
        # Facebook API credentials
        self.facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.facebook_ready = False
        
        # Initialize Facebook API
        self.setup_facebook()
        
        # Random sandwich descriptions
        self.sandwich_posts = [
            {
                "text": "🦃 Today's special: Thick-cut turkey with aged provolone on fresh sourdough. Simple perfection! #TurkeyProvolone #Sandwich",
                "emoji": "🥪"
            },
            {
                "text": "Nothing beats the classic combo - premium turkey breast and creamy provolone. What's your go-to bread choice? 🍞",
                "emoji": "🦃"
            },
            {
                "text": "Pro tip: Let your provolone come to room temperature before assembling. It makes ALL the difference! 🧀✨",
                "emoji": "💡"
            },
            {
                "text": "Turkey and provolone with a touch of mayo, lettuce, and tomato. Sometimes the classics are classic for a reason! 🍅",
                "emoji": "🥬"
            },
            {
                "text": "Craving that perfect balance of savory turkey and mild, nutty provolone? You're in the right place! 😋",
                "emoji": "🎯"
            },
            {
                "text": "Fun fact: Provolone pairs with turkey because its buttery texture complements the lean protein perfectly! 🧠",
                "emoji": "🤓"
            },
            {
                "text": "Friday feeling: Grilled turkey and provolone panini. Crispy outside, melty inside. Pure bliss! 🔥",
                "emoji": "🍳"
            },
            {
                "text": "Weekend vibes: Turkey, provolone, avocado, and a drizzle of olive oil on ciabatta. Living the dream! 🥑",
                "emoji": "🌟"
            },
            {
                "text": "Cold turkey and provolone for lunch, or warm and melted? Tell us your preference in the comments! 💭",
                "emoji": "🤔"
            },
            {
                "text": "The secret ingredient in any great turkey and provolone? Love. And maybe a little mustard. 💛",
                "emoji": "❤️"
            },
            {
                "text": "Rainy day comfort food: Turkey and provolone grilled cheese with a side of tomato soup. Perfection! ☔",
                "emoji": "🍲"
            },
            {
                "text": "Did you know? The best turkey and provolone sandwiches are made with intention, not just hunger. 🎨",
                "emoji": "🧘"
            },
            {
                "text": "Monday motivation: Start your week with a perfectly balanced turkey and provolone on everything bagel! 💪",
                "emoji": "🥯"
            },
            {
                "text": "Sandwich science: The ideal turkey-to-provolone ratio is 3:1. Trust us, we've done the research! 📊",
                "emoji": "🔬"
            },
            {
                "text": "Throwback to simpler times when a turkey and provolone sandwich solved all of life's problems. Still does! 🕰️",
                "emoji": "✨"
            }
        ]
        
        # Sandwich shops database
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
        
        # Load existing shops from file if it exists
        self.load_sandwich_shops()
        
        # Posts that encourage shop recommendations
        self.shop_recommendation_posts = [
            {
                "text": "🏪 Local Love Alert! What's your favorite sandwich shop for turkey and provolone? Drop their name below! If your comment gets 5+ likes, we'll feature them! 👇",
                "emoji": "❤️"
            },
            {
                "text": "🗺️ Help us map the best turkey and provolone in town! Comment your go-to sandwich spot below. 5+ likes = instant feature! 🌟",
                "emoji": "📍"
            },
            {
                "text": "🏆 Sandwich Shop Spotlight time! Tell us about a local place that makes an amazing turkey and provolone. Community votes (5+ likes) get them featured! 🥪",
                "emoji": "🎯"
            },
            {
                "text": "🤝 Supporting local businesses one sandwich at a time! What shop in your area serves the best turkey and provolone? Let the community decide with likes! ❤️",
                "emoji": "🏪"
            }
        ]
        
        # Additional random elements
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
                # Test the connection
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
    
    def load_sandwich_shops(self):
        """Load sandwich shops from file"""
        try:
            if os.path.exists('sandwich_shops.json'):
                with open('sandwich_shops.json', 'r') as f:
                    loaded_shops = json.load(f)
                    # Don't duplicate existing shops
                    existing_names = {shop['name'].lower() for shop in self.sandwich_shops}
                    new_shops = [shop for shop in loaded_shops if shop['name'].lower() not in existing_names]
                    self.sandwich_shops.extend(new_shops)
                    logger.info(f"📂 Loaded {len(new_shops)} shops from file")
        except Exception as e:
            logger.warning(f"⚠️ Error loading shops: {e}")
    
    def save_sandwich_shops(self):
        """Save sandwich shops to file"""
        try:
            # Only save user-added shops (not the default admin ones)
            user_shops = [shop for shop in self.sandwich_shops if shop.get('added_by') != 'admin']
            with open('sandwich_shops.json', 'w') as f:
                json.dump(user_shops, f, indent=2)
            logger.info(f"💾 Saved {len(user_shops)} user shops to file")
        except Exception as e:
            logger.error(f"⚠️ Error saving shops: {e}")
    
    def add_sandwich_shop(self, name, location="Unknown", specialty="Turkey and provolone", added_by="user", comment_id=None):
        """Add a new sandwich shop to the database"""
        new_shop = {
            "name": name,
            "location": location,
            "specialty": specialty,
            "added_by": added_by,
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "status": "pending" if added_by == "user" else "verified",
            "comment_id": comment_id,
            "likes_when_added": 0
        }
        
        # Check if shop already exists
        existing = next((shop for shop in self.sandwich_shops if shop['name'].lower() == name.lower()), None)
        if not existing:
            self.sandwich_shops.append(new_shop)
            self.save_sandwich_shops()
            self.log_activity(f"NEW SHOP ADDED: {name} (by {added_by})")
            return True
        else:
            self.log_activity(f"DUPLICATE SHOP IGNORED: {name}")
            return False
    
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
    
    def check_comments_for_shops(self, post_id, check_hours_back=24):
        """Check recent comments for sandwich shop recommendations with 5+ likes"""
        if not self.facebook_ready:
            return
        
        try:
            # Get comments on the post
            comments_url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
            params = {
                'access_token': self.facebook_access_token,
                'fields': 'id,message,like_count,created_time,from',
                'limit': 100
            }
            
            response = requests.get(comments_url, params=params)
            
            if response.status_code == 200:
                comments_data = response.json()
                comments = comments_data.get('data', [])
                
                self.log_activity(f"CHECKING COMMENTS: Found {len(comments)} comments on post {post_id}")
                
                # Check each comment for shop recommendations with 5+ likes
                for comment in comments:
                    if comment.get('like_count', 0) >= 5:
                        message = comment.get('message', '').strip()
                        comment_id = comment.get('id')
                        
                        # Simple shop detection (you can enhance this logic)
                        if self.looks_like_shop_recommendation(message):
                            shop_name = self.extract_shop_name(message)
                            if shop_name:
                                success = self.add_sandwich_shop(
                                    name=shop_name,
                                    added_by="community",
                                    comment_id=comment_id
                                )
                                
                                if success:
                                    self.log_activity(f"COMMUNITY SHOP ADDED: {shop_name} (5+ likes)")
                                    # Could send notification or reply to comment here
                                
            else:
                self.log_activity(f"ERROR CHECKING COMMENTS: {response.status_code}")
                
        except Exception as e:
            self.log_activity(f"ERROR IN COMMENT CHECKING: {str(e)}")
    
    def looks_like_shop_recommendation(self, message):
        """Detect if a comment looks like a shop recommendation"""
        message_lower = message.lower()
        
        # Keywords that indicate shop recommendations
        shop_keywords = [
            'deli', 'bistro', 'cafe', 'restaurant', 'shop', 'market',
            'sandwich', 'subs', 'hoagie', 'hero', 'grinder'
        ]
        
        location_keywords = [
            'street', 'avenue', 'road', 'boulevard', 'downtown', 'main',
            'corner', 'plaza', 'center', 'mall'
        ]
        
        # Check for shop-related keywords
        has_shop_keyword = any(keyword in message_lower for keyword in shop_keywords)
        has_location = any(keyword in message_lower for keyword in location_keywords)
        
        # Check for common patterns
        patterns = ['at ', 'on ', 'in ', "'s ", 'the ']
        has_pattern = any(pattern in message_lower for pattern in patterns)
        
        return has_shop_keyword or (has_location and has_pattern) or len(message.split()) <= 10
    
    def extract_shop_name(self, message):
        """Extract shop name from comment (basic implementation)"""
        # This is a simple extraction - you might want to enhance this
        # Remove common words and extract potential shop names
        
        words = message.split()
        
        # Look for capitalized words that might be shop names
        potential_names = []
        for i, word in enumerate(words):
            if word and word[0].isupper() and word.lower() not in ['the', 'a', 'an', 'and', 'or', 'but', 'at', 'on', 'in']:
                # Check if next word is also capitalized (multi-word name)
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    potential_names.append(f"{word} {words[i + 1]}")
                else:
                    potential_names.append(word)
        
        # Return the first potential name or the whole message if short
        if potential_names:
            return potential_names[0]
        elif len(message.split()) <= 3:
            return message.strip()
        else:
            return None
    
    def generate_random_sandwich_post(self):
        """Generate a random sandwich-focused post"""
        post_type = random.choice(['preset', 'custom', 'shop_recommendation', 'shop_feature'])
        
        if post_type == 'preset':
            return random.choice(self.sandwich_posts)
        elif post_type == 'shop_recommendation':
            return random.choice(self.shop_recommendation_posts)
        elif post_type == 'shop_feature' and len(self.sandwich_shops) > 2:
            # Feature a random sandwich shop
            shop = random.choice([s for s in self.sandwich_shops if s.get('status') == 'verified'])
            return {
                "text": f"🌟 Sandwich Shop Spotlight: {shop['name']} in {shop['location']}! Known for their {shop['specialty']}. Have you tried them? Let us know in the comments! 🥪",
                "emoji": "👑"
            }
        else:
            # Generate a custom post
            bread = random.choice(self.bread_types)
            addon = random.choice(self.add_ons)
            condiment = random.choice(self.condiments)
            
            custom_posts = [
                {
                    "text": f"🥪 Today's creation: Turkey and provolone on {bread} with {addon} and {condiment}. What would you add?",
                    "emoji": "🤤"
                },
                {
                    "text": f"Experimenting with turkey and provolone on {bread}. The {condiment} really makes it pop! 🎉",
                    "emoji": "👨‍🍳"
                },
                {
                    "text": f"Sometimes you need that perfect {bread} base for your turkey and provolone. Add some {addon} and you're golden! ✨",
                    "emoji": "🏆"
                }
            ]
            
            return random.choice(custom_posts)
    
    def post_to_facebook(self, post_content):
        """Post content to Facebook page"""
        if not self.facebook_ready:
            logger.error("❌ Facebook API not available")
            return False
        
        try:
            post_url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/feed"
            
            # Handle custom message from workflow input
            custom_message = os.getenv('CUSTOM_MESSAGE')
            if custom_message:
                full_message = custom_message
            else:
                # Combine text and emoji
                full_message = f"{post_content['emoji']} {post_content['text']}"
            
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
                
                # Log the post for later comment checking
                self.log_activity(f"POST CREATED: {post_id} - {full_message[:50]}...")
                
                return post_id  # Return post ID for comment monitoring
            else:
                logger.error(f"❌ Failed to post: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error posting to Facebook: {e}")
            return False
    
    def create_and_post(self):
        """Generate and post a random turkey and provolone post"""
        logger.info(f"\n🕐 Creating post at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate random post content
        post_content = self.generate_random_sandwich_post()
        
        # Post to Facebook
        post_id = self.post_to_facebook(post_content)
        
        if post_id:
            logger.info("🎉 Post successful!")
            
            # Store recent post IDs for comment monitoring
            self.store_recent_post(post_id)
            
        else:
            logger.error("😞 Post failed - content saved for later")
            self.save_failed_post(post_content)
    
    def store_recent_post(self, post_id):
        """Store recent post ID for comment monitoring"""
        try:
            os.makedirs("logs", exist_ok=True)
            recent_posts_file = "logs/recent_posts.json"
            
            # Load existing posts
            recent_posts = []
            if os.path.exists(recent_posts_file):
                with open(recent_posts_file, 'r') as f:
                    recent_posts = json.load(f)
            
            # Add new post
            recent_posts.append({
                "post_id": post_id,
                "timestamp": datetime.now().isoformat(),
                "checked": False
            })
            
            # Keep only last 10 posts
            recent_posts = recent_posts[-10:]
            
            # Save updated list
            with open(recent_posts_file, 'w') as f:
                json.dump(recent_posts, f, indent=2)
                
        except Exception as e:
            logger.error(f"⚠️ Error storing post ID: {e}")
    
    def check_recent_posts_for_comments(self):
        """Check recent posts for new shop recommendations"""
        try:
            recent_posts_file = "logs/recent_posts.json"
            if not os.path.exists(recent_posts_file):
                return
            
            with open(recent_posts_file, 'r') as f:
                recent_posts = json.load(f)
            
            logger.info(f"🔍 Checking {len(recent_posts)} recent posts for comments...")
            
            for post_data in recent_posts:
                post_id = post_data['post_id']
                if not post_data.get('checked', False):
                    self.check_comments_for_shops(post_id)
                    post_data['checked'] = True
            
            # Save updated check status
            with open(recent_posts_file, 'w') as f:
                json.dump(recent_posts, f, indent=2)
                
        except Exception as e:
            self.log_activity(f"ERROR CHECKING RECENT POSTS: {str(e)}")
    
    def generate_shop_report(self):
        """Generate a report of all tracked sandwich shops"""
        try:
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"reports/sandwich_shops_report_{timestamp}.json"
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "total_shops": len(self.sandwich_shops),
                "verified_shops": len([s for s in self.sandwich_shops if s.get('status') == 'verified']),
                "pending_shops": len([s for s in self.sandwich_shops if s.get('status') == 'pending']),
                "community_added": len([s for s in self.sandwich_shops if s.get('added_by') == 'community']),
                "shops": self.sandwich_shops
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_activity(f"REPORT GENERATED: {report_file}")
            logger.info(f"📊 Shop report saved: {report_file}")
            
        except Exception as e:
            self.log_activity(f"ERROR GENERATING REPORT: {str(e)}")
    
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
        logger.info("🚀 Turkey & Provolone Bot - Single Post Mode")
        logger.info("=" * 50)
        
        # Check recent posts for comments before posting new content
        self.check_recent_posts_for_comments()
        
        # Create and post new content
        self.create_and_post()
        
        # Generate shop report
        self.generate_shop_report()
        
        logger.info("✅ Single post execution completed")
    
    def run_scheduler(self):
        """Run the bot on a schedule (for local testing)"""
        logger.info("🚀 Turkey & Provolone Bot - Scheduled Mode")
        logger.info("=" * 50)
        
        # Schedule posts
        schedule.every(6).hours.do(self.create_and_post)
        schedule.every(1).hours.do(self.check_recent_posts_for_comments)
        schedule.every(24).hours.do(self.generate_shop_report)
        
        logger.info("📅 Schedule set:")
        logger.info("  • New posts: Every 6 hours")
        logger.info("  • Comment checks: Every hour")
        logger.info("  • Reports: Daily")
        
        # Run immediately on start
        self.run_single_post()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main function"""
    print("🦃 Turkey & Provolone Facebook Bot")
    print("=" * 40)
    
    # Check for required environment variables
    required_vars = ['FACEBOOK_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://developers.facebook.com/")
        print("2. Create a Facebook App")
        print("3. Get a Page Access Token for your page")
        print("4. Find your page ID (in your page's About section)")
        print("5. Set environment variables in GitHub Secrets:")
        print("   FACEBOOK_ACCESS_TOKEN")
        print("   FACEBOOK_PAGE_ID")
        return
    
    # Create and run the bot
    bot = TurkeyProvoloneBot()
    
    if bot.facebook_ready:
        # Check if running in GitHub Actions (or run mode specified)
        run_mode = os.getenv('RUN_MODE', 'single')
        
        if run_mode == 'single':
            bot.run_single_post()
        else:
            # For local testing with scheduler
            bot.run_scheduler()
    else:
        print("❌ Cannot start bot - Facebook API not ready")
        exit(1)  # Exit with error code for GitHub Actions

if __name__ == "__main__":
    main()