import json

from modelscope_vision_mcp.output import (
    build_deepseek_context,
    normalize_vision_payload,
    parse_model_json,
)


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


def test_parse_model_json_accepts_plain_json_and_code_fence():
    payload = {"summary": "ok"}

    assert parse_model_json(json.dumps(payload, ensure_ascii=False)) == payload
    assert parse_model_json("```json\n{\"summary\":\"ok\"}\n```") == payload
