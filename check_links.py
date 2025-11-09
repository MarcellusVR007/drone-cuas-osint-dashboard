#!/usr/bin/env python3
"""
Check incident source URLs for validity and EU relevance
"""
import requests
from backend.database import SessionLocal
from backend.models import Incident
from urllib.parse import urlparse
import time

# EU domain patterns
EU_DOMAINS = {
    # News
    'reuters.com': 'Reuters (UK)',
    'bbc.com': 'BBC (UK)',
    'bbc.co.uk': 'BBC (UK)',
    'eur-lex.europa.eu': 'EU Official',
    'europa.eu': 'EU',

    # Military/Defense (EU)
    'defensie.nl': 'Dutch Defence',
    'mil.be': 'Belgian Defence',
    'bundeswehr.de': 'German Defence',
    'defense.gouv.fr': 'French Defence',

    # Aviation
    'eurocontrol.int': 'Eurocontrol',
    'easa.europa.eu': 'EASA (EU)',

    # Tech/Signals
    'adsb.fi': 'ADS-B Exchange',
    'flightradar24.com': 'FlightRadar24',
}

# Non-EU patterns to exclude
NON_EU_DOMAINS = {
    'washingtonpost.com': 'Washington Post (USA)',
    'nytimes.com': 'NY Times (USA)',
    'bbc.com': 'BBC (UK)',  # Actually UK so borderline
    'cnn.com': 'CNN (USA)',
    'foxnews.com': 'Fox News (USA)',
}

def is_eu_domain(url):
    """Check if URL is from EU or EU-relevant source"""
    if not url:
        return None

    try:
        domain = urlparse(url).netloc.lower().replace('www.', '')

        # Check EU domains
        for eu_domain, name in EU_DOMAINS.items():
            if eu_domain in domain:
                return ('EU', name)

        # Check non-EU domains
        for non_eu_domain, name in NON_EU_DOMAINS.items():
            if non_eu_domain in domain:
                return ('NON-EU', name)

        # Unknown
        return ('UNKNOWN', domain)
    except:
        return None

def check_url_status(url):
    """Check if URL is accessible"""
    if not url:
        return None, None

    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code, response.url
    except requests.exceptions.Timeout:
        return 'TIMEOUT', None
    except requests.exceptions.ConnectionError:
        return 'ERROR', None
    except Exception as e:
        return f'ERROR: {type(e).__name__}', None

def main():
    db = SessionLocal()

    try:
        incidents = db.query(Incident).all()

        print("\n" + "="*80)
        print("LINK VALIDATION REPORT")
        print("="*80 + "\n")

        dead_links = []
        non_eu_links = []
        good_links = []

        for i, incident in enumerate(incidents, 1):
            if not incident.source_url:
                continue

            url = incident.source_url
            status, final_url = check_url_status(url)
            region, source_name = is_eu_domain(url) or ('UNKNOWN', 'Unknown')

            # Categorize
            if status == 200:
                good_links.append({
                    'id': incident.id,
                    'url': url,
                    'region': region,
                    'source': source_name
                })
                symbol = '✅'
            elif region == 'NON-EU':
                non_eu_links.append({
                    'id': incident.id,
                    'url': url,
                    'source': source_name,
                    'status': status
                })
                symbol = '❌'
            else:
                dead_links.append({
                    'id': incident.id,
                    'url': url,
                    'status': status,
                    'source': source_name
                })
                symbol = '💀'

            print(f"{symbol} [{i}/{len([inc for inc in incidents if inc.source_url])}] "
                  f"ID {incident.id}: {status} | {region} | {source_name[:40]}")
            time.sleep(0.1)  # Rate limiting

        # Summary
        print("\n" + "="*80)
        print(f"✅ VALID EU LINKS: {len(good_links)}")
        print(f"❌ NON-EU SOURCES: {len(non_eu_links)}")
        print(f"💀 DEAD LINKS: {len(dead_links)}")
        print("="*80 + "\n")

        # Non-EU details
        if non_eu_links:
            print("NON-EU SOURCES TO REMOVE:")
            print("-" * 80)
            for link in non_eu_links:
                print(f"  ID {link['id']}: {link['source']} ({link['status']})")
                print(f"    {link['url'][:70]}...")
            print()

        # Dead links details
        if dead_links:
            print("DEAD LINKS (No longer accessible):")
            print("-" * 80)
            for link in dead_links:
                print(f"  ID {link['id']}: {link['status']} | {link['source']}")
                print(f"    {link['url'][:70]}...")
            print()

        # Recommendations
        print("RECOMMENDATIONS:")
        print("-" * 80)
        print(f"1. Remove {len(non_eu_links)} non-EU sources (not in scope)")
        print(f"2. Fix or remove {len(dead_links)} dead links")
        print(f"3. Keep {len(good_links)} valid EU-relevant sources")

    finally:
        db.close()

if __name__ == "__main__":
    main()
