"""
Intelligence Analysis API Router

Exposes advanced intelligence features:
- Article headline scraping from news sources
- Sentiment analysis on articles
- Fact-checking verification
- Credibility assessment

Endpoints:
- GET /api/intelligence/articles - Search for articles about incident
- POST /api/intelligence/analyze-sentiment - Analyze sentiment of text
- POST /api/intelligence/verify-claim - Verify a factual claim
- GET /api/intelligence/assess-incident - Assess incident credibility
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.database import get_db
from backend.models import Incident, RestrictedArea
from backend.article_scraper import get_article_scraper, Article
from backend.sentiment_analyzer import get_sentiment_analyzer
from backend.fact_checker import get_fact_checker

router = APIRouter()


class ArticleSearchRequest(BaseModel):
    incident_title: str
    country: Optional[str] = None
    limit: Optional[int] = 10


class SentimentAnalysisRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


class FactCheckRequest(BaseModel):
    claim: str


class IncidentCredibilityRequest(BaseModel):
    incident_id: int
    custom_description: Optional[str] = None


@router.get("/articles/search")
async def search_articles_by_keyword(
    query: str = Query(..., min_length=3, alias="query"),
    country: Optional[str] = "NL",
    limit: int = Query(10, ge=1, le=50),
    language: Optional[str] = "en"
):
    """
    Search for articles by keyword.

    Returns articles from trusted sources containing the keyword.
    """
    scraper = get_article_scraper()

    articles = scraper.search_incident_articles(
        incident_title=query,
        country=country,
        limit=limit,
        use_cache=True
    )

    analyzer = get_sentiment_analyzer()
    articles_with_analysis = []

    for article in articles:
        sentiment = analyzer.analyze_article(
            title=article.title,
            summary=article.summary,
            language=article.language
        )

        article_dict = article.to_dict()
        article_dict["sentiment"] = sentiment["sentiment"]
        article_dict["bias"] = sentiment["bias"]
        articles_with_analysis.append(article_dict)

    return {
        "query": query,
        "country": country,
        "articles_found": len(articles_with_analysis),
        "articles": articles_with_analysis,
        "search_date": datetime.utcnow().isoformat()
    }


@router.get("/articles/{incident_id}")
async def get_incident_articles(
    incident_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get news articles about a specific incident.

    Scrapes headlines from trusted sources in that country.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get country code
    country = None
    if incident.restricted_area_id:
        area = db.query(RestrictedArea).filter(
            RestrictedArea.id == incident.restricted_area_id
        ).first()
        if area:
            country = area.country

    if not country:
        raise HTTPException(status_code=400, detail="Incident location not linked to restricted area")

    # Scrape articles
    scraper = get_article_scraper()
    articles = scraper.search_incident_articles(
        incident_title=incident.title,
        country=country,
        limit=limit
    )

    # Analyze sentiment for each article
    analyzer = get_sentiment_analyzer()
    articles_with_sentiment = []

    for article in articles:
        sentiment = analyzer.analyze_article(
            title=article.title,
            summary=article.summary,
            language=article.language
        )

        article_dict = article.to_dict()
        article_dict["sentiment"] = sentiment["sentiment"]
        article_dict["bias"] = sentiment["bias"]
        articles_with_sentiment.append(article_dict)

    return {
        "incident_id": incident_id,
        "incident_title": incident.title,
        "country": country,
        "articles_found": len(articles_with_sentiment),
        "articles": articles_with_sentiment,
        "search_date": datetime.utcnow().isoformat()
    }


@router.post("/analyze-sentiment")
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """
    Analyze sentiment and bias in text.

    Returns:
    - Sentiment score (-1 to 1)
    - Bias indicators (alarmist, sensational, etc.)
    - Trustworthiness score
    """
    analyzer = get_sentiment_analyzer()

    analysis = analyzer.analyze_article(
        title=request.text[:100],  # Use first 100 chars as title
        summary=request.text,
        language=request.language
    )

    return {
        "text": request.text[:200],  # Return excerpt
        "language": request.language,
        "sentiment": analysis["sentiment"],
        "bias": analysis["bias"],
        "trustworthiness_score": analysis["trustworthiness_score"],
        "analysis_date": datetime.utcnow().isoformat()
    }


@router.post("/verify-claim")
async def verify_claim(request: FactCheckRequest):
    """
    Verify a factual claim using fact-checking services.

    Integrates with:
    - Snopes
    - AFP Fact Check
    - Full Fact
    - Manual database of 800+ debunked claims

    Returns verification status and explanation.
    """
    checker = get_fact_checker()

    result = checker.verify_claim(request.claim)

    if not result:
        return {
            "claim": request.claim,
            "status": "unverified",
            "message": "No fact-check found for this claim",
            "is_debunked": checker.is_claim_debunked(request.claim),
            "verification_date": datetime.utcnow().isoformat()
        }

    return {
        "claim": request.claim,
        "verification": result.to_dict(),
        "is_debunked": result.status.value in ["false", "mostly_false"],
        "verification_date": datetime.utcnow().isoformat()
    }


@router.post("/assess-incident")
async def assess_incident_credibility(request: IncidentCredibilityRequest, db: Session = Depends(get_db)):
    """
    Comprehensive credibility assessment of an incident.

    Analyzes:
    1. Sentiment of incident description
    2. Potential bias in reporting
    3. Factual claims in description
    4. Overall credibility score
    5. Recommendations for verification

    Returns:
    - Credibility score (0-1)
    - Assessment (Credible, Partially Credible, Questionable)
    - Verified claims
    - Flags for investigation
    """
    incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Use custom description if provided, otherwise use incident description
    description = request.custom_description or incident.description
    title = incident.title

    # Analyze sentiment
    analyzer = get_sentiment_analyzer()
    sentiment_analysis = analyzer.analyze_article(title, description, language="en")

    # Verify claims
    checker = get_fact_checker()
    credibility_assessment = checker.assess_incident_credibility(
        title,
        description,
        incident.details
    )

    # Combine assessments
    combined_credibility = (
        credibility_assessment['credibility_score'] * 0.6 +  # Fact-checking weight
        (1 - sentiment_analysis['bias']['overall_bias_score']) * 0.4  # Bias weight
    )

    # Identify flags
    flags = []
    if sentiment_analysis['bias']['overall_bias_score'] > 0.7:
        flags.append("⚠️ High bias detected in reporting")
    if sentiment_analysis['sentiment']['label'] == 'negative':
        flags.append("⚠️ Heavily negative tone (possible exaggeration)")
    if credibility_assessment['credibility_score'] < 0.5:
        flags.append("⚠️ Multiple unverified claims detected")
    if checker.is_claim_debunked(title + " " + description):
        flags.append("🚨 Contains debunked claims")

    # Recommendations
    recommendations = []
    if len(credibility_assessment['verifications']) < 3:
        recommendations.append("Gather more sources to verify claims")
    if sentiment_analysis['bias']['alarmist'] > 0.5:
        recommendations.append("Check if threat level is exaggerated")
    if sentiment_analysis['sentiment']['score'] < -0.5:
        recommendations.append("Seek balanced reporting from multiple sources")
    if not incident.identification_confidence or incident.identification_confidence < 0.7:
        recommendations.append("Improve drone type identification")

    return {
        "incident_id": request.incident_id,
        "incident_title": title,
        "credibility_score": combined_credibility,
        "credibility_assessment": credibility_assessment['assessment'],
        "sentiment_analysis": sentiment_analysis,
        "fact_checks": credibility_assessment['verifications'],
        "red_flags": flags,
        "recommendations": recommendations,
        "analysis_summary": {
            "total_claims_identified": credibility_assessment['claims_verified'],
            "verified_claims": len([v for v in credibility_assessment['verifications'] if v['status'] in ['verified', 'mostly_true']]),
            "disputed_claims": len([v for v in credibility_assessment['verifications'] if v['status'] in ['mixed', 'disputed']]),
            "false_claims": len([v for v in credibility_assessment['verifications'] if v['status'] in ['false', 'mostly_false']]),
        },
        "analysis_date": datetime.utcnow().isoformat()
    }


@router.get("/debunked-claims")
async def get_debunked_drone_claims():
    """
    Get list of commonly debunked drone-related claims.

    Useful for fact-checking user reports and incident descriptions.
    """
    checker = get_fact_checker()
    claims = checker.get_debunked_claims()

    return {
        "total_debunked_claims": len(claims),
        "debunked_claims": claims,
        "note": "These claims have been verified as false or mostly false by fact-checkers",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.post("/compare-sources")
async def compare_sources_sentiment(articles: List[dict]):
    """
    Compare sentiment across multiple articles from different sources.

    Helps identify bias and trustworthiness differences between sources.
    """
    analyzer = get_sentiment_analyzer()

    comparison = analyzer.compare_sources(articles)

    return {
        "source_comparison": comparison,
        "analysis_date": datetime.utcnow().isoformat()
    }
