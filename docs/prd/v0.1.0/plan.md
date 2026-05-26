# ModelScope Vision MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable ModelScope Vision MCP that analyzes one image in detail, rotates through configured daily model quotas, falls back on model failure, and returns DeepSeek-ready visual context.

**Architecture:** The MCP is a self-contained Python project under `mcp/modelscope-vision/`. Runtime paths are resolved from the project root using relative paths only. The implementation separates configuration loading, quota state, model selection, ModelScope client calls, prompt rendering, output normalization, and MCP server wiring.

**Tech Stack:** Python 3.11+, FastMCP or official MCP Python SDK, OpenAI-compatible HTTP client for ModelScope API, PyYAML, pytest.

---

## File Structure

All files are created under the project folder. No implementation file should depend on a machine-specific absolute path.

```text
mcp/modelscope-vision/
  pyproject.toml
  README.md
  config/
    models.example.yaml
  docs/
    prd/
      README.md
      v0.1.0/
        prd.md
        spec.md
        plan.md
        dev.md
        progress.md
        decisions.md
        release.md
        changelog.md
  prompts/
    vision_reverse_prompt.zh.md
  src/
    modelscope_vision_mcp/
      __init__.py
      config.py
      state.py
      selector.py
      prompts.py
      client.py
      output.py
      server.py
      errors.py
  tests/
    fixtures/
      tiny_image_base64.txt
    test_config.py
    test_state.py
    test_selector.py
    test_output.py
```

## Task 1: Package Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/modelscope_vision_mcp/__init__.py`
- Create: `src/modelscope_vision_mcp/errors.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the first config import test**

Create `tests/test_config.py`:

```python
from modelscope_vision_mcp.config import ModelConfig


