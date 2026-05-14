import tempfile
import pytest
from unittest.mock import patch
import json
import os
import random
import shutil
from datetime import datetime, timedelta


# Random Data Generation Functions
def generate_mouse_movements(file_path, start_seconds, seconds_offset, num):
    with open(file_path, "w") as f:
        for _ in range(25):
            current_seconds = start_seconds + seconds_offset
            time = str(timedelta(seconds=current_seconds))
            value1 = round(random.random(), 3)  # Random float between 0 and 1
            value2 = random.randint(0, 999)
            value3 = random.randint(0, 499)
            f.write(f"{time},{value1},{value2},{value3}\n")
            seconds_offset += random.randint(0, 1)


def generate_mouse_scrolls(file_path, start_seconds, seconds_offset, num):
    with open(file_path, "w") as f:
        for _ in range(25):
            current_seconds = start_seconds + seconds_offset
            time = str(timedelta(seconds=current_seconds))
            value1 = round(random.random(), 3)  # Random float between 0 and 1
            value2 = random.randint(400, 1200)
            value3 = random.randint(350, 450)
            f.write(f"{time},{value1},{value2},{value3}\n")
            seconds_offset += random.randint(0, 1)


def generate_mouse_clicks(file_path, start_seconds, seconds_offset, num):
    with open(file_path, "w") as f:
        for _ in range(25):
            current_seconds = start_seconds + seconds_offset
            time = str(timedelta(seconds=current_seconds))
            value1 = round(random.random(), 3)  # Random float between 0 and 1
            value2 = random.randint(400, 1200)
            value3 = random.randint(350, 450)
            f.write(f"{time},{value1},{value2},{value3}\n")
            seconds_offset += random.randint(0, 1)


def generate_keyboard_inputs(file_path, start_seconds, seconds_offset, num):
    with open(file_path, "w") as f:
        for _ in range(25):
            current_seconds = start_seconds + seconds_offset
            time = str(timedelta(seconds=current_seconds))
            value1 = round(random.random(), 3)  # Random float between 0 and 1
            value2 = random.randint(400, 1200)
            value3 = random.randint(350, 450)
            f.write(f"{time},{value1},{value2},{value3}\n")
            seconds_offset += random.randint(0, 1)


@pytest.fixture
def mock_filesystem(client):
    # Create a temporary directory for the base directory
    with tempfile.TemporaryDirectory() as base_dir:
        # Generate data for 3 participants
        start_seconds = 10000  # Starting time (seconds)
        seconds_offset = 0  # Initial offset

        client.post("/insert_participant_sessions")

        for i in range(1, 4):  # For 3 participants
            participant_dir = os.path.join(base_dir, f"{i}_participant_session_id")
            os.makedirs(participant_dir, exist_ok=True)

            for j in range(1, 5):  # For 4 session types
                session_dir = os.path.join(
                    participant_dir, f"{j}_session_data_instance_id"
                )
                os.makedirs(session_dir, exist_ok=True)

                # Generate the file paths
                file_path = os.path.join(session_dir, f"{i}_session_{j}.csv")

                # Generate the data based on session type
                if j == 1:
                    generate_mouse_movements(
                        file_path, start_seconds, seconds_offset, i
                    )
                elif j == 2:
                    generate_mouse_scrolls(file_path, start_seconds, seconds_offset, i)
                elif j == 3:
                    generate_mouse_clicks(file_path, start_seconds, seconds_offset, i)
                elif j == 4:
                    generate_keyboard_inputs(
                        file_path, start_seconds, seconds_offset, i
                    )

                # Simulate posting the file path to the database (mocking actual logic)
                client.post(f"/update_database/file_path/{i}/{j}")

        # Yield the client and base_dir to be used in the test
        yield client, base_dir

        # Cleanup is handled automatically by tempfile.TemporaryDirectory


def test_get_all_session_data_instance_from_participant_zip_success(
    mock_filesystem,
):
    # Extract
    client, _ = mock_filesystem
    response = client.get("/get_all_session_data_instance_from_participant_zip/1")
    assert response.status_code == 200


def test_get_all_session_data_instance_from_participant_zip_fail_no_participant(
    mock_filesystem,
):
    # Extract
    client, _ = mock_filesystem
    response = client.get("/get_all_session_data_instance_from_participant_zip/64")
    assert response.status_code == 404


def test_get_all_session_data_instance_from_participant_session_zip_success(
    mock_file_system,
):
    # Extract
    client, _ = mock_filesystem
    response = client.get(
        "/get_all_session_data_instance_from_participant_session_zip/1"
    )
    assert response.status_code == 200
