import pytest
from app_python.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    with app.test_client() as client:
        yield client
