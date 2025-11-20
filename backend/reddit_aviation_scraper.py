"""
Reddit Aviation Scraper
Monitors aviation subreddits for recruitment activity

Target subreddits:
- r/aviation
- r/flightradar24
- r/AviationSpotters
- r/aviation_memes (sometimes used for coded communication)
- r/ATC (Air Traffic Controllers)
"""

import praw
import sqlite3
from datetime import datetime
import re
from typing import List, Dict
import os

class RedditAviationScraper:
    """
    Scrapes aviation subreddits for potential recruitment posts

    Requires Reddit API credentials (free)
    Get them at: https://www.reddit.com/prefs/apps
    """

    def __init__(self, db_path='data/drone_cuas.db'):
        self.db_path = db_path

        # Reddit API credentials (need to be set as environment variables)
        # For MVP demo: Instructions to get credentials
        self.setup_instructions = """
╔═══════════════════════════════════════════════════════════════╗
║         REDDIT API SETUP INSTRUCTIONS                         ║
╚═══════════════════════════════════════════════════════════════╝

To enable Reddit scraping, you need API credentials:

1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - Name: "Drone CUAS OSINT Dashboard"
   - App type: Select "script"
   - Description: "OSINT monitoring for security research"
   - About URL: (leave blank)
   - Redirect URI: http://localhost:8080

4. Click "Create app"

5. You'll see:
   - client_id: [string under "personal use script"]
   - client_secret: [string next to "secret"]

6. Set environment variables:
   export REDDIT_CLIENT_ID="your_client_id_here"
   export REDDIT_CLIENT_SECRET="your_client_secret_here"
   export REDDIT_USER_AGENT="DroneOSINT/1.0 by YourUsername"

7. Run this script again

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example .env file:
```
REDDIT_CLIENT_ID=abc123xyz
REDDIT_CLIENT_SECRET=def456uvw
REDDIT_USER_AGENT=DroneOSINT/1.0 by marcel_researcher
```
"""

        # Target subreddits
        self.subreddits = [
            'aviation',           # 1.2M members
            'flightradar24',      # 50k members - most relevant
            'aviationspotters',   # Smaller but focused
            'ATC',                # Air Traffic Controllers - HIGH value targets
            'aviation_memes',     # Sometimes used for coded communication
        ]

        # Suspicious keywords specific to aviation recruitment
        self.recruitment_keywords = [
            # Payment indicators
            r'\$\d+.*(?:week|month|photo|data)',
            r'€\d+.*(?:week|month|photo|data)',
            r'(?:pay|payment|compensation).*(?:for|if)',

            # Recruitment language
            r'(?:need|looking for|seeking).*(?:someone|people|person)',
            r'(?:DM|PM|message).*(?:me|us)',
            r'(?:telegram|signal|wickr|protonmail)',

            # Intelligence tasks
            r'(?:track|monitor|photograph).*(?:specific|particular|certain)',
            r'(?:military|government).*(?:aircraft|flight)',
            r'(?:real-time|live).*(?:tracking|updates)',
            r'(?:airport|airbase).*(?:access|near)',
        ]

    def check_credentials(self) -> bool:
        """Check if Reddit API credentials are available"""
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')

        if not all([client_id, client_secret, user_agent]):
            print(self.setup_instructions)
            return False

        return True

    def setup_database(self):
        """Create reddit_posts table if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE NOT NULL,
                subreddit TEXT NOT NULL,
                title TEXT,
                author TEXT,
                content TEXT,
                url TEXT,
                created_utc TIMESTAMP,
                score INTEGER,
                num_comments INTEGER,
                suspicious_score INTEGER DEFAULT 0,
                flagged_keywords TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Reddit posts table ready")

    def calculate_suspicion_score(self, title: str, content: str) -> tuple:
        """
        Calculate suspicion score for Reddit post

        Returns: (score, matched_keywords)
        """
        combined_text = f"{title} {content}".lower()
        score = 0
        matched = []

        for pattern in self.recruitment_keywords:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 10
                matched.append(pattern[:30])

        # Bonus scoring
        if 'telegram' in combined_text and ('contact' in combined_text or 'dm' in combined_text):
            score += 15

        if ('military' in combined_text or 'government' in combined_text) and 'track' in combined_text:
            score += 20

        if re.search(r'[\$€]\d{3,}', combined_text):
            score += 15

        return score, matched

    def scrape_subreddit(self, subreddit_name: str, limit: int = 100) -> List[Dict]:
        """
        Scrape posts from a subreddit

        Args:
            subreddit_name: Name of subreddit (without r/)
            limit: Number of recent posts to fetch

        Returns:
            List of post dictionaries
        """
        if not self.check_credentials():
            return []

        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )

        subreddit = reddit.subreddit(subreddit_name)
        posts = []

        print(f"📡 Scraping r/{subreddit_name} (limit: {limit})...")

        for submission in subreddit.new(limit=limit):
            # Calculate suspicion score
            score, keywords = self.calculate_suspicion_score(
                submission.title,
                submission.selftext
            )

            post_data = {
                'post_id': submission.id,
                'subreddit': subreddit_name,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'content': submission.selftext,
                'url': f"https://reddit.com{submission.permalink}",
                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'score': submission.score,
                'num_comments': submission.num_comments,
                'suspicious_score': score,
                'flagged_keywords': str(keywords) if keywords else None,
            }

            posts.append(post_data)

            # Show high-value posts immediately
            if score >= 30:
                print(f"   🚨 HIGH SCORE ({score}): {submission.title[:60]}...")

        print(f"   ✅ Scraped {len(posts)} posts from r/{subreddit_name}")
        return posts

    def save_posts_to_db(self, posts: List[Dict]):
        """Save scraped posts to database"""
        if not posts:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved = 0
        duplicates = 0

        for post in posts:
            try:
                cursor.execute("""
                    INSERT INTO reddit_posts
                    (post_id, subreddit, title, author, content, url,
                     created_utc, score, num_comments, suspicious_score, flagged_keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post['post_id'],
                    post['subreddit'],
                    post['title'],
                    post['author'],
                    post['content'],
                    post['url'],
                    post['created_utc'],
                    post['score'],
                    post['num_comments'],
                    post['suspicious_score'],
                    post['flagged_keywords'],
                ))
                saved += 1
            except sqlite3.IntegrityError:
                # Post already exists (duplicate)
                duplicates += 1

        conn.commit()
        conn.close()

        print(f"💾 Saved {saved} new posts, {duplicates} duplicates skipped")

    def scrape_all_subreddits(self, limit: int = 100):
        """Scrape all configured aviation subreddits"""
        all_posts = []

        for subreddit in self.subreddits:
            posts = self.scrape_subreddit(subreddit, limit)
            all_posts.extend(posts)

        # Save to database
        self.save_posts_to_db(all_posts)

        return all_posts

    def generate_report(self) -> str:
        """Generate report from scraped Reddit posts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM reddit_posts")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE suspicious_score >= 30")
        high_risk = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE suspicious_score >= 50")
        critical = cursor.fetchone()[0]

        # Get top suspicious posts
        cursor.execute("""
            SELECT title, subreddit, author, suspicious_score, url
            FROM reddit_posts
            WHERE suspicious_score > 0
            ORDER BY suspicious_score DESC
            LIMIT 10
        """)
        top_posts = cursor.fetchall()

        conn.close()

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REDDIT AVIATION MONITORING REPORT                     ║
╚═══════════════════════════════════════════════════════════════╝

📊 STATISTICS:
   Total Posts Scraped: {total}
   High Risk (30+):     {high_risk}
   Critical (50+):      {critical}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 TOP 10 SUSPICIOUS POSTS:
"""

        for i, (title, subreddit, author, score, url) in enumerate(top_posts, 1):
            report += f"""
{i}. Score: {score}/100 | r/{subreddit}
   Title: {title[:70]}...
   Author: u/{author}
   URL: {url}
"""

        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        return report


if __name__ == '__main__':
    scraper = RedditAviationScraper()

    print("🔍 Reddit Aviation Scraper - Recruitment Monitoring\n")

    # Setup database
    scraper.setup_database()

    # Check if credentials are available
    if not scraper.check_credentials():
        print("\n⚠️  Reddit API credentials not found.")
        print("   Follow the instructions above to get credentials.")
        print("\n💡 For demo purposes, the scraper is ready to run once credentials are added.")
    else:
        print("✅ Reddit API credentials found!")
        print("\n🚀 Starting scraping...\n")

        # Scrape all subreddits
        posts = scraper.scrape_all_subreddits(limit=100)

        # Generate report
        report = scraper.generate_report()
        print(report)

        print(f"\n✅ Scraping complete! Found {len(posts)} posts across {len(scraper.subreddits)} subreddits")
