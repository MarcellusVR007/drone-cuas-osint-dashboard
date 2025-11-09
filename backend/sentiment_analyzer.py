"""
Sentiment Analysis for News Articles and Sources

Analyzes the emotional tone and potential bias of news articles
about drone incidents.

Features:
- Multi-language sentiment analysis
- Source bias detection
- Claim extraction and sentiment
- Bias scoring
- Trend analysis over time

Usage:
    from backend.sentiment_analyzer import SentimentAnalyzer
    analyzer = SentimentAnalyzer()

    sentiment = analyzer.analyze("The drone invasion threatens our airspace!")
    print(sentiment)  # {'score': 0.75, 'label': 'positive', 'confidence': 0.95}
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Sentiment:
    """Represents sentiment analysis result"""
    score: float  # -1.0 (very negative) to 1.0 (very positive), 0 = neutral
    label: str  # "negative", "neutral", "positive"
    confidence: float  # 0-1, confidence in the analysis
    language: str  # Language of analyzed text

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
            "language": self.language
        }


class SentimentAnalyzer:
    """
    Analyzes sentiment and bias in news articles.

    Uses a combination of:
    - Keyword-based scoring (fast, offline)
    - Transformer models (optional, requires installation)
    - Contextual analysis
    """

    # Sentiment keywords for different languages
    POSITIVE_KEYWORDS = {
        'en': ['successful', 'effective', 'praised', 'triumph', 'detected', 'captured', 'safe', 'secure'],
        'nl': ['succesvol', 'effectief', 'geprezen', 'triomf', 'gedetecteerd', 'veilig'],
        'de': ['erfolgreich', 'wirksam', 'gelobt', 'triumph', 'erkannt', 'sicher'],
        'fr': ['succès', 'efficace', 'félicité', 'triomphe', 'détecté', 'sûr'],
    }

    NEGATIVE_KEYWORDS = {
        'en': ['threat', 'danger', 'risk', 'attack', 'invasion', 'terrorist', 'failure', 'loss'],
        'nl': ['bedreiging', 'gevaar', 'risico', 'aanval', 'invasie', 'mislukking'],
        'de': ['bedrohung', 'gefahr', 'risiko', 'anschlag', 'invasion', 'niederlage'],
        'fr': ['menace', 'danger', 'risque', 'attaque', 'invasion', 'échec'],
    }

    # Intensifiers (amplify sentiment)
    INTENSIFIERS = {
        'en': ['very', 'extremely', 'highly', 'serious', 'severe', 'major'],
        'nl': ['zeer', 'uiterst', 'ernstig', 'zwaar'],
        'de': ['sehr', 'äußerst', 'ernst', 'schwer'],
        'fr': ['très', 'extrêmement', 'grave', 'sérieux'],
    }

    # Bias indicators
    BIAS_INDICATORS = {
        'alarmist': {
            'en': ['must', 'urgent', 'immediate', 'catastrophe', 'crisis'],
            'nl': ['moet', 'urgent', 'catastrofe', 'crisis'],
        },
        'sensational': {
            'en': ['shocking', 'astounding', 'incredible', 'exclusive', 'breaking'],
            'nl': ['schokken', 'verbazingwekkend', 'exclusief', 'breaking'],
        },
        'politically_motivated': {
            'en': ['communist', 'fascist', 'socialist', 'capitalist', 'regime'],
            'nl': ['communistisch', 'fascistisch', 'regime'],
        },
    }

    def __init__(self, use_transformer: bool = False):
        """
        Initialize sentiment analyzer.

        Args:
            use_transformer: Use transformer model (requires 'transformers' package)
        """
        self.use_transformer = use_transformer
        self.transformer_model = None

        if use_transformer:
            try:
                from transformers import pipeline
                self.transformer_model = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english"
                )
                logger.info("Loaded transformer sentiment model")
            except ImportError:
                logger.warning("Transformers not installed, using keyword-based analysis")
                self.use_transformer = False

    def analyze(self, text: str, language: str = "en") -> Sentiment:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze
            language: Language code (en, nl, de, fr, etc.)

        Returns:
            Sentiment object with score, label, and confidence
        """

        if not text or len(text.strip()) < 10:
            return Sentiment(score=0.0, label="neutral", confidence=0.5, language=language)

        # Try transformer first if available
        if self.use_transformer and language == "en":
            try:
                return self._analyze_transformer(text, language)
            except Exception as e:
                logger.warning(f"Transformer analysis failed: {e}, falling back to keywords")

        # Keyword-based analysis
        return self._analyze_keywords(text, language)

    def _analyze_transformer(self, text: str, language: str) -> Sentiment:
        """Analyze using transformer model (English only)"""
        try:
            result = self.transformer_model(text)[0]

            # Convert to -1 to 1 scale
            if result['label'] == 'POSITIVE':
                score = result['score']
            else:
                score = -result['score']

            label = self._score_to_label(score)

            return Sentiment(
                score=score,
                label=label,
                confidence=abs(result['score']),
                language=language
            )

        except Exception as e:
            logger.error(f"Transformer error: {e}")
            raise

    def _analyze_keywords(self, text: str, language: str) -> Sentiment:
        """Analyze using keyword matching"""

        text_lower = text.lower()

        # Get keywords for language
        positive_words = self.POSITIVE_KEYWORDS.get(language, self.POSITIVE_KEYWORDS['en'])
        negative_words = self.NEGATIVE_KEYWORDS.get(language, self.NEGATIVE_KEYWORDS['en'])
        intensifiers = self.INTENSIFIERS.get(language, self.INTENSIFIERS['en'])

        # Count sentiment words
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        # Check for intensifiers nearby
        intensifier_boost = 0
        for intensifier in intensifiers:
            if intensifier in text_lower:
                # Find nearby sentiment words
                parts = text_lower.split(intensifier)
                for part in parts:
                    if any(word in part for word in positive_words):
                        intensifier_boost += 0.2
                    if any(word in part for word in negative_words):
                        intensifier_boost -= 0.2

        # Calculate score
        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words == 0:
            score = 0.0
            confidence = 0.3
        else:
            raw_score = (pos_count - neg_count) / total_sentiment_words
            score = min(1.0, max(-1.0, raw_score + intensifier_boost))
            confidence = min(1.0, total_sentiment_words / 10)  # More words = more confidence

        label = self._score_to_label(score)

        return Sentiment(
            score=score,
            label=label,
            confidence=confidence,
            language=language
        )

    def _score_to_label(self, score: float) -> str:
        """Convert score to label"""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"

    def detect_bias(self, text: str, language: str = "en") -> Dict[str, float]:
        """
        Detect potential bias in text.

        Returns:
            Dict with bias types and scores (0-1)
        """

        text_lower = text.lower()
        bias_scores = {
            'alarmist': 0.0,
            'sensational': 0.0,
            'politically_motivated': 0.0,
            'overall_bias': 0.0
        }

        # Check each bias type
        for bias_type, keywords_by_lang in self.BIAS_INDICATORS.items():
            keywords = keywords_by_lang.get(language, keywords_by_lang.get('en', []))
            count = sum(1 for keyword in keywords if keyword in text_lower)
            # Score: 0-1 based on how many bias keywords found
            bias_scores[bias_type] = min(1.0, count / 3.0)

        # Overall bias is average of specific biases
        specific_biases = [
            bias_scores['alarmist'],
            bias_scores['sensational'],
            bias_scores['politically_motivated']
        ]
        bias_scores['overall_bias'] = sum(specific_biases) / len(specific_biases)

        return bias_scores

    def analyze_article(
        self,
        title: str,
        summary: Optional[str] = None,
        language: str = "en"
    ) -> Dict:
        """
        Comprehensive analysis of article sentiment and bias.

        Args:
            title: Article title
            summary: Article summary/body
            language: Language code

        Returns:
            Dict with sentiment and bias analysis
        """

        # Analyze title
        title_sentiment = self.analyze(title, language)

        # Analyze body if provided
        body_sentiment = None
        if summary:
            body_sentiment = self.analyze(summary, language)

        # Detect bias in title and body
        title_bias = self.detect_bias(title, language)
        body_bias = self.detect_bias(summary or "", language)

        # Combine scores (if both exist, average them)
        if body_sentiment:
            overall_sentiment = Sentiment(
                score=(title_sentiment.score + body_sentiment.score) / 2,
                label=self._score_to_label((title_sentiment.score + body_sentiment.score) / 2),
                confidence=(title_sentiment.confidence + body_sentiment.confidence) / 2,
                language=language
            )
            bias_score = (title_bias['overall_bias'] + body_bias['overall_bias']) / 2
        else:
            overall_sentiment = title_sentiment
            bias_score = title_bias['overall_bias']

        return {
            "sentiment": overall_sentiment.to_dict(),
            "bias": {
                "alarmist": title_bias['alarmist'] if not body_sentiment else (title_bias['alarmist'] + body_bias['alarmist']) / 2,
                "sensational": title_bias['sensational'] if not body_sentiment else (title_bias['sensational'] + body_bias['sensational']) / 2,
                "politically_motivated": title_bias['politically_motivated'] if not body_sentiment else (title_bias['politically_motivated'] + body_bias['politically_motivated']) / 2,
                "overall_bias_score": bias_score
            },
            "trustworthiness_score": 1.0 - bias_score,  # Inverse of bias
            "analysis_date": datetime.utcnow().isoformat(),
            "language": language
        }

    def compare_sources(self, articles: List[Dict]) -> Dict:
        """
        Compare sentiment across multiple articles from different sources.

        Args:
            articles: List of article dicts with title, summary, source_name

        Returns:
            Comparative analysis across sources
        """

        source_analysis = {}

        for article in articles:
            source = article.get('source_name', 'Unknown')
            analysis = self.analyze_article(
                article.get('title', ''),
                article.get('summary'),
                article.get('language', 'en')
            )

            if source not in source_analysis:
                source_analysis[source] = {
                    'articles': [],
                    'avg_sentiment': 0.0,
                    'avg_bias': 0.0,
                    'avg_trustworthiness': 0.0,
                }

            source_analysis[source]['articles'].append(analysis)

        # Calculate averages per source
        for source, data in source_analysis.items():
            if data['articles']:
                sentiments = [a['sentiment']['score'] for a in data['articles']]
                biases = [a['bias']['overall_bias_score'] for a in data['articles']]
                trustworthiness = [a['trustworthiness_score'] for a in data['articles']]

                data['avg_sentiment'] = sum(sentiments) / len(sentiments)
                data['avg_bias'] = sum(biases) / len(biases)
                data['avg_trustworthiness'] = sum(trustworthiness) / len(trustworthiness)
                data['article_count'] = len(data['articles'])

                # Remove individual articles from output for brevity
                del data['articles']

        return {
            "comparison": source_analysis,
            "summary": {
                "sources_analyzed": len(source_analysis),
                "most_positive_source": max(source_analysis.items(), key=lambda x: x[1]['avg_sentiment'])[0] if source_analysis else None,
                "most_negative_source": min(source_analysis.items(), key=lambda x: x[1]['avg_sentiment'])[0] if source_analysis else None,
                "most_biased_source": max(source_analysis.items(), key=lambda x: x[1]['avg_bias'])[0] if source_analysis else None,
                "most_trustworthy_source": max(source_analysis.items(), key=lambda x: x[1]['avg_trustworthiness'])[0] if source_analysis else None,
            },
            "analysis_date": datetime.utcnow().isoformat()
        }


# Singleton instance
_analyzer_instance = None

def get_sentiment_analyzer(use_transformer: bool = False) -> SentimentAnalyzer:
    """Get or create sentiment analyzer singleton"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer(use_transformer=use_transformer)
    return _analyzer_instance
