from __future__ import annotations

from datetime import datetime, timezone

from .config import ModelConfig
from .errors import NoAvailableModelError
from .state import UsageState


def select_models(
    models: list[ModelConfig],
    state: UsageState,
    preferred_model: str | None = None,
    now: datetime | None = None,
) -> list[ModelConfig]:
    current_time = now or datetime.now(timezone.utc)
    available: list[ModelConfig] = []

    for model in models:
        if not model.enabled:
            continue
        if state.get_used(model.id) >= model.daily_limit:
            continue
        if state.is_blocked_today(model.id):
            continue
        if state.is_in_cooldown(model.id, now=current_time):
            continue
        available.append(model)

    if not available:
        raise NoAvailableModelError("No enabled model has quota remaining")

    return sorted(
        available,
        key=lambda model: (
            0 if preferred_model and model.id == preferred_model else 1,
            model.priority,
            model.id,
        ),
    )
