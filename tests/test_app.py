import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# capture the original state so we can reset before each test
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Automatically run before each test.

    Clear the shared `activities` dict and repopulate it with a deep copy
    of the original data so tests cannot interfere with one another.
    """
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


def test_get_activities_contains_known_entries():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # make sure some of the hard‑coded activities are present
    assert "Chess Club" in data
    assert "Programming Class" in data
    # sanity‑check one of the participant lists
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]


def test_post_signup_success():
    email = "newstudent@mergington.edu"
    resp = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Signed up {email} for Chess Club"
    # verify the in‑memory state was updated
    assert email in activities["Chess Club"]["participants"]


def test_post_signup_duplicate_email():
    # michael is already signed up in the original data
    email = "michael@mergington.edu"
    resp = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up for this activity"


def test_post_signup_invalid_activity():
    resp = client.post(
        "/activities/Nonexistent/signup", params={"email": "foo@mergington.edu"}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_delete_signup_success():
    email = "michael@mergington.edu"
    # ensure participant is present initially
    assert email in activities["Chess Club"]["participants"]
    resp = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Removed {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_delete_signup_duplicate_removal_error():
    email = "notregistered@mergington.edu"
    resp = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student not signed up for this activity"


def test_delete_signup_invalid_activity():
    resp = client.delete(
        "/activities/Unknown/signup", params={"email": "any@mergington.edu"}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
