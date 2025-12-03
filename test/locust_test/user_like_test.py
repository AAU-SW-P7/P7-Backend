"""Locust load test for the search endpoint."""
import random
import time
from locust import HttpUser, task, between

class SearchLoadTestUser(HttpUser):
    """A Locust user class to perform load testing on the search endpoint."""
    wait_time = between(20, 45)

    @task
    def search(self):
        """Task to perform search requests."""
        query = ["test","test account","test case","test plan","test account plan"]
        user_id = 1  # User id that all the load test requests will use
        random_nr = random.randint(1, 5)
        for nr in range(0, random_nr):
            self.client.get(
                f"/api/search/?user_id={user_id}&search_string={query[nr]}",
                headers={"x-internal-auth": "p7"}
                )
            wait_duration = random.uniform(10, 20)
            time.sleep(wait_duration)
