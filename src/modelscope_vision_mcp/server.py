from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .client import ModelScopeVisionClient
from .config import load_config
from .errors import ConfigError, ModelCallError, NoAvailableModelError
from .output import build_deepseek_context, normalize_vision_payload
from .prompts import load_prompt
from .selector import select_models
from .state import UsageState

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - exercised only when MCP dependency is missing.
    FastMCP = None  # type: ignore[assignment]


if FastMCP is not None:
    mcp = FastMCP("modelscope-vision")
else:
    mcp = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def analyze_image_core(
    image: str,
    question: str | None = None,
    detail: str = "medium",
    preferred_model: str | None = None,
) -> dict[str, Any]:
    root = project_root()
    config = load_config(root)
    state = UsageState.load(root, Path("state/usage.json"), today=date.today())
    prompt = load_prompt(root)

    try:
        client = ModelScopeVisionClient(config.modelscope)
        models = select_models(config.models, state, preferred_model=preferred_model)
    except (ConfigError, NoAvailableModelError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "attempts": [],
        }

    attempts: list[dict[str, str]] = []
    for model in models:
        try:
            raw_payload = client.analyze(
                model,
                image=image,
                prompt=prompt,
                question=question,
                project_root=root,
            )
            vision = normalize_vision_payload(raw_payload)
            state.increment(model.id)
            attempts.append({"model": model.id, "status": "success", "reason": ""})
            state.save()
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


if mcp is not None:

    @mcp.tool()
    def analyze_image(
        image: str,
        question: str | None = None,
        detail: str = "medium",
        preferred_model: str | None = None,
    ) -> str:
        return json.dumps(
            analyze_image_core(
                image=image,
                question=question,
                detail=detail,
                preferred_model=preferred_model,
            ),
            ensure_ascii=False,
        )


def main() -> None:
    if mcp is None:
        raise RuntimeError("The mcp package is required to run the server")
    mcp.run()


if __name__ == "__main__":
    main()
