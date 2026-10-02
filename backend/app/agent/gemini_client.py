"""GenAI floor-action agent.

Design: grouping by aisle/bay is deterministic code (reliable, testable);
Gemini only writes the human briefing. If there's no API key or the call
fails, we fall back to a template so the demo never breaks.

TODO(Task 2): let Gemini also rank items/priorities (use response_mime_type
"application/json" + a response schema) once the basic flow works.
"""
import json
import logging
from collections import defaultdict

from google import genai
from google.genai import types

from app.agent.prompts import BRIEFING_PROMPT, SYSTEM_PROMPT
from app.core.config import get_settings
from app.models.anomaly import Anomaly, Checklist, ChecklistGroup

log = logging.getLogger(__name__)
MINUTES_PER_ITEM = 1  # rough walk+check time


def _group(items: list[Anomaly]) -> list[ChecklistGroup]:
    by_aisle: dict[str, list[Anomaly]] = defaultdict(list)
    for it in sorted(items, key=lambda a: (a.aisle, a.bay, -a.p_void)):
        by_aisle[it.aisle].append(it)
    return [
        ChecklistGroup(aisle=a, title=f"Aisle {a} — {rows[0].category}", items=rows)
        for a, rows in by_aisle.items()
    ]


def _template_briefing(items: list[Anomaly]) -> str:
    if not items:
        return "Good morning! No likely shelf voids right now."
    aisles = ", ".join(sorted({i.aisle for i in items}))
    return f"Good morning! {len(items)} high-probability voids detected across aisles {aisles}."


def _llm_briefing(items: list[Anomaly]) -> str:
    s = get_settings()
    client = genai.Client(api_key=s.gemini_api_key)
    payload = [
        {"sku": i.sku_name, "aisle": i.aisle, "bay": i.bay,
         "ledger": i.ledger_stock, "hours_since_sale": i.hours_since_last_sale}
        for i in items
    ]
    resp = client.models.generate_content(
        model=s.gemini_model,
        contents=BRIEFING_PROMPT.format(items=json.dumps(payload)),
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return (resp.text or "").strip()


def build_checklist(items: list[Anomaly]) -> Checklist:
    briefing = _template_briefing(items)
    if items and get_settings().gemini_api_key:
        try:
            briefing = _llm_briefing(items) or briefing
        except Exception:  # network, quota, bad model name...
            log.exception("Gemini call failed; using template briefing")
    return Checklist(
        briefing=briefing,
        estimated_minutes=max(1, len(items) * MINUTES_PER_ITEM),
        groups=_group(items),
    )
