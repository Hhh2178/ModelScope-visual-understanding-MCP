from modelscope_vision_mcp.portability_check import scan


def test_portability_check_finds_windows_absolute_path(tmp_path):
    file_path = tmp_path / "bad.md"
    file_path.write_text("path = " + "C:" + "\\fixed\\path", encoding="utf-8")

    findings = scan(tmp_path)

    assert len(findings) == 1
    assert findings[0][0] == file_path


def test_portability_check_allows_relative_paths(tmp_path):
    file_path = tmp_path / "good.md"
    file_path.write_text("path = config/models.yaml", encoding="utf-8")

    assert scan(tmp_path) == []
