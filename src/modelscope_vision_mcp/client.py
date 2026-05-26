from __future__ import annotations

import base64
import io
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import ModelConfig, ModelScopeConfig
from .errors import ConfigError, ModelCallError
from .output import parse_model_json

MAX_IMAGE_DIMENSION = 2048


class ModelScopeVisionClient:
    def __init__(self, config: ModelScopeConfig):
        token = os.getenv(config.token_env)
        if not token:
            raise ConfigError(f"Missing ModelScope token env var: {config.token_env}")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ConfigError("The openai package is required for ModelScope API calls") from exc

        self._client = OpenAI(api_key=token, base_url=config.base_url)

    def analyze(
        self,
        model: ModelConfig,
        image: str,
        prompt: str,
        question: str | None = None,
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        image_url = prepare_image_url(image, project_root=project_root)
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
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                temperature=0.1,
                timeout=model.timeout_seconds,
                stream=model.stream,
            )
        except Exception as exc:
            reason = str(exc)
            category = _categorize_error(reason)
            raise ModelCallError(model.id, reason, category=category) from exc

        content = _collect_response_content(response, stream=model.stream)
        try:
            return parse_model_json(content)
        except ValueError as exc:
            raise ModelCallError(model.id, str(exc), category="invalid_output") from exc


def _collect_response_content(response: Any, stream: bool) -> str:
    if stream:
        chunks: list[str] = []
        for chunk in response:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None)
            if content:
                chunks.append(content)
        text = "".join(chunks).strip()
        if not text:
            raise ValueError("ModelScope stream did not include text content")
        return text

    choices = getattr(response, "choices", None)
    if not choices:
        raise ValueError(f"ModelScope response did not include choices: {_safe_response_preview(response)}")
    return choices[0].message.content or ""


def _safe_response_preview(response: Any) -> str:
    if hasattr(response, "model_dump"):
        payload = response.model_dump()
    else:
        payload = str(response)
    text = str(payload)
    return text[:500]


def prepare_image_url(image: str, project_root: Path | None = None) -> str:
    value = image.strip()
    if value.startswith("data:image/"):
        return value
    if _looks_like_url(value):
        return value
    if _looks_like_base64(value):
        return f"data:image/png;base64,{value}"

    path = Path(value)
    if path.is_absolute():
        image_path = path
    else:
        root = project_root or Path.cwd()
        image_path = root / path
    if not image_path.exists():
        raise ConfigError(f"Image path does not exist: {path}")
    mime_type, image_bytes = _prepare_local_image_bytes(image_path)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _prepare_local_image_bytes(image_path: Path) -> tuple[str, bytes]:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    raw = image_path.read_bytes()
    try:
        from PIL import Image
    except ImportError:
        return mime_type, raw

    try:
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
            if width <= MAX_IMAGE_DIMENSION and height <= MAX_IMAGE_DIMENSION:
                return mime_type, raw

            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            output = io.BytesIO()
            save_format = "PNG" if image.mode in {"RGBA", "LA", "P"} else "JPEG"
            if save_format == "JPEG" and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(output, format=save_format, quality=92)
            resized_mime = "image/png" if save_format == "PNG" else "image/jpeg"
            return resized_mime, output.getvalue()
    except Exception:
        return mime_type, raw


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_base64(value: str) -> bool:
    if len(value) < 32 or any(ch.isspace() for ch in value):
        return False
    try:
        base64.b64decode(value, validate=True)
    except Exception:
        return False
    return True


def _categorize_error(reason: str) -> str:
    text = reason.lower()
    if "input size exceed" in text or "image size" in text or "2048x2048" in text:
        return "unsupported_input"
    if "quota" in text or "insufficient" in text or "rate limit" in text:
        return "quota_exhausted"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "unauthorized" in text or "invalid api key" in text or "401" in text:
        return "auth_error"
    if "image" in text and "support" in text:
        return "unsupported_input"
    return "model_error"
