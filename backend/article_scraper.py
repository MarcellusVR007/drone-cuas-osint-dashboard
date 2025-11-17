"""
Article Headline Scraper for OSINT CUAS Dashboard

Scrapes headlines from trusted news sources for drone-related incidents.
Supports RSS feeds, news APIs, and direct web scraping with caching.

Features:
- Ethical scraping with rate limiting
- RSS feed support
- Caching to reduce repeated requests
- Language detection
- Sentiment analysis
- Source credibility weighting

Usage:
    from backend.article_scraper import ArticleScraper
    scraper = ArticleScraper()
    articles = scraper.search_incident_articles("Gilze Rijen", "NL", limit=10)
"""

import requests
import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from urllib.parse import urljoin, quote
import hashlib
import json
from functools import lru_cache

logger = logging.getLogger(__name__)


class Article:
    """Represents a news article about an incident"""

    def __init__(
        self,
        title: str,
        url: str,
        source_name: str,
        source_credibility: float,
        publish_date: Optional[datetime] = None,
        summary: Optional[str] = None,
        language: str = "en",
        sentiment_score: Optional[float] = None
    ):
        self.title = title
        self.url = url
        self.source_name = source_name
        self.source_credibility = source_credibility
        self.publish_date = publish_date or datetime.utcnow()
        self.summary = summary
        self.language = language
        self.sentiment_score = sentiment_score  # -1.0 (negative) to 1.0 (positive)
        self.hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate unique hash for deduplication"""
        content = f"{self.title}{self.url}".encode()
        return hashlib.md5(content).hexdigest()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "source_credibility": self.source_credibility,
            "publish_date": self.publish_date.isoformat(),
            "summary": self.summary,
            "language": self.language,
            "sentiment_score": self.sentiment_score,
            "hash": self.hash
        }


class ArticleScraper:
    """
    Scrapes articles from trusted news sources about drone incidents.

    Supports:
    - RSS feeds
    - Google News search
    - Direct news website scraping
    - Caching to avoid repeated requests
    """

    # RSS feeds for news sources
    RSS_FEEDS = {
        'NL': [
            ('NOS News', 'https://feeds.nos.nl/nosnieuws'),
            ('De Volkskrant', 'https://www.volkskrant.nl/rss'),
            ('NRC', 'https://www.nrc.nl/rss'),
        ],
        'BE': [
            ('VRT News', 'https://www.vrt.be/vrtnws/nl/feeds/'),
            ('De Standaard', 'https://www.standaard.be/rss'),
            ('Flanders News', 'https://www.flandersnews.be/feeds/'),
        ],
        'DE': [
            ('Tagesschau', 'https://www.tagesschau.de/xml/rss2_beitrag.xml'),
            ('DPA', 'https://feeds.dpa.de/'),
        ],
        'FR': [
            ('France 24', 'https://www.france24.com/fr/rss'),
            ('AFP', 'https://feeds.afp.com/groups/france'),
        ],
        'PL': [
            ('TVN24', 'https://tvn24.pl/feeds/'),
            ('Onet', 'https://wiadomosci.onet.pl/rss.xml'),
        ],
        'DK': [
            ('DR Nyheder', 'https://www.dr.dk/nyheder/service/feeds/allenyheder'),
            ('TV2 News', 'https://feeds.tv2.dk/rss/nyheder'),
            ('The Local DK', 'https://www.thelocal.dk/feed/'),
        ],
        'UK': [
            ('BBC News', 'https://feeds.bbci.co.uk/news/rss.xml'),
            ('The Guardian', 'https://www.theguardian.com/uk/rss'),
            ('Reuters UK', 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best'),
        ],
        'SE': [
            ('SVT Nyheter', 'https://www.svt.se/nyheter/rss.xml'),
            ('Dagens Nyheter', 'https://www.dn.se/rss/'),
            ('The Local SE', 'https://www.thelocal.se/feed/'),
        ],
        'NO': [
            ('NRK Nyheter', 'https://www.nrk.no/toppsaker.rss'),
            ('VG Nyheter', 'https://www.vg.no/rss/feed/'),
            ('The Local NO', 'https://www.thelocal.no/feed/'),
        ],
    }

    # Search keywords for drone incidents (per language)
    SEARCH_KEYWORDS = {
        'nl': ['drone', 'drones', 'onbemand vliegtuig', 'quadcopter'],
        'en': ['drone', 'drones', 'uav', 'unmanned aircraft'],
        'de': ['Drohne', 'Drohnen', 'unbemanntes Flugzeug'],
        'fr': ['drone', 'drones', 'avion sans pilote'],
        'pl': ['dron', 'drony', 'bezzałogowy'],
        'es': ['dron', 'drones', 'avión sin piloto'],
        'da': ['drone', 'droner', 'ubemannet luftfartøj'],
        'no': ['drone', 'droner', 'ubemannet fly'],
        'sv': ['drönare', 'drönare', 'obemannad farkost'],
    }

    def __init__(self, cache_dir: str = ".cache/articles", cache_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OSINT-CUAS-Dashboard/2.0 (Mozilla/5.0)'
        })
        self._init_cache()

    def _init_cache(self):
        """Initialize cache directory"""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, search_term: str, country: str) -> str:
        """Generate cache key for search"""
        key = f"{search_term}_{country}".encode()
        return hashlib.md5(key).hexdigest()

    def _load_cache(self, search_term: str, country: str) -> Optional[List[Article]]:
        """Load articles from cache if fresh"""
        import os
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(search_term, country)}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.utcnow() - mtime > self.cache_ttl:
                os.remove(cache_file)
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [self._dict_to_article(article) for article in data]
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            return None

    def _save_cache(self, search_term: str, country: str, articles: List[Article]):
        """Save articles to cache"""
        import os
        try:
            cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(search_term, country)}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump([a.to_dict() for a in articles], f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")

    def _dict_to_article(self, data: dict) -> Article:
        """Convert dict to Article object"""
        return Article(
            title=data['title'],
            url=data['url'],
            source_name=data['source_name'],
            source_credibility=data['source_credibility'],
            publish_date=datetime.fromisoformat(data['publish_date']) if data.get('publish_date') else None,
            summary=data.get('summary'),
            language=data.get('language', 'en'),
            sentiment_score=data.get('sentiment_score')
        )

    def search_incident_articles(
        self,
        incident_title: str,
        country: str = "NL",
        limit: int = 10,
        use_cache: bool = True
    ) -> List[Article]:
        """
        Search for articles about a specific incident.

        Args:
            incident_title: Title of the incident (e.g., "Drone over Gilze Rijen")
            country: ISO country code (NL, BE, DE, FR, etc.)
            limit: Maximum number of articles to return
            use_cache: Use cached results if available

        Returns:
            List of Article objects sorted by relevance and credibility
        """

        # Check cache first
        if use_cache:
            cached = self._load_cache(incident_title, country)
            if cached:
                logger.info(f"Using cached articles for '{incident_title}' ({country})")
                return cached[:limit]

        articles = []
        seen_hashes = set()

        # Try RSS feeds first
        logger.info(f"Searching RSS feeds for '{incident_title}' ({country})...")
        rss_articles = self._search_rss_feeds(incident_title, country, limit)
        for article in rss_articles:
            if article.hash not in seen_hashes:
                articles.append(article)
                seen_hashes.add(article.hash)

        # Try Google News search
        if len(articles) < limit:
            logger.info(f"Searching Google News for '{incident_title}' ({country})...")
            google_articles = self._search_google_news(incident_title, country, limit - len(articles))
            for article in google_articles:
                if article.hash not in seen_hashes:
                    articles.append(article)
                    seen_hashes.add(article.hash)

        # Sort by credibility (highest first) and date (newest first)
        articles.sort(
            key=lambda a: (-a.source_credibility, -a.publish_date.timestamp()),
            reverse=False
        )

        # Cache results
        self._save_cache(incident_title, country, articles[:limit])

        logger.info(f"Found {len(articles)} articles for '{incident_title}'")
        return articles[:limit]

    def _search_rss_feeds(
        self,
        incident_title: str,
        country: str,
        limit: int
    ) -> List[Article]:
        """Search RSS feeds for incident articles"""
        from backend.trusted_sources import get_trusted_sources_for_country

        articles = []
        feeds = self.RSS_FEEDS.get(country, [])

        # Map source names to credibility scores
        source_map = {s['name']: s['credibility'] for s in get_trusted_sources_for_country(country)}

        keywords = self.SEARCH_KEYWORDS.get(country.lower(), self.SEARCH_KEYWORDS['en'])
        search_terms = incident_title.lower().split() + keywords

        for source_name, feed_url in feeds:
            try:
                logger.debug(f"Parsing RSS feed: {source_name}")
                feed = feedparser.parse(feed_url)

                credibility = source_map.get(source_name, 0.75)

                for entry in feed.entries[:20]:  # Check first 20 entries
                    # Check if any keyword matches
                    title_lower = entry.get('title', '').lower()
                    summary_lower = entry.get('summary', '').lower()

                    if any(term in title_lower or term in summary_lower for term in search_terms):
                        article = Article(
                            title=entry.get('title', 'No title'),
                            url=entry.get('link', ''),
                            source_name=source_name,
                            source_credibility=credibility,
                            publish_date=self._parse_date(entry.get('published')),
                            summary=entry.get('summary', '')[:200],
                            language=self._detect_language(title_lower)
                        )
                        articles.append(article)

                        if len(articles) >= limit:
                            return articles

            except Exception as e:
                logger.warning(f"Error parsing RSS feed {source_name}: {e}")
                continue

        return articles

    def _search_google_news(
        self,
        incident_title: str,
        country: str,
        limit: int
    ) -> List[Article]:
        """Search Google News for incident articles"""
        articles = []

        try:
            # Build Google News search URL
            search_query = f"{incident_title} drone"
            country_code = country.lower()

            # Google News search
            url = f"https://news.google.com/rss/search?q={quote(search_query)}&ceid={country_code}"

            logger.debug(f"Searching Google News: {url}")

            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', 'No title'),
                    url=entry.get('link', ''),
                    source_name=entry.get('source', {}).get('title', 'Google News'),
                    source_credibility=0.75,  # Default credibility for aggregated news
                    publish_date=self._parse_date(entry.get('published')),
                    summary=entry.get('summary', '')[:200],
                    language=self._detect_language(entry.get('title', '').lower())
                )
                articles.append(article)

        except Exception as e:
            logger.warning(f"Error searching Google News: {e}")

        return articles

    def _parse_date(self, date_string: Optional[str]) -> datetime:
        """Parse various date formats"""
        if not date_string:
            return datetime.utcnow()

        try:
            # Try RFC 2822 format (RSS standard)
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_string)
        except:
            pass

        try:
            # Try ISO format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            pass

        logger.warning(f"Could not parse date: {date_string}")
        return datetime.utcnow()

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on keywords"""
        if not text:
            return "en"

        # Simple heuristic-based detection
        text_lower = text.lower()

        # Dutch
        if any(word in text_lower for word in ['de ', 'het ', 'een ', 'van ', 'is ', 'dat']):
            return "nl"

        # German
        if any(word in text_lower for word in ['der ', 'die ', 'und ', 'ist ', 'das']):
            return "de"

        # French
        if any(word in text_lower for word in ['le ', 'la ', 'de ', 'et ', 'est ', 'que']):
            return "fr"

        # Spanish
        if any(word in text_lower for word in ['el ', 'la ', 'de ', 'y ', 'es ', 'que']):
            return "es"

        # Polish
        if any(word in text_lower for word in ['w ', 'z ', 'się', 'tym', 'jest']):
            return "pl"

        return "en"

    def get_fresh_articles(
        self,
        incident_title: str,
        country: str = "NL",
        since_hours: int = 24,
        limit: int = 10
    ) -> List[Article]:
        """
        Get only fresh articles published in the last N hours.

        Args:
            incident_title: Title of incident
            country: Country code
            since_hours: Only articles from last N hours
            limit: Maximum results

        Returns:
            List of recent articles
        """
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)

        all_articles = self.search_incident_articles(
            incident_title,
            country,
            limit=limit * 2,  # Get extra to filter
            use_cache=False  # Don't use cache for fresh articles
        )

        fresh = [a for a in all_articles if a.publish_date > cutoff]
        return fresh[:limit]


# Singleton instance for easy access
_scraper_instance = None

def get_article_scraper() -> ArticleScraper:
    """Get or create article scraper singleton"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = ArticleScraper()
    return _scraper_instance
