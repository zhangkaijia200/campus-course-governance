import os
import random
from urllib.parse import urlparse
from uuid import uuid4
from gevent.lock import Semaphore
from locust import HttpUser, between, task

TARGET = os.getenv("TARGET_BASE_URL", "http://backend:8000")
parsed = urlparse(TARGET)
if parsed.hostname not in {"backend", "localhost", "127.0.0.1"}:
    raise RuntimeError("Safety guard: load test target must be the local demo stack")


class SharedTokenStudent(HttpUser):
    """Every virtual device shares the exact same JWT for student1."""

    host = TARGET
    wait_time = between(0.2, 0.8)
    _token_lock = Semaphore()
    _shared_token: str | None = None

    def on_start(self):
        with self._token_lock:
            if type(self)._shared_token is None:
                response = self.client.post(
                    "/auth/login",
                    json={"username": "student1", "password": "demo123"},
                    name="/auth/login [bootstrap]",
                )
                response.raise_for_status()
                type(self)._shared_token = response.json()["access_token"]
        self.token = type(self)._shared_token
        self.device_id = f"locust-device-{uuid4().hex[:10]}"

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Device-Id": self.device_id,
        }

    @task(6)
    def queued_selection(self):
        course_id = random.randint(1, 4)
        self.client.post(
            f"/courses/{course_id}/select?mode=queued",
            headers=self.headers,
            name="/courses/:id/select?mode=queued",
        )

    @task(2)
    def list_courses(self):
        self.client.get("/courses", headers=self.headers)
