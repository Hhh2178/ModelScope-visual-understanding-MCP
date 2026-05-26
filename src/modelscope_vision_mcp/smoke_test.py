from __future__ import annotations

import argparse
import json
from pathlib import Path

from .server import analyze_image_core


DEFAULT_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a ModelScope Vision MCP smoke test.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Image URL, data URL, base64, or relative path.")
    parser.add_argument("--question", default="请详细识别这张图片。")
    parser.add_argument("--preferred-model", default=None)
    args = parser.parse_args()

    result = analyze_image_core(
        image=args.image,
        question=args.question,
        preferred_model=args.preferred_model,
    )
    print(json.dumps(_redact(result), ensure_ascii=False, indent=2))


def _redact(value):
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return value.replace("ms-", "ms-***")
    if isinstance(value, Path):
        return str(value)
    return value


if __name__ == "__main__":
    main()
