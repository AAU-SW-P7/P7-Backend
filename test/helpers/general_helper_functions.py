"""Helper functions for all tests."""

import os
from datetime import datetime, timezone

from repository.user import get_user
from repository.service import save_service
from p7.create_user.api import create_user

def create_x_users(count: int):
    """Create multiple users using the create_user function."""
    for _ in range(count):
        create_user("p7")

def create_service(provider, user_id):
    """Helper function to create a service"""
    user_id = os.getenv(f"TEST_USER_{provider}_ID_{user_id}")
    oauth_type = os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_id}")
    oauth_token = os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_id}")
    access_token = os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_id}")
    access_token_expiration = os.getenv(
        f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_id}"
    )
    refresh_token = os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_id}")
    name = os.getenv(f"TEST_USER_{provider}_NAME_{user_id}")
    account_id = os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_id}")
    email = os.getenv(f"TEST_USER_{provider}_EMAIL_{user_id}")
    scope_name = os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_id}")

    # Save service and link to user
    user = get_user(user_id)
    save_service(
        user,
        oauth_type,
        oauth_token,
        access_token,
        access_token_expiration,
        refresh_token,
        name,
        account_id,
        email,
        scope_name,
        datetime.now(timezone.utc),
    )
