"""
Test suite for the Mergington High School Activities API
Tests cover all endpoints: GET /activities, POST /signup, DELETE /unregister
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_email():
    """Provide a sample student email for testing"""
    return "test.student@mergington.edu"


@pytest.fixture
def new_email():
    """Provide another sample student email for testing"""
    return "new.student@mergington.edu"


# ============================================================================
# GET /activities - Tests for retrieving all activities
# ============================================================================


def test_get_activities_returns_200(client):
    """Test that GET /activities returns a 200 status code"""
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict(client):
    """Test that GET /activities returns a dictionary"""
    response = client.get("/activities")
    assert isinstance(response.json(), dict)


def test_get_activities_contains_known_activities(client):
    """Test that the response contains expected activities"""
    response = client.get("/activities")
    activities = response.json()
    
    expected_activities = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Club",
        "Track Team",
        "Art Club",
        "Drama Society",
        "Robotics Club",
        "Debate Club"
    ]
    
    for activity in expected_activities:
        assert activity in activities


def test_activity_has_required_fields(client):
    """Test that each activity has all required fields"""
    response = client.get("/activities")
    activities = response.json()
    
    required_fields = ["description", "schedule", "max_participants", "participants"]
    
    for activity_name, activity_details in activities.items():
        for field in required_fields:
            assert field in activity_details, f"Missing field '{field}' in activity '{activity_name}'"


def test_activity_participants_is_list(client):
    """Test that participants field is always a list"""
    response = client.get("/activities")
    activities = response.json()
    
    for activity_name, activity_details in activities.items():
        assert isinstance(activity_details["participants"], list), \
            f"Participants field in '{activity_name}' is not a list"


def test_activity_max_participants_is_number(client):
    """Test that max_participants is a positive number"""
    response = client.get("/activities")
    activities = response.json()
    
    for activity_name, activity_details in activities.items():
        assert isinstance(activity_details["max_participants"], int)
        assert activity_details["max_participants"] > 0


def test_initial_activities_have_participants(client):
    """Test that activities have pre-populated participants"""
    response = client.get("/activities")
    activities = response.json()
    
    for activity_name, activity_details in activities.items():
        assert len(activity_details["participants"]) > 0, \
            f"Activity '{activity_name}' should have initial participants"


# ============================================================================
# POST /activities/{activity_name}/signup - Tests for student signup
# ============================================================================


def test_signup_success(client, sample_email):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": sample_email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert sample_email in data["message"]


def test_signup_adds_participant(client):
    """Test that signup adds the participant to the activity"""
    email = "add.participant@mergington.edu"
    activity = "Programming%20Class"
    
    # Get initial count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()["Programming Class"]["participants"])
    
    # Sign up
    client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Verify count increased
    updated_response = client.get("/activities")
    updated_count = len(updated_response.json()["Programming Class"]["participants"])
    assert updated_count == initial_count + 1


def test_signup_duplicate_prevents_double_registration(client, sample_email):
    """Test that signing up twice with same email returns 400 error"""
    activity_url = "/activities/Programming%20Class/signup"
    
    # First signup
    response1 = client.post(activity_url, params={"email": sample_email})
    assert response1.status_code == 200
    
    # Second signup with same email should fail
    response2 = client.post(activity_url, params={"email": sample_email})
    assert response2.status_code == 400
    data = response2.json()
    assert "already signed up" in data["detail"].lower()


def test_signup_nonexistent_activity_returns_404(client, sample_email):
    """Test that signing up for non-existent activity returns 404"""
    response = client.post(
        "/activities/Nonexistent%20Club/signup",
        params={"email": sample_email}
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_signup_multiple_students_same_activity(client, sample_email, new_email):
    """Test that multiple different students can sign up for the same activity"""
    activity_url = "/activities/Soccer%20Club/signup"
    
    response1 = client.post(activity_url, params={"email": sample_email})
    assert response1.status_code == 200
    
    response2 = client.post(activity_url, params={"email": new_email})
    assert response2.status_code == 200
    
    # Verify both are now participants
    activities_response = client.get("/activities")
    participants = activities_response.json()["Soccer Club"]["participants"]
    assert sample_email in participants
    assert new_email in participants


# ============================================================================
# DELETE /activities/{activity_name}/unregister - Tests for unregistration
# ============================================================================


def test_unregister_success(client):
    """Test successful unregistration from an activity"""
    # Get an existing participant
    activities_response = client.get("/activities")
    existing_participant = activities_response.json()["Chess Club"]["participants"][0]
    
    response = client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": existing_participant}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Unregistered" in data["message"]


def test_unregister_removes_participant(client):
    """Test that unregister removes the participant from the activity"""
    # First, sign up
    email = "unregister.test@mergington.edu"
    client.post(
        "/activities/Track%20Team/signup",
        params={"email": email}
    )
    
    # Get count after signup
    after_signup = client.get("/activities")
    count_after_signup = len(after_signup.json()["Track Team"]["participants"])
    
    # Unregister
    client.delete(
        "/activities/Track%20Team/unregister",
        params={"email": email}
    )
    
    # Verify count decreased
    after_unregister = client.get("/activities")
    count_after_unregister = len(after_unregister.json()["Track Team"]["participants"])
    assert count_after_unregister == count_after_signup - 1


def test_unregister_nonexistent_participant_returns_400(client):
    """Test that unregistering non-existent participant returns 400"""
    response = client.delete(
        "/activities/Art%20Club/unregister",
        params={"email": "nonexistent@mergington.edu"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "not signed up" in data["detail"].lower()


def test_unregister_nonexistent_activity_returns_404(client):
    """Test that unregistering from non-existent activity returns 404"""
    response = client.delete(
        "/activities/Nonexistent%20Club/unregister",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_unregister_then_signup_again_succeeds(client, sample_email):
    """Test that after unregistering, a student can sign up again"""
    activity_url = "/activities/Drama%20Society/signup"
    unregister_url = "/activities/Drama%20Society/unregister"
    
    # Sign up
    response1 = client.post(activity_url, params={"email": sample_email})
    assert response1.status_code == 200
    
    # Unregister
    response2 = client.delete(unregister_url, params={"email": sample_email})
    assert response2.status_code == 200
    
    # Sign up again
    response3 = client.post(activity_url, params={"email": sample_email})
    assert response3.status_code == 200


# ============================================================================
# Integration tests - Complex scenarios
# ============================================================================


def test_full_workflow_signup_and_unregister(client):
    """Test complete workflow: signup, verify, unregister, verify again"""
    email = "workflow.test@mergington.edu"
    activity = "Robotics%20Club"
    
    # Step 1: Get initial state
    initial = client.get("/activities").json()
    initial_count = len(initial["Robotics Club"]["participants"])
    
    # Step 2: Sign up
    signup_response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert signup_response.status_code == 200
    
    # Step 3: Verify signup
    after_signup = client.get("/activities").json()
    assert len(after_signup["Robotics Club"]["participants"]) == initial_count + 1
    assert email in after_signup["Robotics Club"]["participants"]
    
    # Step 4: Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    assert unregister_response.status_code == 200
    
    # Step 5: Verify unregister
    after_unregister = client.get("/activities").json()
    assert len(after_unregister["Robotics Club"]["participants"]) == initial_count
    assert email not in after_unregister["Robotics Club"]["participants"]


def test_availability_updates_correctly(client, sample_email):
    """Test that available spots decrease when students sign up"""
    activity_name = "Debate Club"
    
    # Get initial availability
    initial = client.get("/activities").json()
    activity = initial[activity_name]
    initial_available = activity["max_participants"] - len(activity["participants"])
    
    # Sign up
    client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": sample_email}
    )
    
    # Check updated availability
    updated = client.get("/activities").json()
    activity = updated[activity_name]
    updated_available = activity["max_participants"] - len(activity["participants"])
    
    assert updated_available == initial_available - 1
