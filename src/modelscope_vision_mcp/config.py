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
    stream: bool = True
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


def load_config(
    project_root: Path | str,
    config_path: Path | str = Path("config/models.yaml"),
) -> AppConfig:
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
