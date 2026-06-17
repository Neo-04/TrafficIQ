"""
rules_engine.py  --  PHASE 4: Transparent rule layers
======================================================
Replaces the removed severity ML model. Everything here is a plain,
editable lookup driven by config.py — no training, fully interpretable.

Pipeline position:
    predicted resolution class  ->  impact score
                                ->  derived severity
                                ->  resource recommendation

All three are pure functions so they can be unit-tested and reused by the
end-to-end pipeline (predict_pipeline.py) or a future dashboard.
"""

import config


def compute_impact_score(resolution_class: str) -> int:
    """Map a predicted resolution class to a 0-100 impact score."""
    return config.IMPACT_SCORE_MAP.get(resolution_class, 0)


def derive_severity(resolution_class: str) -> str:
    """Derive severity (Low / Medium / High) from the resolution class.

    Severity is NOT predicted by a model; it is a transparent rule. Edit
    config.RESOLUTION_TO_SEVERITY to change the mapping.
    """
    return config.RESOLUTION_TO_SEVERITY.get(resolution_class, "Unknown")


def recommend_resources(severity: str, event_cause: str | None = None) -> dict:
    """Recommend manpower / equipment from the derived severity.

    A cause-based adjustment guarantees a tow truck for incidents that
    typically need one (breakdowns, accidents). Edit config.RESOURCE_RULES
    and config.TOW_TRUCK_CAUSES to tune.
    """
    base = dict(config.RESOURCE_RULES.get(severity, config.RESOURCE_RULES["Low"]))
    if event_cause in config.TOW_TRUCK_CAUSES:
        base["tow_trucks"] = max(base.get("tow_trucks", 0), 1)
    return base


def build_response(resolution_class: str, event_cause: str | None = None) -> dict:
    """Run all three rule layers and return a single response dict."""
    severity = derive_severity(resolution_class)
    return {
        "predicted_resolution_class": resolution_class,
        "impact_score": compute_impact_score(resolution_class),
        "severity": severity,
        "recommended_resources": recommend_resources(severity, event_cause),
    }


if __name__ == "__main__":
    # quick self-check
    for rc in ["Quick", "Moderate", "Prolonged"]:
        print(rc, "->", build_response(rc, event_cause="vehicle_breakdown"))