#!/usr/bin/env python3
import json
from deep_translator import GoogleTranslator
from langdetect import detect
import time

input_file = 'telegram_gru_dutch_20251119_084300.json'
output_file = 'telegram_gru_dutch_20251119_084300_translated.json'

print("Loading messages...")
with open(input_file, 'r') as f:
    messages = json.load(f)

print(f"Loaded {len(messages)} messages")
print("Starting translation...\n")

translated = 0
for i, msg in enumerate(messages, 1):
    content = msg.get('content', '')
    if not content:
        continue

    try:
        lang = detect(content)
        if lang == 'en':
            continue

        translator = GoogleTranslator(source=lang, target='en')
        translation = translator.translate(content[:4500])

        msg['content_english'] = translation
        msg['original_language'] = lang
        msg['translation_note'] = f"(Translated to English from {lang.upper()})"

        translated += 1
        print(f"[{translated}/{i}] @{msg['channel']} ({lang}→en)")
        time.sleep(0.3)

    except:
        pass

print(f"\nSaving {translated} translations...")
with open(output_file, 'w') as f:
    json.dump(messages, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Saved to: {output_file}")
