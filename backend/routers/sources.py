"""
Sources API Router - Trusted sources framework endpoints

Endpoints:
- GET /api/sources/trusted/{country} - Get all trusted sources for a country
- GET /api/sources/validate - Validate a URL against trust framework
- GET /api/sources/all-domains - Get all trusted domains
- GET /api/sources/blocked - Check if URL is blocked
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.trusted_sources import (
    get_trusted_sources_for_country,
    validate_source_url,
    is_source_blocked,
    get_all_trusted_domains,
    BLOCKED_SOURCES,
)
import requests
from datetime import datetime

router = APIRouter()


class SourceValidationRequest(BaseModel):
    url: str
    country: Optional[str] = None


class SourceValidationResponse(BaseModel):
    url: str
    valid: bool
    credibility: float
    reason: str
    blocked: bool
    link_working: Optional[bool] = None


class TrustedSourcesResponse(BaseModel):
    country: str
    sources: List[dict]
    count: int


class AllDomainsResponse(BaseModel):
    total: int
    domains: List[str]


@router.get("/trusted/{country}", response_model=TrustedSourcesResponse)
async def get_trusted_sources(country: str):
    """
    Get all trusted news sources and authorities for a specific country.

    Args:
        country: ISO 2-letter country code (e.g., 'BE', 'NL', 'DE')

    Returns:
        List of trusted sources with credibility scores
    """
    sources = get_trusted_sources_for_country(country.upper())

    return TrustedSourcesResponse(
        country=country.upper(),
        sources=sources,
        count=len(sources)
    )


@router.post("/validate", response_model=SourceValidationResponse)
async def validate_source(request: SourceValidationRequest):
    """
    Validate a source URL against the trust framework.

    Returns credibility score and validation status.
    """
    validation = validate_source_url(request.url, request.country)

    # Try to check if link is actually working
    link_working = None
    if validation["valid"]:
        try:
            response = requests.head(request.url, timeout=5, allow_redirects=True)
            link_working = response.status_code < 400
        except:
            link_working = False

    return SourceValidationResponse(
        url=request.url,
        valid=validation["valid"],
        credibility=validation["credibility"],
        reason=validation["reason"],
        blocked=validation["blocked"],
        link_working=link_working
    )


@router.get("/all-domains", response_model=AllDomainsResponse)
async def get_all_trusted_domains_endpoint():
    """
    Get all trusted domains for validation purposes.

    Useful for client-side validation and autocomplete.
    """
    domains = get_all_trusted_domains()

    return AllDomainsResponse(
        total=len(domains),
        domains=domains
    )


@router.get("/blocked")
async def check_if_blocked(url: str = Query(...)):
    """
    Check if a URL is in the blocked sources list.
    """
    return {
        "url": url,
        "blocked": is_source_blocked(url),
        "blocked_sources": BLOCKED_SOURCES
    }


@router.get("/check-link")
async def check_link_working(url: str = Query(...)):
    """
    Check if a link is currently working (HTTP HEAD request).

    Returns:
        {
            "url": str,
            "working": bool,
            "status_code": int,
            "last_checked": datetime
        }
    """
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        working = response.status_code < 400
        status_code = response.status_code
    except requests.exceptions.Timeout:
        working = False
        status_code = -1
    except requests.exceptions.ConnectionError:
        working = False
        status_code = -2
    except Exception as e:
        working = False
        status_code = -3

    return {
        "url": url,
        "working": working,
        "status_code": status_code,
        "last_checked": datetime.utcnow(),
        "status_meaning": {
            -1: "TIMEOUT",
            -2: "CONNECTION_ERROR",
            -3: "OTHER_ERROR"
        }.get(status_code, "")
    }
