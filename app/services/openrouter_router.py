"""Deterministic local AI routing policy for CK Personal Finance.

External model execution is disabled by product policy. This module keeps the
existing interface so a separately approved local or included provider can be
added later without changing route handlers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


EXTERNAL_AI_DISABLED_REASON = (
    "External model providers are disabled by product policy. "
    "Use deterministic local functions or an approved included/local provider."
)

LOCAL_TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "label": "Local simple task",
        "reasoning_levels": ["low", "routine", "cheap"],
        "model": None,
        "cost_policy": "Deterministic local processing only.",
    },
    "modest": {
        "label": "Local structured task",
        "reasoning_levels": ["medium", "normal", "moderate"],
        "model": None,
        "cost_policy": "Deterministic local processing only.",
    },
    "expensive": {
        "label": "Local complex task",
        "reasoning_levels": ["high", "deep", "hard"],
        "model": None,
        "cost_policy": "External execution remains disabled.",
    },
}

REASONING_TO_TIER = {
    "low": "free",
    "routine": "free",
    "cheap": "free",
    "medium": "modest",
    "normal": "modest",
    "moderate": "modest",
    "high": "expensive",
    "deep": "expensive",
    "hard": "expensive",
}
TIER_ORDER = ["free", "modest", "expensive"]


def openrouter_key_configured() -> bool:
    """Compatibility hook. Secrets are deliberately not inspected."""

    return False


def _normalise_reasoning(value: str | None) -> str:
    level = (value or "low").strip().lower()
    return level if level in REASONING_TO_TIER else "low"


def select_openrouter_route(
    reasoning_level: str | None = None,
    max_cost_tier: str | None = None,
) -> dict[str, Any]:
    """Select a deterministic local tier without making a provider call."""

    level = _normalise_reasoning(reasoning_level)
    selected_tier = REASONING_TO_TIER[level]
    max_tier = (max_cost_tier or "expensive").strip().lower()
    if max_tier not in TIER_ORDER:
        max_tier = "free"
    if TIER_ORDER.index(selected_tier) > TIER_ORDER.index(max_tier):
        selected_tier = max_tier
    tier = dict(LOCAL_TIERS[selected_tier])
    tier.update(
        {
            "provider": None,
            "tier": selected_tier,
            "reasoning_level": level,
            "max_cost_tier": max_tier,
            "key_configured": False,
            "provider_call_allowed": False,
            "disabled_reason": EXTERNAL_AI_DISABLED_REASON,
        }
    )
    return tier


def openrouter_policy() -> dict[str, Any]:
    """Return a compatibility policy that never reads secrets or enables calls."""

    return {
        "provider": None,
        "key_configured": False,
        "tiers": LOCAL_TIERS,
        "routing_rule": "Local deterministic route selection only; no external provider execution.",
        "default_execution": "disabled_by_policy",
        "provider_call_allowed": False,
        "privacy_boundary": EXTERNAL_AI_DISABLED_REASON,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def local_fallback(prompt: str, route: dict[str, Any]) -> dict[str, Any]:
    summary = " ".join(prompt.split())[:240] or "No prompt supplied."
    return {
        "provider_called": False,
        "fallback": True,
        "content": (
            f"Local route decision only. Selected {route['label']} ({route['tier']}) "
            f"for {route['reasoning_level']} reasoning. Prompt summary: {summary}"
        ),
        "next_action": "Continue with deterministic local features.",
    }


async def openrouter_complete(
    *,
    prompt: str,
    reasoning_level: str | None = None,
    max_cost_tier: str | None = None,
    execute: bool = False,
    allow_paid_provider: bool = False,
    system: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic blocked result. Never construct a network client."""

    route = select_openrouter_route(reasoning_level, max_cost_tier)
    return {
        "ok": False,
        "state": "disabled_by_policy",
        "provider": None,
        "provider_called": False,
        "provider_call_allowed": False,
        "route": route,
        "result": local_fallback(prompt, route),
        "reason": EXTERNAL_AI_DISABLED_REASON,
    }
