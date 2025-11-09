"""
Source Recommendation Engine

For each incident, recommends trusted local sources from the incident's country
that would likely cover this event.

Endpoints:
- GET /api/incidents/{incident_id}/recommended-sources
- GET /api/incidents/{incident_id}/search-sources
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from backend.database import get_db
from backend.models import Incident, RestrictedArea
from backend.trusted_sources import get_trusted_sources_for_country
import urllib.parse

router = APIRouter()


class RecommendedSource(BaseModel):
    name: str
    url: str
    credibility: float
    category: str  # military, authority, newspaper, news_agency, sensor
    search_url: Optional[str] = None  # URL for searching this incident


class SourceRecommendationResponse(BaseModel):
    incident_id: int
    incident_title: str
    location_country: str
    location_name: str
    recommended_sources: List[RecommendedSource]
    search_tips: Optional[str] = None


@router.get("/{incident_id}/recommended-sources", response_model=SourceRecommendationResponse)
async def get_recommended_sources(incident_id: int, db: Session = Depends(get_db)):
    """
    Get recommended local sources for an incident based on its location country.

    This endpoint analyzes the incident's geographic location and recommends
    the most credible local sources from that country that would likely have
    covered this event.

    For example:
    - Incident at Dutch air base → Recommends De Volkskrant, NRC, NOS (Netherlands)
    - Incident at Belgian airport → Recommends De Standaard, VRT, RTBF (Belgium)
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get the country from the restricted area
    country_code = None
    location_name = "Unknown Location"

    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            country_code = area.country
            location_name = area.name

    if not country_code:
        raise HTTPException(
            status_code=400,
            detail="Incident location not linked to restricted area. Cannot recommend sources."
        )

    # Get all trusted sources for this country, sorted by credibility
    all_sources = get_trusted_sources_for_country(country_code)

    # Prioritize sources by category
    priority_order = [
        "official_military",
        "official_authority",
        "quality_newspaper",
        "news_agency",
        "specialized_intel",
        "sensor_network",
        "local_quality_news",
    ]

    # Organize sources by category for the incident
    recommended = []

    for source in all_sources:
        search_query = _build_search_query(incident.title, source['name'], country_code)

        rec_source = RecommendedSource(
            name=source['name'],
            url=source['url'],
            credibility=source['credibility'],
            category=_categorize_source(source),
            search_url=search_query
        )
        recommended.append(rec_source)

    # Sort by credibility (highest first)
    recommended.sort(key=lambda x: x.credibility, reverse=True)

    # Generate search tips
    search_tips = _generate_search_tips(incident.title, country_code)

    return SourceRecommendationResponse(
        incident_id=incident_id,
        incident_title=incident.title,
        location_country=country_code,
        location_name=location_name,
        recommended_sources=recommended,
        search_tips=search_tips
    )


