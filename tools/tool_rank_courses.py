"""
Rank and filter raw course search results into validated `Course` models.

Scoring follows plan.md: platform (0.3), rating (0.3), completeness (0.2),
currency (0.1), price preference (0.1), plus small boosts for skill match and level fit.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from data_types.dto import Course, SkillLevel

VALID_DOMAINS = (
    "udemy.com",
    "coursera.org",
    "edx.org",
    "pluralsight.com",
    "linkedin.com/learning",
    "freecodecamp.org",
    "youtube.com",
    "udacity.com",
    "codecademy.com",
)

# Longer keys first so e.g. coursera.org matches before .org-only logic
_PLATFORM_REPUTATION: Tuple[Tuple[str, float], ...] = (
    ("linkedin.com/learning", 0.95),
    ("coursera.org", 0.98),
    ("edx.org", 0.96),
    ("udacity.com", 0.92),
    ("pluralsight.com", 0.90),
    ("freecodecamp.org", 0.93),
    ("udemy.com", 0.88),
    ("codecademy.com", 0.87),
    ("youtube.com", 0.72),
)

_WEIGHT_PLATFORM = 0.3
_WEIGHT_RATING = 0.3
_WEIGHT_COMPLETENESS = 0.2
_WEIGHT_CURRENCY = 0.1
_WEIGHT_PRICE = 0.1


def is_valid_course_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.lower()
    return any(domain in u for domain in VALID_DOMAINS)


def rank_courses(
    courses: List[Dict[str, Any]],
    skill: str,
    target_level: str,
) -> List[Course]:
    """
    Score, filter, and sort course dicts (e.g. from web search) into `Course` instances.

    Args:
        courses: Raw records; keys like title, url, snippet, rating, provider, etc.
        skill: Target skill name; used for relevance (title/description match).
        target_level: Desired learner level (e.g. ``SkillLevel.INTERMEDIATE.value``).

    Returns:
        Courses on allowed domains first (by score), then any remaining parsed rows,
        highest composite score first. Empty or invalid rows are dropped.
    """
    if not courses:
        return []

    skill_l = (skill or "").lower().strip()
    target_norm = _normalize_level(target_level)

    scored: List[Tuple[float, Course, bool]] = []
    for raw in courses:
        if not isinstance(raw, dict):
            continue
        parsed = _raw_to_course(raw)
        if parsed is None:
            continue
        valid_domain = is_valid_course_url(parsed.url)
        score = _composite_score(parsed, raw, skill_l, target_norm, valid_domain)
        scored.append((score, parsed, valid_domain))

    if not scored:
        return []

    scored.sort(key=lambda x: (x[2], x[0]), reverse=True)
    return [c for _, c, _ in scored]


def _normalize_level(level: str) -> str:
    s = (level or "").lower().strip()
    for sl in SkillLevel:
        if sl.value == s:
            return sl.value
    aliases = {
        "none": SkillLevel.NONE.value,
        "no experience": SkillLevel.NONE.value,
        "junior": SkillLevel.BEGINNER.value,
        "mid": SkillLevel.INTERMEDIATE.value,
        "mid-level": SkillLevel.INTERMEDIATE.value,
        "senior": SkillLevel.ADVANCED.value,
    }
    return aliases.get(s, s or SkillLevel.BEGINNER.value)


def _get_first(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None and d[k] != "":
            return d[k]
    return None


def _parse_rating(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        r = float(value)
        return r if 0 <= r <= 5 else min(max(r / 20.0, 0.0), 5.0)  # allow 0-100 mistake
    if isinstance(value, str):
        m = re.search(r"(\d+\.?\d*)\s*(?:/|\s*out of\s*)?\s*5", value, re.I)
        if m:
            return min(max(float(m.group(1)), 0.0), 5.0)
        m = re.search(r"(\d+\.?\d*)", value)
        if m:
            val = float(m.group(1))
            if val > 5:
                val = min(val / 20.0, 5.0)
            return min(max(val, 0.0), 5.0)
    return None


def _parse_hours(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(round(value)))
    if isinstance(value, str):
        m = re.search(r"(\d+)\s*(?:h|hr|hours?)", value, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)", value)
        if m:
            return int(m.group(1))
    return None


def _provider_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host or "unknown"
    except Exception:
        return "unknown"


def _raw_to_course(raw: Dict[str, Any]) -> Optional[Course]:
    title = _get_first(raw, "title", "name", "headline")
    url = _get_first(raw, "url", "link", "href")
    if not title or not url:
        return None
    if not isinstance(title, str) or not isinstance(url, str):
        title, url = str(title).strip(), str(url).strip()
        if not title or not url:
            return None

    provider = _get_first(raw, "provider", "site", "source")
    if not provider:
        provider = _provider_from_url(url)
    else:
        provider = str(provider)

    description = _get_first(raw, "description", "snippet", "text", "summary")
    if description is not None:
        description = str(description)

    instructor = _get_first(raw, "instructor", "author", "creator")
    if instructor is not None:
        instructor = str(instructor)

    rating = _parse_rating(_get_first(raw, "rating", "score", "stars", "review_score"))

    estimated_hours = _parse_hours(
        _get_first(raw, "estimated_hours", "duration_hours", "hours", "duration")
    )

    level_raw = _get_first(raw, "level", "difficulty")
    level = str(level_raw).lower().strip() if level_raw else "unknown"

    price_raw = _get_first(raw, "price", "cost")
    price = _normalize_price(price_raw, raw, title, url)

    return Course(
        title=title.strip(),
        provider=provider,
        url=url.strip(),
        instructor=instructor,
        rating=rating,
        estimated_hours=estimated_hours,
        level=level,
        price=price,
        description=description,
    )


def _normalize_price(price_raw: Any, raw: Dict[str, Any], title: str, url: str) -> str:
    if raw.get("is_free") is True:
        return "Free"
    if isinstance(price_raw, str) and price_raw.strip():
        return price_raw.strip()
    blob = f"{title} {url}".lower()
    if "free" in blob or "freecodecamp" in blob:
        return "Free"
    return "Paid"


def _platform_component(url: str, valid_domain: bool) -> float:
    if not valid_domain:
        return 0.15
    u = url.lower()
    for domain, rep in _PLATFORM_REPUTATION:
        if domain in u:
            return rep
    return 0.65


def _rating_component(rating: Optional[float]) -> float:
    if rating is None:
        return 0.55
    return min(max(rating / 5.0, 0.0), 1.0)


def _completeness_component(c: Course) -> float:
    parts = [
        bool(c.title),
        bool(c.url),
        bool(c.description),
        c.rating is not None,
        c.estimated_hours is not None,
        c.level != "unknown",
        bool(c.instructor),
    ]
    return sum(1.0 for p in parts if p) / len(parts)


def _currency_component(title: str, description: Optional[str]) -> float:
    text = f"{title} {description or ''}"
    if re.search(r"20(2[4-9]|3\d)", text):
        return 1.0
    if re.search(r"\b(updated|latest)\b", text, re.I):
        return 0.85
    return 0.45


def _price_component(price: str) -> float:
    p = (price or "").lower()
    if "free" in p:
        return 1.0
    if "paid" in p or "$" in p or "£" in p or "€" in p:
        return 0.65
    return 0.5


def _skill_relevance(title: str, description: Optional[str], skill_l: str) -> float:
    if not skill_l:
        return 0.5
    hay = f"{title} {description or ''}".lower()
    if skill_l in hay:
        return 1.0
    tokens = [t for t in re.split(r"[^\w]+", skill_l) if len(t) > 2]
    if tokens and all(t in hay for t in tokens):
        return 0.9
    return 0.35


def _level_fit(course_level: str, target_norm: str) -> float:
    order = [
        SkillLevel.NONE.value,
        SkillLevel.BEGINNER.value,
        SkillLevel.INTERMEDIATE.value,
        SkillLevel.ADVANCED.value,
        SkillLevel.EXPERT.value,
    ]
    cl = course_level.lower().strip() if course_level else "unknown"
    try:
        ti = order.index(target_norm) if target_norm in order else 1
    except ValueError:
        ti = 1
    try:
        ci = order.index(cl) if cl in order else -1
    except ValueError:
        ci = -1
    if ci < 0:
        return 0.55
    diff = abs(ci - ti)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.82
    return max(0.35, 0.82 - 0.15 * (diff - 1))


def _composite_score(
    c: Course,
    raw: Dict[str, Any],
    skill_l: str,
    target_norm: str,
    valid_domain: bool,
) -> float:
    base = (
        _WEIGHT_PLATFORM * _platform_component(c.url, valid_domain)
        + _WEIGHT_RATING * _rating_component(c.rating)
        + _WEIGHT_COMPLETENESS * _completeness_component(c)
        + _WEIGHT_CURRENCY * _currency_component(c.title, c.description)
        + _WEIGHT_PRICE * _price_component(c.price)
    )
    relevance = _skill_relevance(c.title, c.description, skill_l)
    level_fit = _level_fit(c.level, target_norm)
    # Small multiplicative blend so main weights still dominate
    return base * (0.88 + 0.06 * relevance + 0.06 * level_fit)
