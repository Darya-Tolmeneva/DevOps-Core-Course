def test_404_error(client):
    response = client.get("/nonexistent")
    data = response.get_json()

    assert response.status_code == 404
    assert data["error"] == "Not Found"
    assert "message" in data


def test_500_handler(client, monkeypatch):
    from app_python import app as app_module

    def broken_function():
        raise Exception("Test exception")

    monkeypatch.setattr(app_module, "get_system_info", broken_function)

    response = client.get("/")

    assert response.status_code == 500
    data = response.get_json()
    assert data["error"] == "Internal Server Error"
