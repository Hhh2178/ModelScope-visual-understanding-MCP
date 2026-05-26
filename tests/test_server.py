import json

from modelscope_vision_mcp import server


def test_mcp_tool_returns_json_string(monkeypatch):
    if server.mcp is None:
        return

    def fake_core(**kwargs):
        return {"ok": True, "deepseek_context": "context"}

    monkeypatch.setattr(server, "analyze_image_core", fake_core)

    result = server.analyze_image("image.png")

    assert isinstance(result, str)
    assert json.loads(result) == {"ok": True, "deepseek_context": "context"}
