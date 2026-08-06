import io

from fastapi.testclient import TestClient
from PIL import Image

from main import app

import pytest

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _make_fake_image_bytes(fmt: str = "JPEG") -> bytes:
    """Tạo 1 ảnh nhỏ 64x64 màu đỏ trong bộ nhớ để dùng cho test upload."""
    img = Image.new("RGB", (64, 64), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_detect_image_valid_file(client):
    image_bytes = _make_fake_image_bytes("JPEG")
    response = client.post(
        "/api/detect/image",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        data={"confidence": "0.25"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "annotated_image_base64" in data
    assert "detections" in data
    assert "count" in data
    assert "processing_time_ms" in data


def test_detect_image_invalid_extension(client):
    fake_bytes = b"this is not an image"
    response = client.post(
        "/api/detect/image",
        files={"file": ("test.txt", fake_bytes, "text/plain")},
        data={"confidence": "0.25"},
    )
    assert response.status_code == 400


def test_detect_image_invalid_confidence(client):
    image_bytes = _make_fake_image_bytes("JPEG")
    response = client.post(
        "/api/detect/image",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        data={"confidence": "1.5"},  # ngoài khoảng [0, 1]
    )
    assert response.status_code == 400


def test_detect_video_invalid_extension(client):
    fake_bytes = b"not a real video"
    response = client.post(
        "/api/detect/video",
        files={"file": ("test.mov", fake_bytes, "video/quicktime")},
        data={"confidence": "0.25"},
    )
    assert response.status_code == 400