from pathlib import Path

from modelscope_vision_mcp.config import load_config


def test_project_models_config_contains_requested_models():
    project_root = Path(__file__).resolve().parents[1]

    config = load_config(project_root)

    assert [(model.id, model.daily_limit, model.priority) for model in config.models] == [
        ("Qwen/Qwen3-VL-8B-Instruct", 50, 1),
        ("Qwen/Qwen3.5-35B-A3B", 50, 3),
        ("Qwen/Qwen3.5-27B", 50, 4),
        ("Qwen/Qwen3.5-397B-A17B", 50, 5),
        ("Qwen/Qwen3.5-122B-A10B", 50, 6),
        ("moonshotai/Kimi-K2.5", 50, 2),
    ]