def test_model_config_defaults_are_portable():
    model = ModelConfig(id="Qwen/test-model", priority=2)

    assert model.id == "Qwen/test-model"
    assert model.priority == 2
    assert model.enabled is True
    assert model.daily_limit == 100
    assert model.timeout_seconds == 60
    assert model.cooldown_seconds == 300
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
pytest tests/test_config.py -q
```

Expected: FAIL because `modelscope_vision_mcp.config` does not exist yet.

- [ ] **Step 3: Add package metadata**

Create `pyproject.toml`:

```toml
[project]
name = "modelscope-vision-mcp"
version = "0.1.0"
description = "Hermes ModelScope vision recognition MCP"
requires-python = ">=3.11"
dependencies = [
  "mcp>=1.0.0",
  "openai>=1.0.0",
  "pydantic>=2.0.0",
  "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[project.scripts]
modelscope-vision-mcp = "modelscope_vision_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Add minimal package files**

Create `src/modelscope_vision_mcp/__init__.py`:

```python
"""ModelScope Vision MCP package."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `src/modelscope_vision_mcp/errors.py`:

```python
class VisionMcpError(Exception):
    """Base error for ModelScope Vision MCP."""


class ConfigError(VisionMcpError):
    """Raised when project configuration is invalid."""


class NoAvailableModelError(VisionMcpError):
    """Raised when no configured model can be used."""


class ModelCallError(VisionMcpError):
    """Raised when a ModelScope model call fails."""

    def __init__(self, model_id: str, reason: str, category: str = "model_error"):
        super().__init__(f"{model_id}: {reason}")
        self.model_id = model_id
        self.reason = reason
        self.category = category
```

- [ ] **Step 5: Commit**

```bash
git add mcp/modelscope-vision/pyproject.toml mcp/modelscope-vision/src mcp/modelscope-vision/tests/test_config.py
git commit -m "feat: scaffold modelscope vision mcp package"
```

If the workspace is not a git repository, record the completed task in `docs/prd/v0.1.0/progress.md` instead of committing.

## Task 2: Relative Configuration Loader

**Files:**
- Create: `src/modelscope_vision_mcp/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Add config loader tests**

Append to `tests/test_config.py`:

```python
from pathlib import Path

from modelscope_vision_mcp.config import load_config


def test_load_config_resolves_paths_from_project_root(tmp_path):
    project_root = tmp_path
    config_dir = project_root / "config"
    config_dir.mkdir()
    config_file = config_dir / "models.yaml"
    config_file.write_text(
        """
modelscope:
  base_url: https://api-inference.modelscope.cn/v1
  token_env: MODELSCOPE_TOKEN
models:
  - id: Qwen/test-model
    priority: 1
    daily_limit: 9
""".strip(),
        encoding="utf-8",
    )

    config = load_config(project_root)

    assert config.project_root == project_root
    assert config.config_path == Path("config/models.yaml")
    assert config.modelscope.base_url == "https://api-inference.modelscope.cn/v1"
    assert config.models[0].id == "Qwen/test-model"
    assert config.models[0].daily_limit == 9
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_config.py -q
```

Expected: FAIL because `load_config` is not implemented.

- [ ] **Step 3: Implement config loader**

Create `src/modelscope_vision_mcp/config.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .errors import ConfigError


class ModelScopeConfig(BaseModel):
    base_url: str = "https://api-inference.modelscope.cn/v1"
    token_env: str = "MODELSCOPE_TOKEN"


class ModelConfig(BaseModel):
    id: str
    name: str | None = None
    enabled: bool = True
    priority: int = 100
    daily_limit: int = 100
    timeout_seconds: int = 60
    cooldown_seconds: int = 300
    supports_image_url: bool = True
    supports_base64: bool = True


class AppConfig(BaseModel):
    project_root: Path
    config_path: Path = Path("config/models.yaml")
    modelscope: ModelScopeConfig = Field(default_factory=ModelScopeConfig)
    models: list[ModelConfig]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML object")
    return data


def load_config(project_root: Path | str, config_path: Path | str = Path("config/models.yaml")) -> AppConfig:
    root = Path(project_root)
    relative_config_path = Path(config_path)
    if relative_config_path.is_absolute():
        raise ConfigError("Config path must be relative to the project root")

    data = _read_yaml(root / relative_config_path)
    data["project_root"] = root
    data["config_path"] = relative_config_path
    if not data.get("models"):
        raise ConfigError("At least one model must be configured")
    return AppConfig.model_validate(data)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
pytest tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit or progress update**

```bash
git add mcp/modelscope-vision/src/modelscope_vision_mcp/config.py mcp/modelscope-vision/tests/test_config.py
git commit -m "feat: add relative config loader"
```

If git is unavailable, update `docs/prd/v0.1.0/progress.md`.

## Task 3: Daily Quota State

**Files:**
- Create: `src/modelscope_vision_mcp/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write quota state tests**

Create `tests/test_state.py`:

```python
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_state.py -q
```

Expected: FAIL because `UsageState` does not exist.

- [ ] **Step 3: Implement quota state**

Create `src/modelscope_vision_mcp/state.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
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
    def load(cls, project_root: Path | str, state_path: Path | str, today: date | None = None) -> "UsageState":
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
        return cls(project_root=root, state_path=relative_state_path, date=current_day, models=models)

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
                model_id: usage.__dict__
                for model_id, usage in self.models.items()
            },
        }
        absolute_state_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
pytest tests/test_state.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit or progress update**

```bash
git add mcp/modelscope-vision/src/modelscope_vision_mcp/state.py mcp/modelscope-vision/tests/test_state.py
git commit -m "feat: add daily model quota state"
```

If git is unavailable, update `docs/prd/v0.1.0/progress.md`.

## Task 4: Model Selector

**Files:**
- Create: `src/modelscope_vision_mcp/selector.py`
- Create: `tests/test_selector.py`

- [ ] **Step 1: Write selector tests**

Create `tests/test_selector.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_selector.py -q
```

Expected: FAIL because `select_models` is missing.

- [ ] **Step 3: Implement selector**

Create `src/modelscope_vision_mcp/selector.py`:

```python
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
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
pytest tests/test_selector.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit or progress update**

```bash
git add mcp/modelscope-vision/src/modelscope_vision_mcp/selector.py mcp/modelscope-vision/tests/test_selector.py
git commit -m "feat: add quota-aware model selector"
```

If git is unavailable, update `docs/prd/v0.1.0/progress.md`.

## Task 5: Prompt and Output Normalization

**Files:**
- Create: `src/modelscope_vision_mcp/prompts.py`
- Create: `src/modelscope_vision_mcp/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write output tests**

Create `tests/test_output.py`:

```python
from modelscope_vision_mcp.output import build_deepseek_context, normalize_vision_payload


def test_normalize_vision_payload_keeps_required_fields():
    payload = {
        "summary": "画面是一张室内人像。",
        "camera": ["平视中近景，浅景深。"],
        "subject": ["一名人物面向镜头。"],
    }

    result = normalize_vision_payload(payload)

    assert result["summary"] == "画面是一张室内人像。"
    assert result["camera"] == ["平视中近景，浅景深。"]
    assert result["text_detected"] == ["无明显可读文字"]
    assert result["uncertainties"] == ["未提供额外不确定点"]


def test_build_deepseek_context_is_detailed_and_cautious():
    vision = normalize_vision_payload(
        {
            "summary": "画面是一张室内人像。",
            "camera": ["平视中近景，浅景深。"],
            "subject": ["一名人物面向镜头。"],
            "environment": ["背景为室内空间。"],
            "lighting": ["柔和侧光。"],
        }
    )

    context = build_deepseek_context(vision, question="这张图适合做头像吗？")

    assert "图片识别结果" in context
    assert "平视中近景" in context
    assert "用户问题：这张图适合做头像吗？" in context
    assert "不要假设未被识别出的画面细节" in context
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_output.py -q
```

Expected: FAIL because output helpers do not exist.

- [ ] **Step 3: Implement prompt loader**

Create `src/modelscope_vision_mcp/prompts.py`:

```python
from __future__ import annotations

from pathlib import Path

from .errors import ConfigError


def load_prompt(project_root: Path | str, prompt_path: Path | str = Path("prompts/vision_reverse_prompt.zh.md")) -> str:
    root = Path(project_root)
    relative_prompt_path = Path(prompt_path)
    if relative_prompt_path.is_absolute():
        raise ConfigError("Prompt path must be relative to the project root")
    absolute_prompt_path = root / relative_prompt_path
    if not absolute_prompt_path.exists():
        raise ConfigError(f"Missing prompt file: {relative_prompt_path}")
    return absolute_prompt_path.read_text(encoding="utf-8")
```

- [ ] **Step 4: Implement output normalization**

Create `src/modelscope_vision_mcp/output.py`:

```python
from __future__ import annotations

from typing import Any


REQUIRED_ARRAY_FIELDS = [
    "camera",
    "subject",
    "environment",
    "composition",
    "lighting",
    "color",
    "texture",
    "text_detected",
    "style",
    "effects",
    "quality",
    "uncertainties",
]


def _as_string_list(value: Any, default: str) -> list[str]:
    if value is None:
        return [default]
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned or [default]
    text = str(value).strip()
    return [text] if text else [default]


def normalize_vision_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "summary": str(payload.get("summary") or "未提供图片整体概括").strip(),
    }
    for field in REQUIRED_ARRAY_FIELDS:
        default = "无明显可读文字" if field == "text_detected" else f"未提供{field}信息"
        if field == "uncertainties":
            default = "未提供额外不确定点"
        result[field] = _as_string_list(payload.get(field), default)
    return result


