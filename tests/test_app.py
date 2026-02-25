"""
Tests for the Mergington High School API (src/app.py).

Uses FastAPI's synchronous TestClient (backed by httpx).
Every test follows the Arrange-Act-Assert (AAA) pattern:
  - Arrange: prepare inputs and preconditions
  - Act:     call the endpoint under test
  - Assert:  verify the response and side-effects

An autouse fixture deep-copies the initial activities state before each test
and restores it afterwards, so signup/unregister mutations don't bleed across tests.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# ---------------------------------------------------------------------------
# Snapshot of the original activities dict captured at import time.
# This gives us a clean reference independent of any test mutations.
# ---------------------------------------------------------------------------
_ORIGINAL_ACTIVITIES = copy.deepcopy(activities)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the shared in-memory activities dict after every test."""
    yield
    activities.clear()
    activities.update(copy.deepcopy(_ORIGINAL_ACTIVITIES))


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client: TestClient):
        # Arrange — no extra setup; default activities are already seeded

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_returns_all_activities(self, client: TestClient):
        # Arrange — no extra setup; 9 activities are seeded by default

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9

    def test_known_activity_present(self, client: TestClient):
        # Arrange
        expected_activity = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        assert expected_activity in response.json()

    def test_activity_has_expected_fields(self, client: TestClient):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        chess = response.json()["Chess Club"]
        assert expected_fields.issubset(chess.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client: TestClient):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]

    def test_signup_returns_confirmation_message(self, client: TestClient):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        body = response.json()
        assert "message" in body
        assert email in body["message"]

    def test_signup_activity_not_found(self, client: TestClient):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404

    def test_signup_already_registered(self, client: TestClient):
        # Arrange — "michael@mergington.edu" is pre-seeded in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400

    def test_signup_duplicate_returns_error_detail(self, client: TestClient):
        # Arrange — "michael@mergington.edu" is pre-seeded in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert "detail" in response.json()

    def test_signup_capacity_exceeded_returns_400(self, client: TestClient):
        # Arrange — Chess Club has max_participants=12 and starts with 2 members;
        #            fill the remaining 10 slots so it is at capacity.
        activity_name = "Chess Club"
        for i in range(10):
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"student{i}@mergington.edu"},
            )

        # Act — attempt to sign up one more student beyond capacity
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"},
        )

        # Assert
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client: TestClient):
        # Arrange — "michael@mergington.edu" is pre-seeded in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]

    def test_unregister_returns_confirmation_message(self, client: TestClient):
        # Arrange — "michael@mergington.edu" is pre-seeded in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        body = response.json()
        assert "message" in body
        assert email in body["message"]

    def test_unregister_activity_not_found(self, client: TestClient):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404

    def test_unregister_not_registered(self, client: TestClient):
        # Arrange — "nobody@mergington.edu" is not in any activity
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400

    def test_unregister_not_registered_returns_error_detail(self, client: TestClient):
        # Arrange — "nobody@mergington.edu" is not in any activity
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        assert "detail" in response.json()


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self, client: TestClient):
        # Arrange — no extra setup needed

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code in (301, 302, 307, 308)

    def test_root_redirect_location(self, client: TestClient):
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/")

        # Assert
        assert response.headers["location"] == expected_location
