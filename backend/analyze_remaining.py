#!/usr/bin/env python3
"""
Analyze remaining posts (skip already analyzed) - safe for concurrent work
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict
import anthropic
import os
from dotenv import load_dotenv
import time

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
DB_PATH = "data/drone_cuas.db"
LOG_FILE = "/tmp/ai_analysis_progress.log"

CLASSIFICATION_PROMPT = """You are an OSINT analyst specializing in counter-UAS intelligence.

Analyze this Telegram post and provide:

1. **English Translation** (if not in English)
2. **Classification** - ONE of:
   - INTELLIGENCE_GATHERING (requests for surveillance, reconnaissance, photos/videos of infrastructure)
   - BOUNTY_OFFER (payment offered for tasks, includes crypto addresses)
   - RECRUITMENT (seeking people for operations)
   - COORDINATION (planning or coordinating activities)
   - CLAIM_RESPONSIBILITY (claiming credit for incidents)
   - NEWS_REPORT (just reporting news, no actionable intelligence)
   - PROPAGANDA (opinion/commentary without intelligence value)
   - IRRELEVANT (spam, off-topic, unrelated)

3. **Intelligence Value** (0-10 scale):
   - 9-10: Direct surveillance requests, bounties for specific targets
   - 7-8: Strong indicators of coordination, recruitment with specifics
   - 5-6: Relevant context about operations/capabilities
   - 3-4: Background information, general discussion
   - 0-2: No intelligence value

4. **Target Details** (if mentioned):
   - Specific locations (Belgium, Netherlands, airports, nuclear plants, NATO bases)
   - Infrastructure types
   - Payment amounts
   - Timeline information

5. **Confidence Level** (LOW/MEDIUM/HIGH/VERY_HIGH)

Post to analyze:
---
Channel: {channel}
Date: {date}
Content:
{content}
---

Respond in JSON format:
{{
  "translation": "English translation here",
  "classification": "CLASSIFICATION_TYPE",
  "intelligence_value": 7,
  "confidence": "HIGH",
  "reasoning": "Brief explanation of classification",
  "target_details": {{
    "locations": ["Belgium", "Doel"],
    "infrastructure": "nuclear plant",
    "payment_amount": "$1000",
    "payment_method": "Bitcoin",
    "timeline": "before November 3"
  }},
  "relevant_keywords": ["surveillance", "bounty", "nuclear"],
  "is_intelligence": true
}}
"""

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def analyze_post_with_ai(channel: str, date: str, content: str) -> Dict:
    """Use Claude to analyze and classify a Telegram post"""

    prompt = CLASSIFICATION_PROMPT.format(
        channel=channel,
        date=date,
        content=content[:4000]  # Limit content length
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text

        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        analysis = json.loads(response_text)
        return analysis

    except Exception as e:
        return {
            "translation": content,
            "classification": "ERROR",
            "intelligence_value": 0,
            "confidence": "LOW",
            "reasoning": f"Analysis failed: {str(e)}",
            "is_intelligence": False
        }

def main():
    log("=" * 80)
    log("AI ANALYSIS - REMAINING POSTS (SAFE MODE)")
    log("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get posts that need analysis (PENDING_ANALYSIS status)
    # Order by relevance score (original credibility_score from scraper)
    cursor.execute("""
        SELECT id, channel_name, post_date, content, post_url, credibility_score
        FROM social_media_posts
        WHERE platform = 'Telegram'
        AND verification_status = 'PENDING_ANALYSIS'
        ORDER BY credibility_score DESC
        LIMIT 150
    """)

    posts = cursor.fetchall()
    log(f"\n📊 Found {len(posts)} posts needing analysis")
    log(f"⏱️  Estimated time: {len(posts) * 3} seconds (~{len(posts) * 3 / 60:.1f} minutes)\n")

    if len(posts) == 0:
        log("✅ No posts need analysis - all done!")
        conn.close()
        return

    analyzed = 0
    intelligence_posts = 0
    start_time = time.time()

    for post_id, channel, post_date, content, post_url, relevance in posts:
        log(f"📝 Post #{post_id} - {channel} ({post_date[:10]}) [Relevance: {relevance:.2f}]")

        # Analyze with AI
        analysis = analyze_post_with_ai(channel, post_date, content)

        intel_value = analysis.get('intelligence_value', 0)
        classification = analysis.get('classification', 'UNKNOWN')
        confidence = analysis.get('confidence', 'LOW')

        log(f"   → {classification} | Intel: {intel_value}/10 | Confidence: {confidence}")

        if analysis.get('is_intelligence'):
            intelligence_posts += 1
            log(f"   ✅ INTELLIGENCE POST")

        # Update database with AI analysis
        cursor.execute("""
            UPDATE social_media_posts
            SET
                content = ?,
                verification_status = ?,
                credibility_score = ?,
                correlation_notes = ?
            WHERE id = ?
        """, (
            analysis.get('translation', content),
            confidence,
            intel_value / 10.0,  # Store as 0.0-1.0
            json.dumps({
                'classification': classification,
                'reasoning': analysis.get('reasoning', ''),
                'target_details': analysis.get('target_details', {}),
                'relevant_keywords': analysis.get('relevant_keywords', []),
                'original_content': content,
                'original_relevance_score': relevance
            }),
            post_id
        ))

        analyzed += 1

        # Commit every 10 to avoid conflicts
        if analyzed % 10 == 0:
            conn.commit()
            elapsed = time.time() - start_time
            rate = analyzed / elapsed
            remaining = len(posts) - analyzed
            eta = remaining / rate if rate > 0 else 0
            log(f"\n💾 Checkpoint: {analyzed}/{len(posts)} | Rate: {rate:.1f} posts/sec | ETA: {eta/60:.1f} min\n")

    conn.commit()
    conn.close()

    total_time = time.time() - start_time

    log("=" * 80)
    log("ANALYSIS COMPLETE")
    log("=" * 80)
    log(f"   Total analyzed: {analyzed}")
    log(f"   Intelligence posts: {intelligence_posts}")
    log(f"   Intelligence rate: {intelligence_posts/analyzed*100:.1f}%")
    log(f"   Total time: {total_time/60:.1f} minutes")
    log(f"   Average: {total_time/analyzed:.1f} sec/post")

if __name__ == "__main__":
    main()