def _join(items: list[str]) -> str:
    return "；".join(item for item in items if item)


def build_deepseek_context(vision: dict[str, Any], question: str | None = None) -> str:
    lines = [
        "图片识别结果：",
        f"1. 整体概括：{vision['summary']}",
        f"2. 主体与关系：{_join(vision['subject'])}",
        f"3. 场景与空间：{_join(vision['environment'])}",
        f"4. 机位、镜头与构图：{_join(vision['camera'])}；{_join(vision['composition'])}",
        f"5. 光影、色彩与材质：{_join(vision['lighting'])}；{_join(vision['color'])}；{_join(vision['texture'])}",
        f"6. 风格、效果与质量：{_join(vision['style'])}；{_join(vision['effects'])}；{_join(vision['quality'])}",
        f"7. 可见文字：{_join(vision['text_detected'])}",
        f"8. 不确定点：{_join(vision['uncertainties'])}",
    ]
    if question:
        lines.append(f"用户问题：{question}")
    lines.append("请基于以上视觉识别结果继续分析；不要假设未被识别出的画面细节；如需要判断，请区分已确认事实与推测。")
    return "\n".join(lines)
```

- [ ] **Step 5: Run tests and verify pass**

Run:

```bash
pytest tests/test_output.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit or progress update**

```bash
git add mcp/modelscope-vision/src/modelscope_vision_mcp/prompts.py mcp/modelscope-vision/src/modelscope_vision_mcp/output.py mcp/modelscope-vision/tests/test_output.py
git commit -m "feat: normalize detailed vision output"
```

