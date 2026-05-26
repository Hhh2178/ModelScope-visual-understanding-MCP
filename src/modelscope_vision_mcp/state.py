from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ConfigError


@dataclass
class ModelUsage:
    used_today: int = 0
    blocked_today: bool = False
    last_error: str = ""
    cooldown_until: str = ""


@dataclass
class UsageState:
    project_root: Path
    state_path: Path
    date: date
    models: dict[str, ModelUsage] = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        project_root: Path | str,
        state_path: Path | str,
        today: date | None = None,
    ) -> "UsageState":
        root = Path(project_root)
        relative_state_path = Path(state_path)
        if relative_state_path.is_absolute():
            raise ConfigError("State path must be relative to the project root")

        current_day = today or date.today()
        absolute_state_path = root / relative_state_path
        if not absolute_state_path.exists():
            return cls(project_root=root, state_path=relative_state_path, date=current_day)

        data = json.loads(absolute_state_path.read_text(encoding="utf-8"))
        stored_date = date.fromisoformat(data.get("date", current_day.isoformat()))
        if stored_date != current_day:
            return cls(project_root=root, state_path=relative_state_path, date=current_day)

        models = {
            model_id: ModelUsage(**usage)
            for model_id, usage in data.get("models", {}).items()
        }
        return cls(
            project_root=root,
            state_path=relative_state_path,
            date=current_day,
            models=models,
        )

    def _usage(self, model_id: str) -> ModelUsage:
        self.models.setdefault(model_id, ModelUsage())
        return self.models[model_id]

    def get_used(self, model_id: str) -> int:
        return self._usage(model_id).used_today

    def increment(self, model_id: str) -> None:
        self._usage(model_id).used_today += 1

    def block_today(self, model_id: str, reason: str) -> None:
        usage = self._usage(model_id)
        usage.blocked_today = True
        usage.last_error = reason

    def is_blocked_today(self, model_id: str) -> bool:
        return self._usage(model_id).blocked_today

    def cooldown(self, model_id: str, until: datetime, reason: str) -> None:
        usage = self._usage(model_id)
        usage.cooldown_until = until.astimezone(timezone.utc).isoformat()
        usage.last_error = reason

    def is_in_cooldown(self, model_id: str, now: datetime | None = None) -> bool:
        usage = self._usage(model_id)
        if not usage.cooldown_until:
            return False
        current = now or datetime.now(timezone.utc)
        return current < datetime.fromisoformat(usage.cooldown_until)

    def save(self) -> None:
        absolute_state_path = self.project_root / self.state_path
        absolute_state_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "date": self.date.isoformat(),
            "models": {
                model_id: asdict(usage)
                for model_id, usage in self.models.items()
            },
        }
        absolute_state_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
