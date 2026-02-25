"""
Tests for the Mergington High School API.

Each test follows the Arrange-Act-Assert (AAA) pattern:
  - Arrange: set up the preconditions for the test.
  - Act:     perform the action under test (HTTP request).
  - Assert:  verify the response matches expectations.

State is reset between tests by the `client` fixture in conftest.py.
"""


def test_root_redirects(client):
    # Arrange — no extra setup; clean state is provided by the fixture

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all(client):
    # Arrange — no extra setup; clean state is provided by the fixture

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_signup_valid(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "new@test.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert new_email in participants


def test_signup_unknown_activity_returns_404(client):
    # Arrange
    unknown_activity = "Unknown Activity"
    email = "student@test.com"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404


def test_signup_duplicate_email_returns_400(client):
    # Arrange — michael@mergington.edu is pre-seeded in Chess Club
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email},
    )

    # Assert
    assert response.status_code == 400  # fails until duplicate-guard is added to app


def test_signup_capacity_exceeded_returns_400(client):
    # Arrange — Chess Club has max_participants=12 and starts with 2 members;
    #            fill the remaining 10 slots so it is at capacity.
    activity_name = "Chess Club"
    for i in range(10):
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": f"student{i}@test.com"},
        )

    # Act — attempt to sign up one more student beyond capacity
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@test.com"},
    )

    # Assert
    assert response.status_code == 400  # fails until capacity-guard is added to app