If git is unavailable, update `docs/prd/v0.1.0/progress.md`.

## Task 6: ModelScope Client and MCP Server

**Files:**
- Create: `src/modelscope_vision_mcp/client.py`
- Create: `src/modelscope_vision_mcp/server.py`
- Modify: `docs/prd/v0.1.0/dev.md`

- [ ] **Step 1: Implement ModelScope client**

Create `src/modelscope_vision_mcp/client.py`:

```python
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .config import ModelConfig, ModelScopeConfig
from .errors import ConfigError, ModelCallError


class ModelScopeVisionClient:
    def __init__(self, config: ModelScopeConfig):
        token = os.getenv(config.token_env)
        if not token:
            raise ConfigError(f"Missing ModelScope token env var: {config.token_env}")
        self._client = OpenAI(api_key=token, base_url=config.base_url)

    def analyze(self, model: ModelConfig, image: str, prompt: str, question: str | None = None) -> dict[str, Any]:
        user_text = prompt
        if question:
            user_text += f"\n\n用户针对图片的问题：{question}"
        try:
            response = self._client.chat.completions.create(
                model=model.id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": image}},
                        ],
                    }
                ],
                temperature=0.1,
                timeout=model.timeout_seconds,
            )
        except Exception as exc:
            reason = str(exc)
            category = _categorize_error(reason)
            raise ModelCallError(model.id, reason, category=category) from exc

        content = response.choices[0].message.content or ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelCallError(model.id, "Model did not return valid JSON", category="invalid_output") from exc
        if not isinstance(parsed, dict):
            raise ModelCallError(model.id, "Model JSON output must be an object", category="invalid_output")
        return parsed


def _categorize_error(reason: str) -> str:
    text = reason.lower()
    if "quota" in text or "insufficient" in text or "limit" in text:
        return "quota_exhausted"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "unauthorized" in text or "invalid api key" in text or "401" in text:
        return "auth_error"
    if "image" in text and "support" in text:
        return "unsupported_input"
    return "model_error"
```

- [ ] **Step 2: Implement MCP server**

Create `src/modelscope_vision_mcp/server.py`:

