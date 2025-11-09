"""
Trusted Sources Framework for EU OSINT CUAS Dashboard

This module defines trusted news sources, agencies, and intelligence organizations
by country and category. Each source is ranked by credibility and relevance to
drone incident reporting.

Used for:
1. Source validation when adding incidents
2. Link checking against trusted domains only
3. Recommendation engine for incidents with missing sources
4. Prevention of unreliable sources (non-EU bias)
"""

# Credibility levels
CREDIBILITY_SCORES = {
    "official_military": 0.99,      # NATO, government defense agencies
    "official_authority": 0.95,      # Government aviation, civil authorities
    "sensor_network": 0.95,          # Senhive, radar, ADS-B networks
    "established_news": 0.85,        # Major international news agencies
    "quality_newspaper": 0.80,       # Trusted quality newspapers per country
    "aviation_authority": 0.75,      # EASA, national CAAs
    "specialized_intel": 0.80,       # Janes, military forums
    "local_quality_news": 0.70,      # Reputable local/regional news
}

# Trusted sources by country
TRUSTED_SOURCES_BY_COUNTRY = {
    "BE": {  # Belgium
        "official_military": [
            {"name": "Belgian Ministry of Defence", "url": "https://www.mil.be/", "credibility": 0.99},
            {"name": "Belgian Royal Air Force (Orgaan)", "url": "https://www.mil.be/en/military-component/royal-air-force", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Belgian Federal Civil Aviation Authority", "url": "https://www.mobilit.fgov.be/en", "credibility": 0.95},
            {"name": "Port of Antwerp Authority", "url": "https://www.portofantwerp.com/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "De Standaard", "url": "https://www.standaard.be/", "credibility": 0.80},
            {"name": "De Morgen", "url": "https://www.demorgen.be/", "credibility": 0.78},
            {"name": "VRT News (Flemish TV)", "url": "https://www.vrt.be/", "credibility": 0.82},
            {"name": "RTBF News (Walloon TV)", "url": "https://www.rtbf.be/", "credibility": 0.82},
            {"name": "Flanders News (English)", "url": "https://www.flandersnews.be/", "credibility": 0.75},
        ],
    },
    "NL": {  # Netherlands
        "official_military": [
            {"name": "Dutch Ministry of Defence", "url": "https://www.defensie.nl/", "credibility": 0.99},
            {"name": "Royal Netherlands Air Force (KLu)", "url": "https://www.defensie.nl/english/organisation/klu", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Amsterdam Airport Schiphol Authority", "url": "https://www.schiphol.nl/", "credibility": 0.95},
            {"name": "Dutch Civil Aviation Authority (ILT)", "url": "https://www.ilent.nl/", "credibility": 0.95},
        ],
        "quality_newspaper": [
            {"name": "NOS News (Dutch TV)", "url": "https://nos.nl/", "credibility": 0.85},
            {"name": "NRC Handelsblad", "url": "https://www.nrc.nl/", "credibility": 0.83},
            {"name": "De Volkskrant", "url": "https://www.volkskrant.nl/", "credibility": 0.82},
            {"name": "AD.nl (Algemeen Dagblad)", "url": "https://www.ad.nl/", "credibility": 0.78},
            {"name": "RTL News", "url": "https://www.rtlnieuws.nl/", "credibility": 0.80},
        ],
    },
    "DE": {  # Germany
        "official_military": [
            {"name": "German Ministry of Defence (Bundesverteidigungsministerium)", "url": "https://www.bmvg.de/", "credibility": 0.99},
            {"name": "Luftwaffe (German Air Force)", "url": "https://www.luftwaffe.de/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "German Civil Aviation Authority (LBA)", "url": "https://www.lba.de/", "credibility": 0.95},
            {"name": "Berlin Brandenburg Airport", "url": "https://www.berlin-airport.de/", "credibility": 0.90},
            {"name": "Munich Airport", "url": "https://www.munich-airport.de/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "Tagesschau (German TV News)", "url": "https://www.tagesschau.de/", "credibility": 0.85},
            {"name": "Spiegel Online", "url": "https://www.spiegel.de/", "credibility": 0.83},
            {"name": "Die Welt", "url": "https://www.welt.de/", "credibility": 0.82},
            {"name": "Frankfurter Allgemeine (FAZ)", "url": "https://www.faz.net/", "credibility": 0.82},
            {"name": "Süddeutsche Zeitung", "url": "https://www.sueddeutsche.de/", "credibility": 0.82},
            {"name": "Deutsche Presse-Agentur (dpa)", "url": "https://www.dpa.com/", "credibility": 0.85},
        ],
    },
    "FR": {  # France
        "official_military": [
            {"name": "French Ministry of Defence (Ministère de la Défense)", "url": "https://www.defense.gouv.fr/", "credibility": 0.99},
            {"name": "French Air Force (Armée de l'Air)", "url": "https://www.air-et-cosmos.com/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "French Civil Aviation Authority (DGAC)", "url": "https://www.dgac.gouv.fr/", "credibility": 0.95},
            {"name": "Aéroports de Paris", "url": "https://www.parisaeroport.fr/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "France 24 News (English/French)", "url": "https://www.france24.com/", "credibility": 0.84},
            {"name": "Le Monde", "url": "https://www.lemonde.fr/", "credibility": 0.83},
            {"name": "Le Figaro", "url": "https://www.lefigaro.fr/", "credibility": 0.82},
            {"name": "Libération", "url": "https://www.liberation.fr/", "credibility": 0.80},
            {"name": "Agence France-Presse (AFP)", "url": "https://www.afp.com/", "credibility": 0.85},
        ],
    },
    "PL": {  # Poland
        "official_military": [
            {"name": "Polish Ministry of Defence", "url": "https://www.mon.gov.pl/", "credibility": 0.99},
            {"name": "Polish Air Force (Siły Powietrzne)", "url": "https://www.wp.mil.pl/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Polish Civil Aviation Authority (UACL)", "url": "https://www.ulc.gov.pl/", "credibility": 0.95},
            {"name": "Polish Air Navigation Services", "url": "https://www.pansa.pl/", "credibility": 0.95},
        ],
        "quality_newspaper": [
            {"name": "TVN24 News", "url": "https://www.tvn24.pl/", "credibility": 0.80},
            {"name": "Onet News", "url": "https://wiadomosci.onet.pl/", "credibility": 0.78},
            {"name": "Polish Press Agency (PAP)", "url": "https://www.pap.pl/", "credibility": 0.82},
            {"name": "Gazeta Wyborcza", "url": "https://wyborcza.pl/", "credibility": 0.80},
        ],
    },
    "EE": {  # Estonia
        "official_military": [
            {"name": "Estonian Ministry of Defence", "url": "https://www.kaitseministeerium.ee/", "credibility": 0.99},
            {"name": "Estonian Air Force (Eesti Õhuvägi)", "url": "https://www.mil.ee/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Estonian Civil Aviation Administration", "url": "https://www.ecaa.ee/", "credibility": 0.95},
        ],
        "quality_newspaper": [
            {"name": "ERR News (Estonian TV)", "url": "https://www.err.ee/", "credibility": 0.82},
            {"name": "Delfi News", "url": "https://www.delfi.ee/", "credibility": 0.78},
            {"name": "Postimees", "url": "https://www.postimees.ee/", "credibility": 0.78},
        ],
    },
    "LT": {  # Lithuania
        "official_military": [
            {"name": "Lithuanian Ministry of Defence", "url": "https://kam.lt/", "credibility": 0.99},
            {"name": "Lithuanian Air Force (Ore Pajegos)", "url": "https://www.kam.lt/en/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Lithuanian Civil Aviation Authority (CAA)", "url": "https://www.caa.lt/", "credibility": 0.95},
            {"name": "Vilnius Airport Authority", "url": "https://www.vilnius-airport.lt/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "LRT News (Lithuanian TV)", "url": "https://www.lrt.lt/", "credibility": 0.82},
            {"name": "Delfi.lt News", "url": "https://www.delfi.lt/", "credibility": 0.78},
            {"name": "15min.lt", "url": "https://www.15min.lt/", "credibility": 0.75},
        ],
    },
    "DK": {  # Denmark
        "official_military": [
            {"name": "Danish Ministry of Defence", "url": "https://www.fmn.dk/", "credibility": 0.99},
            {"name": "Royal Danish Air Force", "url": "https://www.forsvarets.dk/da/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Danish Civil Aviation and Railway Authority (Trafikstyrelsen)", "url": "https://www.trafikstyrelsen.dk/", "credibility": 0.95},
            {"name": "Copenhagen Airport Authority", "url": "https://www.cph.dk/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "DR News (Danish TV)", "url": "https://www.dr.dk/", "credibility": 0.85},
            {"name": "Politiken", "url": "https://politiken.dk/", "credibility": 0.82},
            {"name": "Jyllands-Posten", "url": "https://jyllands-posten.dk/", "credibility": 0.80},
        ],
    },
    "ES": {  # Spain
        "official_military": [
            {"name": "Spanish Ministry of Defence", "url": "https://www.defensa.gob.es/", "credibility": 0.99},
            {"name": "Spanish Air Force (Ejército del Aire)", "url": "https://www.ejercitodelaire.es/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "AENA Spanish Airports", "url": "https://www.aena.es/", "credibility": 0.95},
            {"name": "Spanish Civil Aviation Authority (AESA)", "url": "https://www.aesa.gob.es/", "credibility": 0.95},
        ],
        "quality_newspaper": [
            {"name": "EFE News Agency (Spanish)", "url": "https://www.efe.com/", "credibility": 0.84},
            {"name": "RTVE.es (Spanish TV)", "url": "https://www.rtve.es/", "credibility": 0.83},
            {"name": "El País", "url": "https://elpais.com/", "credibility": 0.82},
            {"name": "El Mundo", "url": "https://www.elmundo.es/", "credibility": 0.80},
        ],
    },
    "AT": {  # Austria
        "official_military": [
            {"name": "Austrian Ministry of Defence", "url": "https://www.bundesheer.at/", "credibility": 0.99},
            {"name": "Austrian Air Force", "url": "https://www.bundesheer.at/", "credibility": 0.99},
        ],
        "official_authority": [
            {"name": "Austrian Civil Aviation Authority (FCCB)", "url": "https://www.fccb.at/", "credibility": 0.95},
            {"name": "Vienna International Airport", "url": "https://www.viennaairport.com/", "credibility": 0.90},
        ],
        "quality_newspaper": [
            {"name": "ORF News (Austrian TV)", "url": "https://orf.at/", "credibility": 0.83},
            {"name": "Die Presse", "url": "https://www.diepresse.com/", "credibility": 0.82},
            {"name": "Der Standard", "url": "https://derstandard.at/", "credibility": 0.80},
        ],
    },
}

# International news agencies (high credibility, EU-focused)
INTERNATIONAL_AGENCIES = [
    {"name": "Reuters", "url": "https://www.reuters.com/", "credibility": 0.85, "categories": ["news"]},
    {"name": "Agence France-Presse (AFP)", "url": "https://www.afp.com/", "credibility": 0.85, "categories": ["news"]},
    {"name": "BBC News", "url": "https://www.bbc.com/news", "credibility": 0.84, "categories": ["news"]},
    {"name": "Associated Press (AP)", "url": "https://apnews.com/", "credibility": 0.83, "categories": ["news"]},
    {"name": "Deutsche Presse-Agentur (dpa)", "url": "https://www.dpa.com/", "credibility": 0.84, "categories": ["news"]},
    {"name": "European Commission (EU)", "url": "https://ec.europa.eu/", "credibility": 0.95, "categories": ["authority"]},
    {"name": "EASA (European Union Aviation Safety Agency)", "url": "https://www.easa.europa.eu/", "credibility": 0.95, "categories": ["authority"]},
    {"name": "Eurocontrol", "url": "https://www.eurocontrol.int/", "credibility": 0.95, "categories": ["authority"]},
]

# Specialized intelligence sources
SPECIALIZED_SOURCES = [
    {"name": "Janes Intelligence & Insight", "url": "https://www.janes.com/", "credibility": 0.98, "categories": ["sigint", "military_analysis"]},
    {"name": "Senhive", "url": "https://senhive.com/", "credibility": 0.95, "categories": ["drone_detection", "sensor"]},
    {"name": "ADS-B Exchange", "url": "https://adsbexchange.com/", "credibility": 0.90, "categories": ["adsb"]},
    {"name": "Flightradar24", "url": "https://www.flightradar24.com/", "credibility": 0.92, "categories": ["adsb"]},
    {"name": "Military Aviation Forums", "url": "https://www.militaryaviationforum.com/", "credibility": 0.70, "categories": ["community"]},
]

# BLOCKED sources (not to be used)
BLOCKED_SOURCES = [
    "washingtonpost.com",  # US bias
    "nytimes.com",         # US bias
    "cnn.com",            # US bias, sensationalist
    "foxnews.com",        # US bias, sensationalist
    "theguardian.com",    # Some coverage OK but generally left-leaning, secondary only
    "dailymail.co.uk",    # Tabloid, unreliable
    "breitbart.com",      # Extremist, unreliable
    "infowars.com",       # Conspiracy, unreliable
    "twitter.com",        # Social media, unverified
    "x.com",              # Social media, unverified
    "facebook.com",       # Social media, unverified
    "reddit.com",         # Social media, unverified
]

def get_source_credibility_by_country(source_name: str, country_code: str) -> dict:
    """
    Get credibility score and details for a source in a specific country.

    Args:
        source_name: Name of the news source
        country_code: ISO 2-letter country code (e.g., "BE", "NL", "DE")

    Returns:
        dict: {"credibility": float, "url": str, "verified": bool}
    """
    if country_code in TRUSTED_SOURCES_BY_COUNTRY:
        country_sources = TRUSTED_SOURCES_BY_COUNTRY[country_code]
        for category in country_sources.values():
            for source in category:
                if source_name.lower() in source['name'].lower():
                    return {"credibility": source['credibility'], "url": source['url'], "verified": True}

    # Check international agencies
    for source in INTERNATIONAL_AGENCIES:
        if source_name.lower() in source['name'].lower():
            return {"credibility": source['credibility'], "url": source['url'], "verified": True}

    # Check specialized sources
    for source in SPECIALIZED_SOURCES:
        if source_name.lower() in source['name'].lower():
            return {"credibility": source['credibility'], "url": source['url'], "verified": True}

    return {"credibility": 0.5, "url": None, "verified": False}


def is_source_blocked(url: str) -> bool:
    """Check if a URL domain is in the blocked list"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().replace("www.", "")
    return any(blocked in domain for blocked in BLOCKED_SOURCES)


def get_trusted_sources_for_country(country_code: str) -> list:
    """Get all trusted sources for a specific country"""
    if country_code not in TRUSTED_SOURCES_BY_COUNTRY:
        return []

    sources = []
    for category, items in TRUSTED_SOURCES_BY_COUNTRY[country_code].items():
        sources.extend(items)
    return sorted(sources, key=lambda x: x['credibility'], reverse=True)


def validate_source_url(url: str, country_code: str = None) -> dict:
    """
    Validate a source URL against the trust framework.

    Returns:
        {
            "valid": bool,
            "credibility": float,
            "reason": str,
            "blocked": bool
        }
    """
    if not url:
        return {"valid": False, "credibility": 0, "reason": "No URL provided", "blocked": False}

    # Check if blocked
    if is_source_blocked(url):
        return {"valid": False, "credibility": 0, "reason": "Source is in blocked list (bias/unreliability)", "blocked": True}

    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()

    # Check against all trusted sources
    all_trusted = INTERNATIONAL_AGENCIES + SPECIALIZED_SOURCES
    if country_code and country_code in TRUSTED_SOURCES_BY_COUNTRY:
        for category in TRUSTED_SOURCES_BY_COUNTRY[country_code].values():
            all_trusted.extend(category)

    for source in all_trusted:
        source_domain = urlparse(source['url']).netloc.lower()
        if source_domain in domain or domain in source_domain:
            return {
                "valid": True,
                "credibility": source['credibility'],
                "reason": f"Trusted source: {source['name']}",
                "blocked": False
            }

    return {
        "valid": False,
        "credibility": 0,
        "reason": "Source not in trusted framework",
        "blocked": False
    }


def get_all_trusted_domains() -> list:
    """Get all trusted domains for validation"""
    domains = set()

    # Add international agencies
    for source in INTERNATIONAL_AGENCIES:
        from urllib.parse import urlparse
        domain = urlparse(source['url']).netloc.replace("www.", "")
        domains.add(domain)

    # Add specialized sources
    for source in SPECIALIZED_SOURCES:
        from urllib.parse import urlparse
        domain = urlparse(source['url']).netloc.replace("www.", "")
        domains.add(domain)

    # Add country-specific sources
    for country, categories in TRUSTED_SOURCES_BY_COUNTRY.items():
        for category, sources in categories.items():
            for source in sources:
                from urllib.parse import urlparse
                domain = urlparse(source['url']).netloc.replace("www.", "")
                domains.add(domain)

    return sorted(list(domains))
