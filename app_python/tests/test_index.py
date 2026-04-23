def test_index_status_code(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_structure(client):
    response = client.get("/")
    data = response.get_json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_service_fields(client):
    response = client.get("/")
    service = response.get_json()["service"]

    assert service["name"] == "devops-info-service"
    assert service["framework"] == "Flask"
    assert isinstance(service["version"], str)


def test_system_fields_exist(client):
    response = client.get("/")
    system = response.get_json()["system"]

    required_fields = [
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ]

    for field in required_fields:
        assert field in system


def test_runtime_fields(client):
    response = client.get("/")
    runtime = response.get_json()["runtime"]

    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert runtime["timezone"] == "UTC"
    assert isinstance(runtime["uptime_seconds"], int)


def test_request_info(client):
    response = client.get("/", headers={"User-Agent": "pytest-agent"})
    request_data = response.get_json()["request"]

    assert request_data["method"] == "GET"
    assert request_data["path"] == "/"
    assert request_data["user_agent"] == "pytest-agent"
