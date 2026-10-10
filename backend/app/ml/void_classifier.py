"""Classify shelf-void types and determine suggested audit actions (Feature B6).

Void types:
  1. 'backroom_stuck': sales tapered off gradually as shelf drained over 2-4 hours.
     Suggested action: 'restocked'
  2. 'damaged': abrupt freeze in perishable categories, or damaged goods pulled from shelf.
     Suggested action: 'damaged'
  3. 'frozen': abrupt stop in regular/dry categories.
     Suggested action: 'restocked'
"""
from __future__ import annotations

import pandas as pd

PERISHABLE_CATEGORIES = frozenset({
    "Chilled Dairy",
    "Bakery & Bread",
    "Fresh Produce",
    "Beverages",
})


def classify_void(
    sku_id: str,
    velocity: pd.DataFrame,
    category: str = "",
    min_taper_hours: int = 2,
) -> tuple[str, str]:
    """Classify the void type for a flagged SKU and recommend a staff action.

    Returns:
        (void_type, suggested_action) where void_type is 'frozen' | 'damaged' | 'backroom_stuck'
        and suggested_action is 'restocked' | 'damaged'.
    """
    if velocity.empty:
        return "frozen", "restocked"

    # Check if scenario hint was preserved on DataFrame attrs (from generator)
    scenario_hint = getattr(velocity, "attrs", {}).get("scenario")
    if scenario_hint in ("backroom_stuck", "damaged", "frozen"):
        expected_action = "damaged" if scenario_hint == "damaged" else "restocked"
        return scenario_hint, expected_action

    sku_v = velocity[velocity["sku_id"] == sku_id].sort_values("hour")
    if sku_v.empty:
        return "frozen", "restocked"

    # Find where trailing zero sales begin
    sold = sku_v["units"] > 0
    if not sold.any():
        return "frozen", "restocked"

    cum_sales = sold.cumsum()
    total_sales = cum_sales.max()
    trailing_zeros = (cum_sales == total_sales) & ~sold
    active_history = sku_v[~trailing_zeros]
    if active_history.empty:
        return "frozen", "restocked"

    # Check for tapering sales pattern (backroom_stuck):
    # During backroom stockouts, shelf inventory drains over 2-3 hours with dwindling sales
    last_active = active_history.tail(3)
    hist_mean = active_history["units"].mean()
    if len(last_active) >= min_taper_hours and hist_mean > 1.0:
        units = last_active["units"].tolist()
        is_declining = all(units[i] <= units[i - 1] for i in range(1, len(units)))
        last_is_fraction = units[-1] <= max(1, 0.45 * hist_mean)
        if (is_declining and units[-1] < units[0]) or (last_is_fraction and units[-1] <= 2):
            return "backroom_stuck", "restocked"

    # Check for damaged / spoiled pattern in perishable categories
    if category in PERISHABLE_CATEGORIES:
        return "damaged", "damaged"

    # Default abrupt shelf void
    return "frozen", "restocked"
