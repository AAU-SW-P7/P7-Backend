"""Locust load test for the search endpoint."""
import random
import time
from urllib.parse import quote
from locust import HttpUser, task, between

class SearchLoadTestUser(HttpUser):
    """A Locust user class to perform load testing on the search endpoint."""
    wait_time = between(20, 45)

    @task
    def search(self):
        """Task to perform search requests."""
        queries = ["test", "test account", "test case", "test plan", "test account plan"]
        user_id = 1  # User id that all the load test requests will use

        # Fix: Ensure we don't exceed array bounds
        random_nr = random.randint(1, len(queries))

        for nr in range(random_nr):
            # URL encode the search string to handle spaces and special characters
            search_string = quote(queries[nr])
            self.client.get(
                f"/api/search/?user_id={user_id}&search_string={search_string}",
                headers={"x-internal-auth": "p7"}
            )
            # Simulate user reading/processing time between searches
            wait_duration = random.uniform(10, 20)
            time.sleep(wait_duration)
