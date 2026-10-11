"""Generates plain-English explanations for why a SKU was flagged as an anomaly (Feature C3)."""
import logging
import time
from typing import Any

from google import genai
from google.genai import types

from app.agent.prompts import EXPLAIN_PROMPT, EXPLAIN_SYSTEM_PROMPT
from app.core.config import get_settings

log = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600
_EXPLAIN_CACHE: dict[tuple, tuple[float, str]] = {}


def format_rate_str(rate: float) -> str:
    if abs(rate - round(rate)) < 0.05 and round(rate) > 0:
        return f"{int(round(rate))}/hr"
    return f"{rate:.1f}/hr"


def format_hours_str(hours: float) -> str:
    h = int(round(hours))
    return f"{h} hours" if h != 1 else "1 hour"


def template_explanation(
    sku_name: str,
    rate: float,
    hours: float,
    ledger: int,
    void_type: str = "frozen",
    category: str = "",
    expected_sales: float | None = None,
) -> str:
    """Deterministic plain-English explanation following Scout's standard audit format."""
    rate_str = format_rate_str(rate)
    hours_str = format_hours_str(hours)

    if void_type == "damaged":
        cat_str = f" in {category}" if category else ""
        return (f"Usually sells {rate_str} at this time, none in {hours_str} despite {ledger} units on ledger "
                f"(high damage/breakage risk{cat_str}).")
    if void_type == "backroom_stuck":
        return (f"Sales tapered to zero over {hours_str} while ledger says {ledger} units "
                f"(suspected backroom stock not replenished to shelf).")

    # default: frozen shelf void
    return f"Usually sells {rate_str} at this time, none in {hours_str}, ledger says {ledger}."


def llm_explanation(
    sku_name: str,
    rate: float,
    hours: float,
    ledger: int,
    void_type: str = "frozen",
    category: str = "",
) -> str:
    """Generate a 1-sentence plain-English explanation using Gemini."""
    s = get_settings()
    if not s.gemini_api_key:
        return template_explanation(sku_name, rate, hours, ledger, void_type, category)

    cache_key = (sku_name, round(rate, 2), round(hours, 1), ledger, void_type)
    now = time.time()
    if cache_key in _EXPLAIN_CACHE:
        ts, cached = _EXPLAIN_CACHE[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached

    prompt = EXPLAIN_PROMPT.format(
        sku_name=sku_name,
        category=category or "Groceries",
        rate=format_rate_str(rate),
        hours=format_hours_str(hours),
        ledger=ledger,
        void_type=void_type,
    )

    client = genai.Client(
        api_key=s.gemini_api_key,
        http_options=types.HttpOptions(timeout=10000),
    )
    resp = client.models.generate_content(
        model=s.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=EXPLAIN_SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=100,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    text = (resp.text or "").strip()
    if text:
        _EXPLAIN_CACHE[cache_key] = (now, text)
        return text
    return template_explanation(sku_name, rate, hours, ledger, void_type, category)


def explain_anomaly(
    sku_name: str,
    rate: float,
    hours: float,
    ledger: int,
    void_type: str = "frozen",
    category: str = "",
    expected_sales: float | None = None,
    use_llm: bool = False,
) -> str:
    """Returns a single plain-English sentence explaining why this anomaly was flagged."""
    if use_llm and get_settings().gemini_api_key:
        try:
            return llm_explanation(sku_name, rate, hours, ledger, void_type, category)
        except Exception:
            log.exception("LLM explanation failed; falling back to template")
    return template_explanation(sku_name, rate, hours, ledger, void_type, category, expected_sales)


def explain_anomaly_details(
    anomaly_id: str,
    sku_id: str,
    sku_name: str,
    rate: float,
    hours: float,
    ledger: int,
    p_void: float,
    void_type: str = "frozen",
    category: str = "",
    revenue_at_risk: float = 0.0,
    expected_sales: float | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Generates an explanation and factor breakdown for the /explain endpoint."""
    source = "template"
    if use_llm and get_settings().gemini_api_key:
        try:
            reason = llm_explanation(sku_name, rate, hours, ledger, void_type, category)
            source = "gemini"
        except Exception:
            log.exception("LLM explanation failed; using template")
            reason = template_explanation(sku_name, rate, hours, ledger, void_type, category, expected_sales)
    else:
        reason = template_explanation(sku_name, rate, hours, ledger, void_type, category, expected_sales)

    return {
        "anomaly_id": anomaly_id,
        "sku_id": sku_id,
        "sku_name": sku_name,
        "why_flagged": reason,
        "source": source,
        "factors": {
            "rate_per_hour": round(rate, 2),
            "hours_since_last_sale": round(hours, 1),
            "ledger_stock": ledger,
            "p_void": round(p_void, 3),
            "void_type": void_type,
            "category": category,
            "expected_sales": round(expected_sales if expected_sales is not None else (rate * hours), 1),
            "revenue_at_risk": round(revenue_at_risk, 2),
        },
    }
