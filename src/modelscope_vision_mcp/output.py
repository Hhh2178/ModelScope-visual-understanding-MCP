from __future__ import annotations

import json
import re
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


def parse_model_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Model JSON output must be an object")
    return parsed


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
