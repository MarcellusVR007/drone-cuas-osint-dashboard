"""
Operational Classification Algorithm
Classifies drone incidents as BOUNTY_AMATEUR or STATE_ACTOR_PROFESSIONAL
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

def classify_incident(
    lights_observed: Optional[bool],
    drone_description: Optional[str],
    altitude_m: Optional[int],
    estimated_altitude_m: Optional[int],
    flight_pattern: Optional[str],
    time_of_day: Optional[str],
    sighting_time: Optional[str],
    duration_minutes: Optional[int],
    description: str,
    suspected_operator: Optional[str],
    drone_type_model: Optional[str] = None
) -> Tuple[str, float, str]:
    """
    Classify incident as BOUNTY_AMATEUR or STATE_ACTOR_PROFESSIONAL

    Returns:
        (classification, confidence, reasoning)
    """

    score_amateur = 0.0
    score_professional = 0.0
    reasoning_parts = []

    # 1. LIGHTS OBSERVED (strong indicator)
    if lights_observed is True:
        score_amateur += 0.25
        reasoning_parts.append("✓ Lights ON (amateur behavior - DJI default)")
    elif lights_observed is False:
        score_professional += 0.25
        reasoning_parts.append("✓ Lights OFF (professional stealth)")

    # 2. DRONE TYPE
    if drone_description:
        desc_lower = drone_description.lower()
        # Consumer drones
        if any(word in desc_lower for word in ["dji", "mavic", "phantom", "consumer", "hobby", "small quad"]):
            score_amateur += 0.20
            reasoning_parts.append(f"✓ Consumer drone: {drone_description}")
        # Military drones
        elif any(word in desc_lower for word in ["orlan", "military", "fixed wing", "large drone"]):
            score_professional += 0.25
            reasoning_parts.append(f"✓ Military-grade: {drone_description}")

    if drone_type_model:
        if "Orlan" in drone_type_model:
            score_professional += 0.30
            reasoning_parts.append(f"✓ Military model confirmed: {drone_type_model}")

    # 3. ALTITUDE
    altitude = estimated_altitude_m or altitude_m
    if altitude:
        if altitude < 120:  # Legal limit in most countries
            score_amateur += 0.15
            reasoning_parts.append(f"✓ Low altitude ({altitude}m - staying legal-ish)")
        elif altitude > 400:  # Beyond visual range
            score_professional += 0.20
            reasoning_parts.append(f"✓ High altitude ({altitude}m - BVLOS operation)")

    # 4. FLIGHT PATTERN
    if flight_pattern:
        if flight_pattern in ["erratic", "hover", "unknown"]:
            score_amateur += 0.10
            reasoning_parts.append(f"✓ {flight_pattern.title()} pattern (amateur)")
        elif flight_pattern in ["systematic", "perimeter_scan"]:
            score_professional += 0.15
            reasoning_parts.append(f"✓ {flight_pattern.title()} (professional recon)")

    # 5. TIME OF DAY
    if time_of_day:
        if time_of_day in ["day", "evening"]:
            score_amateur += 0.10
            reasoning_parts.append(f"✓ {time_of_day.title()} flight (amateur schedule)")
        elif time_of_day in ["dawn", "dusk", "night"]:
            score_professional += 0.15
            reasoning_parts.append(f"✓ {time_of_day.title()} flight (tactical advantage)")

    # 6. DURATION
    if duration_minutes:
        if duration_minutes < 20:  # Battery constraint
            score_amateur += 0.05
            reasoning_parts.append(f"✓ Short flight ({duration_minutes}min - consumer battery)")
        elif duration_minutes > 60:  # Extended mission
            score_professional += 0.10
            reasoning_parts.append(f"✓ Long flight ({duration_minutes}min - professional endurance)")

    # 7. DESCRIPTION KEYWORDS ANALYSIS
    desc_lower = description.lower()

    # Amateur indicators
    amateur_keywords = ["witnessed", "reported by civilian", "pilot observed", "airport closure"]
    for keyword in amateur_keywords:
        if keyword in desc_lower:
            score_amateur += 0.05
            reasoning_parts.append(f"✓ Civilian-visible operation ('{keyword}')")
            break

    # Professional indicators
    professional_keywords = ["espionage", "intelligence", "coordinated", "multiple sites", "systematic", "military base"]
    for keyword in professional_keywords:
        if keyword in desc_lower:
            score_professional += 0.10
            reasoning_parts.append(f"✓ Professional operation ('{keyword}')")
            break

    # 8. SUSPECTED OPERATOR
    if suspected_operator:
        op_lower = suspected_operator.lower()
        if any(word in op_lower for word in ["gru", "svr", "military", "state", "russia"]):
            score_professional += 0.20
            reasoning_parts.append(f"✓ State actor identified: {suspected_operator}")

    # 9. CALCULATE FINAL CLASSIFICATION
    total_score = score_amateur + score_professional

    if total_score == 0:
        return ("UNKNOWN", 0.0, "Insufficient data for classification")

    # Normalize confidence
    confidence_amateur = score_amateur / total_score
    confidence_professional = score_professional / total_score

    if confidence_professional > 0.6:
        classification = "STATE_ACTOR_PROFESSIONAL"
        confidence = confidence_professional
    elif confidence_amateur > 0.6:
        classification = "RECRUITED_LOCAL"
        confidence = confidence_amateur
    else:
        classification = "UNKNOWN"
        confidence = max(confidence_amateur, confidence_professional)
        reasoning_parts.append("⚠ Indicators inconclusive")

    reasoning = "\n".join(reasoning_parts)

    return (classification, confidence, reasoning)


def analyze_for_telegram_correlation(
    incident_date: datetime,
    location: str,
    target_type: str,
    telegram_posts: list
) -> Optional[Dict]:
    """
    Check if incident correlates with a Telegram bounty post

    Args:
        incident_date: Date of drone incident
        location: Location of incident
        target_type: Type of target (airport, military_base, etc.)
        telegram_posts: List of Telegram posts with dates

    Returns:
        Matching Telegram post dict or None
    """

    # Look for posts within 60 days before incident
    time_window = timedelta(days=60)

    for post in telegram_posts:
        post_date = datetime.fromisoformat(post['post_date'])
        days_diff = (incident_date - post_date).days

        # Must be after post date, within 60 days
        if 0 <= days_diff <= 60:
            # Check location match
            post_location = post.get('target_location', '').lower()
            if location.lower() in post_location or post_location in location.lower():
                return {
                    "post_id": post['id'],
                    "post_date": post['post_date'],
                    "time_delta_days": days_diff,
                    "payment_amount": post.get('payment_amount'),
                    "payment_currency": post.get('payment_currency'),
                    "bitcoin_wallet": post.get('crypto_wallet_address'),
                    "author": post.get('author_name'),
                    "correlation_strength": "HIGH" if days_diff < 30 else "MEDIUM"
                }

    return None


def generate_attribution_chain(
    incident,
    telegram_correlation: Optional[Dict],
    classification: str
) -> Dict:
    """
    Generate full attribution chain from handler to operative

    Returns:
        Attribution chain as dict
    """

    chain = {
        "incident_id": incident.id,
        "classification": classification,
        "chain_strength": "unknown"
    }

    if telegram_correlation:
        chain.update({
            "handler": {
                "username": telegram_correlation.get('author'),
                "affiliation": "Suspected GRU/SVR recruiter",
                "confidence": 0.7
            },
            "payment": {
                "wallet_address": telegram_correlation.get('bitcoin_wallet'),
                "amount": telegram_correlation.get('payment_amount'),
                "currency": telegram_correlation.get('payment_currency')
            },
            "operative": {
                "profile": "RECRUITED_LOCAL" if classification == "RECRUITED_LOCAL" else "PROFESSIONAL_OPERATOR",
                "estimated_count": 1,
                "motivation": "Financial (bounty)" if classification == "RECRUITED_LOCAL" else "Ideological/Professional"
            },
            "chain_strength": "STRONG"
        })
    else:
        # No Telegram link found
        if classification == "STATE_ACTOR_PROFESSIONAL":
            chain.update({
                "handler": {
                    "username": None,
                    "affiliation": "Likely direct military command (no recruitment)",
                    "confidence": 0.8
                },
                "operative": {
                    "profile": "MILITARY_PERSONNEL",
                    "estimated_count": 2-4,  # Typical Orlan team
                    "motivation": "Military orders"
                },
                "chain_strength": "MEDIUM (no SOCMINT link)"
            })
        else:
            chain["chain_strength"] = "WEAK (no attribution data)"

    return chain
