from io import BytesIO

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_parking_detection_rejects_non_image_upload():
    response = client.post(
        "/api/parking/detect",
        files={"image": ("payload.txt", BytesIO(b"not an image"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only JPEG, PNG, and WebP images are supported"


def test_parking_detection_accepts_supported_image_types():
    for content_type in ("image/jpeg", "image/png", "image/webp"):
        response = client.post(
            "/api/parking/detect",
            files={"image": ("parking", BytesIO(b"image data"), content_type)},
        )

        assert response.status_code == 200
        assert len(response.json()["slots"]) == 10
