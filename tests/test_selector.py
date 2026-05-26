from datetime import date
from pathlib import Path

import pytest

from modelscope_vision_mcp.config import ModelConfig
from modelscope_vision_mcp.errors import NoAvailableModelError
from modelscope_vision_mcp.selector import select_models
from modelscope_vision_mcp.state import UsageState


def test_selector_orders_by_preferred_then_priority(tmp_path):
    models = [
        ModelConfig(id="Qwen/b", priority=2),
        ModelConfig(id="Qwen/a", priority=1),
    ]
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))

    selected = select_models(models, state, preferred_model="Qwen/b")

    assert [m.id for m in selected] == ["Qwen/b", "Qwen/a"]


def test_selector_skips_quota_exhausted_model(tmp_path):
    models = [
        ModelConfig(id="Qwen/a", priority=1, daily_limit=1),
        ModelConfig(id="Qwen/b", priority=2, daily_limit=10),
    ]
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))
    state.increment("Qwen/a")

    selected = select_models(models, state)

    assert [m.id for m in selected] == ["Qwen/b"]


def test_selector_raises_when_no_model_available(tmp_path):
    models = [ModelConfig(id="Qwen/a", priority=1, enabled=False)]
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))

    with pytest.raises(NoAvailableModelError):
        select_models(models, state)
