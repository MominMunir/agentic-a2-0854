from fastapi.testclient import TestClient

from apps.api.main import app


def test_article_is_public_and_attributes_the_author():
    with TestClient(app) as client:
        response = client.get("/blog/gigbid")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Muhammad Momin Munir" in response.text
    assert "The retriever that lost to its baseline" in response.text
    assert "synthetic" in response.text
    assert chr(8212) not in response.text
