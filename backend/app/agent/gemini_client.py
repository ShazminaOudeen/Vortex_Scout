"""GenAI floor-action agent.

Design: grouping by aisle/bay is deterministic code (reliable, testable);
Gemini only writes the human briefing. If there's no API key or the call
fails, we fall back to a template so the demo never breaks.

TODO(Task 2): let Gemini also rank items/priorities (use response_mime_type
"application/json" + a response schema) once the basic flow works.
"""

import time
from google.genai import errors
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


def _aisle_sort_key(aisle_str: str) -> tuple[int, str]:
    clean = (aisle_str or "").strip()
    return (int(clean), clean) if clean.isdigit() else (10**6, clean)


def _bay_sort_key(bay_str: str) -> tuple[int, str]:
    clean = (bay_str or "").strip()
    num_part = "".join(c for c in clean if c.isdigit())
    alpha_part = "".join(c for c in clean if not c.isdigit())
    return (int(num_part) if num_part else 0, alpha_part)


def _item_walk_key(a: Anomaly) -> tuple:
    # Walk path order along bay, then highest financial impact first on ties
    return (_bay_sort_key(a.bay), -a.revenue_at_risk, -a.p_void)


def prioritize_anomalies(items: list[Anomaly]) -> list[Anomaly]:
    """Rank anomalies store-wide by revenue at risk (units/hr * price * hours silent) and p_void (Feature C2)."""
    return sorted(items, key=lambda a: (-a.revenue_at_risk, -a.p_void, _aisle_sort_key(a.aisle), _bay_sort_key(a.bay)))


def _group(items: list[Anomaly]) -> list[ChecklistGroup]:
    """Group items by aisle and order along the supervisor's physical walk path (Feature C2)."""
    by_aisle: dict[str, list[Anomaly]] = defaultdict(list)
    for it in items:
        by_aisle[it.aisle].append(it)
    for a in by_aisle:
        by_aisle[a].sort(key=_item_walk_key)
    sorted_aisles = sorted(by_aisle.keys(), key=_aisle_sort_key)
    return [
        ChecklistGroup(aisle=a, title=f"Aisle {a} — {by_aisle[a][0].category}", items=by_aisle[a])
        for a in sorted_aisles
    ]


def _template_briefing(items: list[Anomaly]) -> str:
    if not items:
        return "Good morning! No likely shelf voids right now."
    aisles = ", ".join(sorted({i.aisle for i in items}, key=_aisle_sort_key))
    n, many_aisles = len(items), len({i.aisle for i in items}) > 1
    total_rev = sum(i.revenue_at_risk for i in items)
    rev_str = f" (~LKR {int(total_rev):,} at risk)" if total_rev > 0 else ""
    top_item = max(items, key=lambda i: i.revenue_at_risk, default=None)
    start_str = f" Start in Aisle {top_item.aisle} ({top_item.sku_name})." if top_item and top_item.revenue_at_risk > 0 else ""
    return (f"Good morning! {n} high-probability {'voids' if n > 1 else 'void'}{rev_str} detected "
            f"in {'aisles' if many_aisles else 'aisle'} {aisles}.{start_str}")


_CACHE: dict[tuple, tuple[float, str]] = {}
CACHE_SECONDS = 300
RETRY_DELAYS = (1, 2)  # seconds; keeps the worst case short for /floor
RETRYABLE = {429, 500, 503, 504}


def _llm_briefing(items: list[Anomaly]) -> str:
    key = tuple(sorted(i.id for i in items))
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    s = get_settings()
    client = genai.Client(
        api_key=s.gemini_api_key,
        http_options=types.HttpOptions(timeout=15000),
    )
    prioritized = prioritize_anomalies(items)
    payload = [
        {"sku": i.sku_name, "aisle": i.aisle, "bay": i.bay,
         "ledger": i.ledger_stock, "hours_since_sale": i.hours_since_last_sale,
         "revenue_at_risk_lkr": round(i.revenue_at_risk, 2), "p_void": round(i.p_void, 2)}
        for i in prioritized
    ]
    last_exc: Exception | None = None
    for delay in (0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            resp = client.models.generate_content(
                model=s.gemini_model,
                contents=BRIEFING_PROMPT.format(items=json.dumps(payload)),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except errors.APIError as e:
            if e.code not in RETRYABLE:
                raise
            last_exc = e
            log.warning("Gemini %s, retrying", e.code)
            continue
        text = (resp.text or "").strip()
        if not text:
            log.warning("Gemini returned empty text; using template")
            return ""
        _CACHE[key] = (time.time(), text)
        return text
    raise last_exc  # type: ignore[misc]


def verify_gemini_connection() -> dict:
    """Verifies the live Gemini API connection and configured model."""
    s = get_settings()
    if not s.gemini_api_key:
        return {"status": "skipped", "message": "No GEMINI_API_KEY configured"}
    try:
        client = genai.Client(
            api_key=s.gemini_api_key,
            http_options=types.HttpOptions(timeout=15000),
        )
        resp = client.models.generate_content(
            model=s.gemini_model,
            contents="Say hello in one short sentence.",
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return {
            "status": "ok",
            "model": s.gemini_model,
            "response": (resp.text or "").strip(),
        }
    except Exception as e:
        log.exception("verify_gemini_connection failed")
        return {
            "status": "error",
            "model": s.gemini_model,
            "error": str(e),
        }


def build_checklist(items: list[Anomaly]) -> Checklist:
    briefing = _template_briefing(items)
    if items and get_settings().gemini_api_key:
        try:
            briefing = _llm_briefing(items) or briefing
        except Exception:  # network, quota, bad model name...
            log.exception("Gemini call failed; using template briefing")
    total_rev = round(sum(i.revenue_at_risk for i in items), 2)
    return Checklist(
        briefing=briefing,
        estimated_minutes=max(1, len(items) * MINUTES_PER_ITEM),
        total_revenue_at_risk=total_rev,
        groups=_group(items),
    )
