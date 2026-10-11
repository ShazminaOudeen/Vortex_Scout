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

from app.agent.prompts import (
    BRIEFING_PROMPT,
    STRUCTURED_PLAN_PROMPT,
    STRUCTURED_PLAN_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)
from app.core.config import get_settings
from app.models.anomaly import (
    Anomaly,
    Checklist,
    ChecklistAgentPlan,
    ChecklistGroup,
    ItemStructuredAdvice,
    PriorityLevel,
)

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
        if not getattr(it, "why_flagged", ""):
            from app.agent.explainer import template_explanation
            rate = it.expected_sales / max(1.0, it.hours_since_last_sale) if it.expected_sales else 1.0
            it.why_flagged = template_explanation(
                it.sku_name, rate, it.hours_since_last_sale, it.ledger_stock,
                void_type=it.void_type, category=it.category, expected_sales=it.expected_sales,
            )
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


class CircuitBreaker:
    """Protects mobile /floor requests from hanging on persistent Gemini upstream outages (Feature C5)."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_failures = 0
        self.last_failure_time: float = 0.0
        self.state: str = "closed"

    def is_open(self) -> bool:
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.cooldown_seconds:
                self.state = "half_open"
                return False
            return True
        return False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = "closed"

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = "open"

    def reset(self) -> None:
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.state = "closed"

    def status(self) -> dict:
        remaining = max(0.0, round(self.cooldown_seconds - (time.time() - self.last_failure_time), 1)) if self.state == "open" else 0.0
        return {
            "state": self.state,
            "consecutive_failures": self.consecutive_failures,
            "cooldown_remaining_sec": remaining,
        }


CIRCUIT_BREAKER = CircuitBreaker()
_CACHE: dict[tuple, tuple[float, str]] = {}
CACHE_SECONDS = 300
RETRY_DELAYS = (1, 2)  # seconds; keeps the worst case short for /floor
RETRYABLE = {429, 500, 503, 504}


def _llm_briefing(items: list[Anomaly]) -> str:
    key = tuple(sorted(i.id for i in items))
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    if CIRCUIT_BREAKER.is_open():
        log.warning("Circuit breaker is open; bypassing LLM briefing call")
        return ""

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
                CIRCUIT_BREAKER.record_failure()
                raise
            last_exc = e
            log.warning("Gemini %s, retrying", e.code)
            continue
        text = (resp.text or "").strip()
        if not text:
            log.warning("Gemini returned empty text; using template")
            return ""
        CIRCUIT_BREAKER.record_success()
        _CACHE[key] = (time.time(), text)
        return text
    CIRCUIT_BREAKER.record_failure()
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


def _compute_priority_level(a: Anomaly) -> PriorityLevel:
    if a.revenue_at_risk >= 5000 or (a.revenue_at_risk >= 2000 and a.p_void >= 0.85):
        return "critical"
    if a.revenue_at_risk >= 1500 or a.p_void >= 0.80:
        return "high"
    if a.revenue_at_risk >= 500 or a.p_void >= 0.75:
        return "medium"
    return "low"


def _template_plan(items: list[Anomaly]) -> ChecklistAgentPlan:
    if not items:
        return ChecklistAgentPlan(
            briefing="Good morning! No likely shelf voids right now.",
            start_aisle="",
            items=[],
        )
    briefing = _template_briefing(items)
    top_item = max(items, key=lambda i: i.revenue_at_risk, default=None)
    start_aisle = top_item.aisle if top_item else (items[0].aisle if items else "")
    items_advice = [
        ItemStructuredAdvice(
            sku_id=i.sku_id,
            priority=_compute_priority_level(i),
            reason=i.why_flagged or (
                f"Usually sells {getattr(i, 'expected_sales', 1.0) / max(1.0, i.hours_since_last_sale):.1f}/hr, "
                f"none in {int(i.hours_since_last_sale)} hours, ledger says {i.ledger_stock}."
            ),
            suggested_action=i.suggested_action,
        )
        for i in items
    ]
    return ChecklistAgentPlan(
        briefing=briefing,
        start_aisle=start_aisle,
        items=items_advice,
    )


_PLAN_CACHE: dict[tuple, tuple[float, ChecklistAgentPlan]] = {}


def _llm_structured_plan(items: list[Anomaly]) -> ChecklistAgentPlan:
    if not items:
        return _template_plan(items)
    key = tuple(sorted(i.id for i in items))
    hit = _PLAN_CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    if CIRCUIT_BREAKER.is_open():
        log.warning("Circuit breaker is open; bypassing LLM structured plan call")
        return _template_plan(items)

    s = get_settings()
    client = genai.Client(
        api_key=s.gemini_api_key,
        http_options=types.HttpOptions(timeout=15000),
    )
    prioritized = prioritize_anomalies(items)
    payload = [
        {
            "sku_id": i.sku_id,
            "sku_name": i.sku_name,
            "aisle": i.aisle,
            "bay": i.bay,
            "ledger_stock": i.ledger_stock,
            "hours_since_sale": i.hours_since_last_sale,
            "revenue_at_risk_lkr": round(i.revenue_at_risk, 2),
            "p_void": round(i.p_void, 2),
            "void_type": i.void_type,
            "category": i.category,
        }
        for i in prioritized
    ]
    last_exc: Exception | None = None
    for delay in (0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            resp = client.models.generate_content(
                model=s.gemini_model,
                contents=STRUCTURED_PLAN_PROMPT.format(items=json.dumps(payload)),
                config=types.GenerateContentConfig(
                    system_instruction=STRUCTURED_PLAN_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ChecklistAgentPlan,
                    temperature=0.2,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except errors.APIError as e:
            if e.code not in RETRYABLE:
                CIRCUIT_BREAKER.record_failure()
                raise
            last_exc = e
            log.warning("Gemini %s, retrying structured plan", e.code)
            continue
        text = (resp.text or "").strip()
        if not text:
            log.warning("Gemini returned empty structured plan; falling back to template")
            return _template_plan(items)
        try:
            plan = ChecklistAgentPlan.model_validate_json(text)
            CIRCUIT_BREAKER.record_success()
            _PLAN_CACHE[key] = (time.time(), plan)
            return plan
        except Exception:
            log.exception("Failed to parse Gemini structured response into ChecklistAgentPlan")
            return _template_plan(items)
    CIRCUIT_BREAKER.record_failure()
    raise last_exc  # type: ignore[misc]


def get_agent_health() -> dict:
    """Returns reliability metrics, circuit breaker state, and cache statistics (Feature C5)."""
    s = get_settings()
    configured = bool(s.gemini_api_key)
    cb_status = CIRCUIT_BREAKER.status()
    if not configured:
        health_status = "unconfigured"
    elif cb_status["state"] == "open":
        health_status = "degraded"
    else:
        health_status = "healthy"

    return {
        "status": health_status,
        "configured": configured,
        "model": s.gemini_model,
        "timeout_ms": 15000,
        "circuit_breaker": cb_status,
        "cache": {
            "text_cache_entries": len(_CACHE),
            "plan_cache_entries": len(_PLAN_CACHE),
        },
    }


def generate_agent_plan(items: list[Anomaly], use_llm: bool = True) -> ChecklistAgentPlan:
    """Generate structured audit plan with typed schema (Feature C4)."""
    if use_llm and get_settings().gemini_api_key and items:
        try:
            return _llm_structured_plan(items)
        except Exception:
            log.exception("Structured LLM plan call failed; falling back to template plan")
    return _template_plan(items)


def build_checklist(items: list[Anomaly]) -> Checklist:
    briefing = _template_briefing(items)
    plan: ChecklistAgentPlan | None = None
    if items and get_settings().gemini_api_key:
        try:
            plan = generate_agent_plan(items, use_llm=True)
            briefing = plan.briefing or briefing
        except Exception:
            log.exception("Structured plan generation failed; using template briefing")
            try:
                briefing = _llm_briefing(items) or briefing
            except Exception:
                pass
            plan = _template_plan(items)
    else:
        plan = _template_plan(items)

    if plan:
        advice_by_sku = {a.sku_id: a for a in plan.items}
        for it in items:
            adv = advice_by_sku.get(it.sku_id)
            if adv:
                it.priority_level = adv.priority
                if not getattr(it, "why_flagged", ""):
                    it.why_flagged = adv.reason
                if adv.suggested_action in ("restocked", "damaged", "false_alarm"):
                    it.suggested_action = adv.suggested_action
            else:
                it.priority_level = _compute_priority_level(it)
    else:
        for it in items:
            it.priority_level = _compute_priority_level(it)

    total_rev = round(sum(i.revenue_at_risk for i in items), 2)
    return Checklist(
        briefing=briefing,
        estimated_minutes=max(1, len(items) * MINUTES_PER_ITEM),
        total_revenue_at_risk=total_rev,
        groups=_group(items),
        plan=plan,
    )
