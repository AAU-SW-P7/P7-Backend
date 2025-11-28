"""Locust load test for the search endpoint."""
from locust import HttpUser, task, between

class SearchLoadTestUser(HttpUser):
    """A Locust user class to perform load testing on the search endpoint."""
    wait_time = between(5, 10)

    @task
    def search(self):
        """Task to perform search requests."""
        query = "test"
        user_id = 1  # User id that all the load test requests will use
        self.client.get(
            f"/api/search/?user_id={user_id}&search_string={query}",
            headers={"x-internal-auth": "p7"}
            )

    @task
    def search2(self):
        """Task to perform search requests."""
        query = "test"
        user_id = 2  # User id that all the load test requests will use
        self.client.get(
            f"/api/search/?user_id={user_id}&search_string={query}",
            headers={"x-internal-auth": "p7"}
            )
