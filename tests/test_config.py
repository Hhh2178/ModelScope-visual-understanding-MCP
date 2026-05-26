from pathlib import Path

import pytest

from modelscope_vision_mcp.config import ModelConfig, load_config
from modelscope_vision_mcp.errors import ConfigError


def test_model_config_defaults_are_portable():
    model = ModelConfig(id="Qwen/test-model", priority=2)

    assert model.id == "Qwen/test-model"
    assert model.priority == 2
    assert model.enabled is True
    assert model.daily_limit == 100
    assert model.timeout_seconds == 60
    assert model.cooldown_seconds == 300
    assert model.stream is True


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


def test_load_config_rejects_absolute_config_path(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path, tmp_path / "config" / "models.yaml")
