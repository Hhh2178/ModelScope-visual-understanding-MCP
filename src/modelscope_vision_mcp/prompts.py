from __future__ import annotations

from pathlib import Path

from .errors import ConfigError


def load_prompt(
    project_root: Path | str,
    prompt_path: Path | str = Path("prompts/vision_reverse_prompt.zh.md"),
) -> str:
    root = Path(project_root)
    relative_prompt_path = Path(prompt_path)
    if relative_prompt_path.is_absolute():
        raise ConfigError("Prompt path must be relative to the project root")

    absolute_prompt_path = root / relative_prompt_path
    if not absolute_prompt_path.exists():
        raise ConfigError(f"Missing prompt file: {relative_prompt_path}")
    return absolute_prompt_path.read_text(encoding="utf-8")
