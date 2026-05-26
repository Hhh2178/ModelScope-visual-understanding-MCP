from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from modelscope_vision_mcp.errors import ConfigError
from modelscope_vision_mcp.state import UsageState


def test_usage_state_starts_empty_and_uses_relative_path(tmp_path):
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))

    assert state.date == date(2026, 5, 25)
    assert state.get_used("Qwen/test") == 0


def test_usage_state_increments_and_persists(tmp_path):
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))
    state.increment("Qwen/test")
    state.save()

    reloaded = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))

    assert reloaded.get_used("Qwen/test") == 1


def test_usage_state_resets_on_new_day(tmp_path):
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))
    state.increment("Qwen/test")
    state.save()

    reloaded = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 26))

    assert reloaded.get_used("Qwen/test") == 0


def test_cooldown_blocks_until_time(tmp_path):
    now = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    state = UsageState.load(tmp_path, Path("state/usage.json"), today=date(2026, 5, 25))
    state.cooldown("Qwen/test", until=now + timedelta(seconds=300), reason="timeout")

    assert state.is_in_cooldown("Qwen/test", now=now) is True
    assert state.is_in_cooldown("Qwen/test", now=now + timedelta(seconds=301)) is False


def test_usage_state_rejects_absolute_state_path(tmp_path):
    with pytest.raises(ConfigError):
        UsageState.load(tmp_path, tmp_path / "state" / "usage.json")
