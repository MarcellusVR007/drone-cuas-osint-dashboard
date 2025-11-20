#!/usr/bin/env python3
"""
Analyze TOP 200 posts by relevance score - for quick quality results
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
DB_PATH = "data/drone_cuas.db"

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
        print(f"   ✗ Error: {e}")
        return {
            "translation": content,
            "classification": "ERROR",
            "intelligence_value": 0,
            "confidence": "LOW",
            "reasoning": f"Analysis failed: {str(e)}",
            "is_intelligence": False
        }

def main():
    print("=" * 80)
    print("AI ANALYSIS - TOP 200 POSTS BY RELEVANCE")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get top 200 posts by relevance (credibility_score)
    cursor.execute("""
        SELECT id, channel_name, post_date, content, post_url
        FROM social_media_posts
        WHERE platform = 'Telegram'
        ORDER BY credibility_score DESC
        LIMIT 200
    """)

    posts = cursor.fetchall()
    print(f"\n📊 Analyzing {len(posts)} top posts with AI...\n")

    analyzed = 0
    intelligence_posts = 0

    for post_id, channel, post_date, content, post_url in posts:
        print(f"📝 Post #{post_id} - {channel} ({post_date[:10]})")

        # Analyze with AI
        analysis = analyze_post_with_ai(channel, post_date, content)

        print(f"   Classification: {analysis.get('classification')}")
        print(f"   Intelligence Value: {analysis.get('intelligence_value')}/10")
        print(f"   Confidence: {analysis.get('confidence')}")

        if analysis.get('is_intelligence'):
            intelligence_posts += 1
            print(f"   ✅ INTELLIGENCE POST")

        # Update database
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
            analysis.get('confidence', 'LOW'),
            analysis.get('intelligence_value', 0) / 10.0,
            json.dumps({
                'classification': analysis.get('classification'),
                'reasoning': analysis.get('reasoning'),
                'target_details': analysis.get('target_details', {}),
                'relevant_keywords': analysis.get('relevant_keywords', []),
                'original_content': content
            }),
            post_id
        ))

        analyzed += 1

        # Commit every 10
        if analyzed % 10 == 0:
            conn.commit()
            print(f"\n💾 Checkpoint: {analyzed}/200 posts analyzed\n")

    conn.commit()
    conn.close()

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"   Total analyzed: {analyzed}")
    print(f"   Intelligence posts: {intelligence_posts}")
    print(f"   Intelligence rate: {intelligence_posts/analyzed*100:.1f}%")

if __name__ == "__main__":
    main()