```python
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ModelScopeVisionClient
from .config import load_config
from .errors import ModelCallError, NoAvailableModelError
from .output import build_deepseek_context, normalize_vision_payload
from .prompts import load_prompt
from .selector import select_models
from .state import UsageState


mcp = FastMCP("modelscope-vision")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@mcp.tool()
def analyze_image(
    image: str,
    question: str | None = None,
    detail: str = "medium",
    preferred_model: str | None = None,
) -> dict[str, Any]:
    root = project_root()
    config = load_config(root)
    state = UsageState.load(root, Path("state/usage.json"), today=date.today())
    prompt = load_prompt(root)
    client = ModelScopeVisionClient(config.modelscope)
    attempts: list[dict[str, str]] = []

    try:
        models = select_models(config.models, state, preferred_model=preferred_model)
    except NoAvailableModelError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "attempts": attempts,
        }

    for model in models:
        try:
            raw_payload = client.analyze(model, image=image, prompt=prompt, question=question)
            vision = normalize_vision_payload(raw_payload)
            state.increment(model.id)
            state.save()
            attempts.append({"model": model.id, "status": "success", "reason": ""})
            return {
                "ok": True,
                "model_used": model.id,
                "fallback_used": len(attempts) > 1,
                "attempts": attempts,
                "detail": detail,
                "deepseek_context": build_deepseek_context(vision, question=question),
                "vision": vision,
            }
        except ModelCallError as exc:
            attempts.append({"model": model.id, "status": exc.category, "reason": exc.reason})
            if exc.category == "quota_exhausted":
                state.block_today(model.id, exc.reason)
            elif exc.category in {"timeout", "model_error", "invalid_output", "unsupported_input"}:
                state.cooldown(
                    model.id,
                    until=datetime.now(timezone.utc) + timedelta(seconds=model.cooldown_seconds),
                    reason=exc.reason,
                )
            elif exc.category == "auth_error":
                state.save()
                return {
                    "ok": False,
                    "error": "ModelScope authentication failed",
                    "attempts": attempts,
                }
            state.save()

    return {
        "ok": False,
        "error": "All configured vision models failed or were unavailable",
        "attempts": attempts,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run import check**

Run:

```bash
python -c "from modelscope_vision_mcp.server import analyze_image; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 4: Commit or progress update**

```bash
git add mcp/modelscope-vision/src/modelscope_vision_mcp/client.py mcp/modelscope-vision/src/modelscope_vision_mcp/server.py
git commit -m "feat: add modelscope vision mcp server"
```

If git is unavailable, update `docs/prd/v0.1.0/progress.md`.

## Task 7: Documentation and Local Validation

**Files:**
- Create: `docs/prd/v0.1.0/dev.md`
- Create: `docs/prd/v0.1.0/progress.md`
- Create: `docs/prd/v0.1.0/decisions.md`
- Create: `docs/prd/v0.1.0/release.md`
- Create: `docs/prd/v0.1.0/changelog.md`
- Modify: `README.md`

- [ ] **Step 1: Run tests**

Run:

```bash
pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run path portability scan**

Run:

```bash
python -m modelscope_vision_mcp.portability_check
```

Expected: PASS with no machine-specific path findings.

- [ ] **Step 3: Document Hermes MCP add command using placeholders**

Add to `README.md`:

```markdown
## Hermes 接入示例

以下命令只作为模板，所有路径由部署环境决定，不在项目内写死绝对路径：

```bash
hermes mcp add modelscope-vision --command python --args -m modelscope_vision_mcp.server --env MODELSCOPE_TOKEN=<token>
```
```

- [ ] **Step 4: Update progress docs**

Record:

```markdown
## v0.1.0 Progress

- PRD: complete
- Spec: complete
- Implementation plan: complete
- Code: pending
- Local tests: pending
- Hermes runtime integration: pending confirmation
```

- [ ] **Step 5: Commit or progress update**

```bash
git add mcp/modelscope-vision/README.md mcp/modelscope-vision/docs/prd/v0.1.0
git commit -m "docs: add modelscope vision mcp implementation docs"
```

If git is unavailable, keep the progress files as the source of truth.

## Self-Review

Spec coverage:

- Independent folder: covered by file structure and path principles.
- Detailed visual output: covered by prompt, output normalization, and DeepSeek context tasks.
- Model quota list: covered by config and state tasks.
- Quota-based model switching: covered by selector and server tasks.
- Failure fallback: covered by server task.
- Relative paths only: covered by config, state, prompt loader, and validation scan.
- PRD/spec guidance: covered by project docs in `docs/prd/v0.1.0/`.

Placeholder scan:

- No open-ended implementation placeholders remain in the task steps.
- The only placeholder-style values are documented command/template values such as `<token>` and replacement model IDs, which are intentional configuration examples.

Type consistency:

- `ModelConfig`, `UsageState`, `select_models`, `normalize_vision_payload`, and `build_deepseek_context` are introduced before use in later tasks.
