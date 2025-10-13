import pytest
from ninja.testing import TestClient
from p7.create_user.api import create_user_router

@pytest.fixture
def client():
    return TestClient(create_user_router)

def test_create_user_success(mocker, client):
    # Mock internal auth validation to return None (success)
    mocker.patch("p7.helpers.validate_internal_auth", return_value=None)
    # Mock save_user to return a user object with id
    mock_user = type("User", (), {"id": 123})()
    mocker.patch("repository.user.save_user", return_value=mock_user)
    headers = {"x-internal-auth": "valid_token"}
    response = client.post("/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"id": 123}

def test_create_user_invalid_auth(mocker, client):
    # Mock internal auth validation to return error response
    mocker.patch("p7.helpers.validate_internal_auth", return_value={"error": "invalid auth"})
    headers = {"x-internal-auth": "invalid_token"}
    response = client.post("/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"error": "invalid auth"}