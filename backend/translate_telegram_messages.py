#!/usr/bin/env python3
"""
Translate Telegram Messages to English
Adds English translations to all non-English messages
"""

import json
import sys
from pathlib import Path
from deep_translator import GoogleTranslator
import time
from langdetect import detect, LangDetectException

def detect_language(text):
    """Detect language of text"""
    try:
        return detect(text)
    except LangDetectException:
        return 'unknown'

def translate_message(text, source_lang):
    """Translate text to English"""
    if not text or len(text.strip()) == 0:
        return None

    # Skip if already English
    if source_lang == 'en':
        return None

    try:
        translator = GoogleTranslator(source=source_lang, target='en')
        # Translate in chunks if text is too long
        if len(text) > 4500:
            # Split by paragraphs
            paragraphs = text.split('\n\n')
            translated_parts = []
            for para in paragraphs:
                if para.strip():
                    translated = translator.translate(para[:4500])
                    translated_parts.append(translated)
                    time.sleep(0.5)  # Rate limiting
            return '\n\n'.join(translated_parts)
        else:
            translated = translator.translate(text)
            time.sleep(0.3)  # Rate limiting
            return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def main():
    """Main translation pipeline"""

    # Input file
    input_file = 'telegram_gru_dutch_20251119_084300.json'
    output_file = 'telegram_gru_dutch_20251119_084300_translated.json'

    print("=" * 80)
    print("TELEGRAM MESSAGE TRANSLATION TO ENGLISH")
    print("=" * 80)
    print(f"\n📂 Loading: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)

    print(f"✓ Loaded {len(messages)} messages\n")

    translated_count = 0
    skipped_count = 0

    language_stats = {}

    for i, msg in enumerate(messages, 1):
        content = msg.get('content', '')

        if not content or len(content.strip()) == 0:
            skipped_count += 1
            continue

        # Detect language
        lang = detect_language(content)
        language_stats[lang] = language_stats.get(lang, 0) + 1

        if lang == 'en':
            skipped_count += 1
            continue

        # Translate
        print(f"[{i}/{len(messages)}] Translating @{msg['channel']} ({lang} → en)...", end='')

        translation = translate_message(content, lang)

        if translation:
            msg['content_english'] = translation
            msg['original_language'] = lang
            msg['translation_note'] = f"(Translated to English from {lang.upper()})"
            translated_count += 1
            print(" ✓")
        else:
            print(" ⚠️ Failed")
            skipped_count += 1

    # Save translated data
    print(f"\n💾 Saving to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("TRANSLATION COMPLETE")
    print("=" * 80)
    print(f"\n✅ Translated: {translated_count} messages")
    print(f"⏭️  Skipped: {skipped_count} messages (already English or empty)")

    print(f"\n📊 Language breakdown:")
    for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {lang}: {count} messages")

    print(f"\n🎯 Output: {output_file}")
    print("   Use this file in the frontend for English translations\n")

if __name__ == '__main__':
    main()
