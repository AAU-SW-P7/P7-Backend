import os
import pytest_check as check

from repository.models import Service, User

payload = {
    "userId": os.getenv("TEST_USER_ID"),
    "oauthType": os.getenv("TEST_USER_OAUTHTYPE"),
    "oauthToken": os.getenv("TEST_USER_OAUTHTOKEN"),
    "accessToken": os.getenv("TEST_USER_ACCESSTOKEN"),
    "accessTokenExpiration": os.getenv("TEST_USER_ACCESSTOKENEXPIRATION"),
    "refreshToken": os.getenv("TEST_USER_REFRESHTOKEN"),
    "name": os.getenv("TEST_USER_NAME"),
    "accountId": os.getenv("TEST_USER_ACCOUNTID"),
    "email": os.getenv("TEST_USER_EMAIL"),
    "scopeName": os.getenv("TEST_USER_SCOPENAME"),
}

def assert_create_service_success(client):
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    
    check.equal(initial_user_count == 1, True) # Assuming a user is already created for service creation
    check.equal(initial_service_count == 0, True) 

    response = client.post("/", json=payload, headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})

    data = response.json()

    check.equal(response.status_code, 200)
    check.equal("id" in data, True)
    check.equal("error" not in data, True)
    check.equal(type(data["id"]) is int, True)
    
    # Assert that a new user was created in the database
    check.equal(User.objects.count(), initial_user_count)  # User count should remain the same
    check.equal(Service.objects.count(), initial_service_count + 1)

    # Assert that the service with the returned ID actually exists
    created_service = Service.objects.get(id=data["id"], name=payload["name"])
    check.is_not_none(created_service)
    check.equal(created_service.id, data["id"])

def assert_create_service_invalid_auth(client):
    response = client.post("/", json=payload, headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_create_service_missing_header(client):
    response = client.post("/", json=payload)

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string', 'type': 'string_type'}]})