@router.get("/{incident_id}/search-sources")
async def search_incident_in_sources(
    incident_id: int,
    db: Session = Depends(get_db),
    keyword: Optional[str] = None
):
    """
    Generate search links for the incident in trusted local sources.

    Returns clickable search URLs for:
    - Google News search in local language
    - News archive searches
    - Government websites
    - Airport/military base websites

    Example:
    GET /api/incidents/1/search-sources?keyword="drone+gilze+rijen"
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get country
    country_code = None
    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            country_code = area.country

    if not country_code:
        raise HTTPException(status_code=400, detail="Location country not determined")

    # Build search URLs
    search_keyword = keyword or incident.title
    search_urls = _build_search_urls(incident.title, search_keyword, country_code)

    return {
        "incident_id": incident_id,
        "incident_title": incident.title,
        "country": country_code,
        "search_keyword": search_keyword,
        "search_urls": search_urls,
        "how_to_use": "Open these URLs to search for news articles about this incident"
    }


def _categorize_source(source: dict) -> str:
    """Categorize a source for display"""
    name = source.get('name', '').lower()

    if 'ministry' in name or 'air force' in name or 'military' in name or 'defense' in name:
        return 'official_military'
    elif 'authority' in name or 'airport' in name or 'easa' in name or 'caa' in name:
        return 'official_authority'
    elif any(x in name for x in ['tv', 'news', 'rtbf', 'vrt', 'orf', 'dr', 'rtve', 'nos', 'err', 'lrt']):
        return 'news_agency'
    elif any(x in name for x in ['senhive', 'flightradar', 'ads-b', 'adsb']):
        return 'sensor_network'
    elif 'janes' in name or 'intelligence' in name:
        return 'specialized_intel'
    else:
        return 'quality_newspaper'


def _build_search_query(incident_title: str, source_name: str, country_code: str) -> str:
    """Build a search query for this incident on a source's website"""
    keywords = incident_title.replace(',', ' ').split()[:5]  # First 5 words
    search_term = ' '.join(keywords)

    # Map country to language for search
    language_map = {
        'BE': 'nl',  # Dutch (Belgium)
        'NL': 'nl',  # Dutch
        'DE': 'de',  # German
        'FR': 'fr',  # French
        'PL': 'pl',  # Polish
        'EE': 'et',  # Estonian
        'LT': 'lt',  # Lithuanian
        'DK': 'da',  # Danish
        'ES': 'es',  # Spanish
        'AT': 'de',  # German (Austria)
    }

    lang = language_map.get(country_code, 'en')
    search_encoded = urllib.parse.quote(search_term)

    # Build Google News search
    return f"https://news.google.com/search?q={search_encoded}&gl={country_code.lower()}&hl={lang}"


def _build_search_urls(incident_title: str, search_keyword: str, country_code: str) -> dict:
    """Build multiple search URLs for finding related articles"""
    encoded = urllib.parse.quote(search_keyword)

    urls = {
        "google_news": f"https://news.google.com/search?q={encoded}",
        "google_search": f"https://www.google.com/search?q={encoded}+drone",
    }

    # Add country-specific searches
    if country_code == 'NL':
        urls.update({
            "nos_news": f"https://nos.nl/zoeken/?q={encoded}",
            "volkskrant": f"https://www.volkskrant.nl/search/{encoded}",
            "nrc": f"https://www.nrc.nl/search/{encoded}",
        })
    elif country_code == 'BE':
        urls.update({
            "vrt": f"https://www.vrt.be/vrtnws/nl/search/?q={encoded}",
            "standaard": f"https://www.standaard.be/search/{encoded}",
            "demorgen": f"https://www.demorgen.be/search/{encoded}",
        })
    elif country_code == 'DE':
        urls.update({
            "tagesschau": f"https://www.tagesschau.de/suche/{encoded}",
            "spiegel": f"https://www.spiegel.de/suche/{encoded}",
        })
    elif country_code == 'FR':
        urls.update({
            "france24": f"https://www.france24.com/fr/search/{encoded}",
            "lemonde": f"https://www.lemonde.fr/recherche/?keywords={encoded}",
        })

    return urls


def _generate_search_tips(incident_title: str, country_code: str) -> str:
    """Generate helpful tips for finding articles about this incident"""
    keywords = incident_title.split()[:3]
    location_keyword = " ".join(keywords)

    language_tips = {
        'NL': f"Zoek naar '{location_keyword} drone' in Nederlandse nieuwsbronnen",
        'BE': f"Zoek naar '{location_keyword} drone' in Belgische media (nl/fr)",
        'DE': f"Suchen Sie nach '{location_keyword} Drohne' in deutscher Presse",
        'FR': f"Recherchez '{location_keyword} drone' dans les médias français",
        'PL': f"Poszukaj '{location_keyword} dron' w polskich mediach",
        'EE': f"Otsi '{location_keyword} drooni' Eesti meediast",
        'LT': f"Ieškoti '{location_keyword} dronas' Lietuvos žiniasklaidoje",
        'DK': f"Søg efter '{location_keyword} drone' i danske medier",
        'ES': f"Busca '{location_keyword} dron' en medios españoles",
        'AT': f"Suchen Sie nach '{location_keyword} Drohne' in österreichischer Presse",
    }

    return language_tips.get(country_code, f"Search for '{location_keyword} drone' in local news sources")
