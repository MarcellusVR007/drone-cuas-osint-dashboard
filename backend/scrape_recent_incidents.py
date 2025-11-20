#!/usr/bin/env python3
"""
Recent Incident Scraper - Zoekt nieuwe drone incidenten in het nieuws
Ondersteunt: NL, BE, DE, FR, UK
"""

import anthropic
import os
from datetime import datetime, timedelta

def search_news_incidents(countries=['NL', 'BE', 'DE', 'FR', 'UK'], days_back=14):
    """Zoek nieuwe drone incidenten in het nieuws"""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    prompt = f"""Je bent een OSINT analist die drone incidenten verzamelt uit het nieuws.

Zoek naar RECENTE drone incidenten in de volgende landen: {', '.join(countries)}
Periode: {start_date.strftime('%Y-%m-%d')} tot {end_date.strftime('%Y-%m-%d')}

Zoek naar:
- Drone waarnemingen bij militaire bases, vliegvelden, kritieke infrastructuur
- Drone crashes of neergestorte drones
- Drone intercepties door autoriteiten
- Verdachte drone activiteiten
- Drone detecties door radar/sensoren

Voor elk incident, geef:
1. **Datum**: Wanneer vond het plaats? (YYYY-MM-DD)
2. **Locatie**: Specifieke plaats (stad, basis, vliegveld)
3. **Land**: {', '.join(countries)}
4. **Beschrijving**: Korte samenvatting (2-3 zinnen)
5. **Bron**: Nieuwsbron en URL indien beschikbaar
6. **Type**: Waarneming/Crash/Interceptie/Detectie
7. **Betrouwbaarheid**: LOW/MEDIUM/HIGH

Focus ALLEEN op échte, recent gepubliceerde nieuwsberichten.
Geen speculatie, alleen feiten uit betrouwbare bronnen.

Formaat output als een lijst met elk incident duidelijk genummerd."""

    print(f"\n🔍 Zoeken naar incidenten in {', '.join(countries)} (laatste {days_back} dagen)...")
    print(f"📅 Periode: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}\n")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text

    print("=" * 80)
    print("GEVONDEN INCIDENTEN:")
    print("=" * 80)
    print(response)
    print("=" * 80)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/incidents_scan_{timestamp}.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Incident Scan Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Countries: {', '.join(countries)}\n")
        f.write(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(response)

    print(f"\n💾 Results saved to: {output_file}")

    return response, output_file

if __name__ == "__main__":
    import sys

    # Check if specific countries were requested
    if len(sys.argv) > 1:
        countries = sys.argv[1].split(',')
    else:
        countries = ['NL', 'BE', 'DE', 'FR', 'UK']

    # Check if days_back was specified
    if len(sys.argv) > 2:
        days_back = int(sys.argv[2])
    else:
        days_back = 14

    try:
        search_news_incidents(countries, days_back)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
