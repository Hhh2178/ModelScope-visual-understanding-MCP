import base64

from PIL import Image

from modelscope_vision_mcp.client import prepare_image_url


def test_prepare_image_url_keeps_http_url():
    assert prepare_image_url("https://example.com/a.png") == "https://example.com/a.png"


def test_prepare_image_url_keeps_data_url():
    data_url = "data:image/png;base64,AAAA"
    assert prepare_image_url(data_url) == data_url


def test_prepare_image_url_converts_relative_file_to_data_url(tmp_path):
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = prepare_image_url("image.png", project_root=tmp_path)

    assert result.startswith("data:image/png;base64,")
    assert result.endswith(base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii"))


def test_prepare_image_url_resizes_large_local_image(tmp_path):
    image_path = tmp_path / "large.jpg"
    Image.new("RGB", (1256, 2760), "white").save(image_path, format="JPEG")

    result = prepare_image_url("large.jpg", project_root=tmp_path)
    encoded = result.split(",", 1)[1]
    decoded = base64.b64decode(encoded)

    from PIL import Image as PILImage
    import io

    with PILImage.open(io.BytesIO(decoded)) as image:
        assert max(image.size) <= 2048
