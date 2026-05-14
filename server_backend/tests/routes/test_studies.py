import json
import pytest
from unittest.mock import patch


@pytest.fixture
def create_study_submission_data():
    return {
        "studyName": "Sample Study on User Behavior",
        "studyDescription": "This study is focused on understanding how users interact with new technology.",
        "studyDesignType": "Within",
        "participantCount": 50,
        "tasks": [
            {
                "taskName": "Product Selection",
                "taskDescription": "Participants will choose a product based on certain criteria.",
                "taskDirections": "Select a product you find most appealing from the list.",
                "taskDuration": 10,
                "measurementOptions": ["Mouse Movement", "Mouse Scrolls"],
            },
            {
                "taskName": "Feedback Submission",
                "taskDescription": "Participants will provide feedback on the product they selected.",
                "taskDirections": "Rate the product and give a brief reason for your choice.",
                "taskDuration": 5,
                "measurementOptions": ["Mouse Movement", "Mouse Clicks"],
            },
        ],
        "factors": [
            {
                "factorName": "Age Group",
                "factorDescription": "The age group of the participants, which could affect product selection.",
            },
            {
                "factorName": "Gender",
                "factorDescription": "The gender of the participants, which may influence their feedback.",
            },
        ],
    }


def test_get_study_data_code_success(client):
    response = client.get("/get_study_data/1")
    assert response.status_code == 200


def test_get_study_data_code_fail_no_user(client):
    response = client.get("/get_study_data/1000")
    assert response.status_code == 404


def test_load_study_success(client):
    response = client.get("/load_study/1")
    assert response.status_code == 200


def test_load_study_fail(client):
    response = client.get("/load_study/1000")
    assert response.status_code == 500


def test_delete_study_success(client):
    response = client.post("/delete_study/1/1")
    assert response.status_code == 200


def test_delete_study_fail_not_owner(client):
    response = client.post("/delete_study/10/1")
    assert response.status_code == 403


def test_create_study_code_success(client, create_study_submission_data):
    response = client.post("/create_study/1", json=create_study_submission_data)
    assert response.status_code == 200


def test_create_study_code_fail_no_user(client, create_study_submission_data):
    response = client.post("/create_study/1000", json=create_study_submission_data)
    assert response.status_code == 500


# this should break because sessions exist BUT test_db does not yet have sessions
def test_overwite_study_code_success_owner(client, create_study_submission_data):
    response = client.put("/overwrite_study/1/1", json=create_study_submission_data)
    assert response.status_code == 200


def test_overwite_study_code_success_editor(client, create_study_submission_data):
    response = client.put("/overwrite_study/1/8", json=create_study_submission_data)
    assert response.status_code == 200


def test_overwite_study_code_fail_no_study(client, create_study_submission_data):
    response = client.put("/overwrite_study/1/1000", json=create_study_submission_data)
    assert response.status_code == 404
    assert json.loads(response.data) == {"error": "Study does not exist"}


def test_overwite_study_code_fail_no_access(client, create_study_submission_data):
    response = client.put("/overwrite_study/1/2", json=create_study_submission_data)
    assert response.status_code == 404
    assert json.loads(response.data) == {"error": "User does not have access to study"}


def test_overwite_study_code_fail_only_viewer(client, create_study_submission_data):
    response = client.put("/overwrite_study/1/10", json=create_study_submission_data)
    assert response.status_code == 404
    assert json.loads(response.data) == {"error": "User may only view this study"}


def test_overwite_study_code_fail_code_bad_json(client):
    response = client.put("/overwrite_study/1/1", json={"hello": "i will destroy you"})
    assert response.status_code == 500
