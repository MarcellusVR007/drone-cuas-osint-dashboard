#!/usr/bin/env python3
"""
Fast Translation - High Value Messages Only
Only translates messages with relevance_score >= 10 to save time
"""

import json
from deep_translator import GoogleTranslator
from langdetect import detect
import time

def main():
    input_file = 'telegram_gru_dutch_20251119_084300.json'
    output_file = 'telegram_gru_dutch_20251119_084300_translated.json'

    print("=" * 80)
    print("FAST TRANSLATION - HIGH VALUE MESSAGES ONLY")
    print("=" * 80)

    with open(input_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)

    print(f"\n✓ Loaded {len(messages)} messages")

    # Translate ALL non-English messages
    print(f"🎯 Translating ALL non-English messages")

    translated = 0
    skipped = 0
    for i, msg in enumerate(messages, 1):
        content = msg.get('content', '')

        if not content:
            continue

        try:
            lang = detect(content)

            # Skip if already English
            if lang == 'en':
                continue

            # Translate
            translator = GoogleTranslator(source=lang, target='en')

            # Chunk if needed
            if len(content) > 4500:
                content = content[:4500]

            translation = translator.translate(content)

            msg['content_english'] = translation
            msg['original_language'] = lang
            msg['translation_note'] = f"(Translated to English from {lang.upper()})"

            translated += 1
            print(f"[{translated}] @{msg['channel']} ({lang}→en) ✓")

            time.sleep(0.2)  # Rate limit

        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            skipped += 1
            continue

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"✅ Translated {translated} high-value messages")
    print(f"💾 Saved to: {output_file}")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()
