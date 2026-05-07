"""Extract ``skillpath_viz`` JSON from orchestrator replies (Option A / Gradio charts)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import ValidationError

from data_types.dto import LearningPath

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


@dataclass
class SkillpathVizPayload:
    current_skills: dict[str, str]
    required_skills: dict[str, str]
    learning_path: LearningPath | None


def _parse_learning_path(raw: object) -> LearningPath | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return LearningPath.model_validate(raw)
    except ValidationError:
        return None


def _build_payload(inner: dict) -> SkillpathVizPayload | None:
    cs = inner.get("current_skills")
    rs = inner.get("required_skills")
    if cs is None:
        cs = {}
    if rs is None:
        rs = {}
    if not isinstance(cs, dict) or not isinstance(rs, dict):
        return None
    current = {str(k): str(v) for k, v in cs.items()}
    required = {str(k): str(v) for k, v in rs.items()}
    lp = _parse_learning_path(inner.get("learning_path"))
    if not current and not required and lp is None:
        return None
    return SkillpathVizPayload(
        current_skills=current,
        required_skills=required,
        learning_path=lp,
    )


def extract_skillpath_viz(assistant_text: str) -> tuple[str, SkillpathVizPayload | None]:
    """
    Find the last valid ```json``` block containing ``{"skillpath_viz": {...}}``.

    Returns cleaned assistant text (block removed) and the payload, or (original, None).
    """
    last_payload: SkillpathVizPayload | None = None
    last_span: tuple[int, int] | None = None

    for m in _JSON_FENCE.finditer(assistant_text):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or "skillpath_viz" not in data:
            continue
        inner = data["skillpath_viz"]
        if not isinstance(inner, dict):
            continue
        payload = _build_payload(inner)
        if payload is not None:
            last_payload = payload
            last_span = m.span()

    if last_span is None or last_payload is None:
        return assistant_text.strip(), None

    start, end = last_span
    cleaned = (assistant_text[:start].rstrip() + "\n\n" + assistant_text[end:].lstrip()).strip()
    return cleaned, last_payload
