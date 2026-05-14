import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import json
import pytest
import sys
import os

# Set up import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utility.analytics.data_processor import (
    get_study_summary,
    get_learning_curve_data,
    get_task_performance_data,
    get_participant_data,
)

from app.utility.analytics.visualization_helper import (
    plot_to_base64,
    generate_task_completion_chart,
    calculate_interaction_metrics,
)


@pytest.fixture
def mock_db_connection():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def study_id():
    return "test_study_123"


@pytest.fixture
def sample_task_data():
    return [
        {"taskId": 1, "taskName": "Task 1", "successRate": 85.0},
        {"taskId": 2, "taskName": "Task 2", "successRate": 75.5},
    ]


@pytest.fixture
def sample_interaction_data():
    return [
        {"type": "mouse_click"},
        {"type": "mouse_click"},
        {"type": "key_press"},
        {"type": "key_press"},
        {"type": "key_press"},
        {"type": "mouse_move"},
        {"type": "mouse_move"},
        {"type": "mouse_move"},
        {"type": "mouse_move"},
        {"type": "scroll"},
        {"type": "scroll"},
    ]


def test_get_study_summary(mock_db_connection, study_id):
    conn, cursor = mock_db_connection

    # Setup mock database responses
    cursor.fetchone.side_effect = [
        (25,),  # Number of participants
        (300.5,),  # Average time to complete
        (85.2,),  # Success rate percentage
        (5,),  # Number of tasks
        (3.7,),  # Average errors per attempt
    ]

    # Test with fixed random values
    with patch("numpy.random.uniform", return_value=5.0):
        result = get_study_summary(conn, study_id)

    # Check database was queried correctly
    assert cursor.execute.call_count == 5

    # Check result values match expected data
    assert isinstance(result, dict)
    assert result["participantCount"] == 25
    assert result["avgCompletionTime"] == 300.5
    assert result["successRate"] == 85.2
    assert result["taskCount"] == 5
    assert result["avgErrorCount"] == 3.7

    # Check metrics array
    assert "metrics" in result
    assert len(result["metrics"]) == 4

    # Check that each metric has all required fields
    for metric in result["metrics"]:
        assert "title" in metric
        assert "value" in metric
        assert "icon" in metric
        assert "color" in metric


def test_get_learning_curve_data(mock_db_connection, study_id):
    conn, cursor = mock_db_connection

    # Mock database results
    cursor.fetchall.side_effect = [
        [(1, "Task 1"), (2, "Task 2")],  # Tasks list
        [(1, 120.5, 2.5), (2, 95.2, 1.8)],  # First task attempts
        [(1, 150.3, 3.2), (2, 110.5, 2.1)],  # Second task attempts
    ]

    # Get learning curve data
    result = get_learning_curve_data(conn, study_id)

    # Verify database queries
    assert cursor.execute.call_count == 3

    # Check result format
    assert isinstance(result, list)
    assert len(result) == 4  # 2 tasks × 2 attempts

    # Verify data for first attempt
    assert result[0]["taskId"] == 1
    assert result[0]["taskName"] == "Task 1"
    assert result[0]["attempt"] == 1
    assert result[0]["completionTime"] == 120.5
    assert result[0]["errorCount"] == 2.5


def test_get_task_performance_data(mock_db_connection, study_id):
    conn, cursor = mock_db_connection

    # Set up mock return values for fetchall
    cursor.fetchall.side_effect = [
        [(1, "Task 1"), (2, "Task 2")],  # Tasks
    ]

    cursor.fetchone.side_effect = [
        (100.5, 85.0, 2.5),  # Performance data for Task 1
        (120.3, 75.5, 3.2),  # Performance data for Task 2
    ]

    # Get task performance data
    result = get_task_performance_data(conn, study_id)

    # Verify test expectations
    assert len(result) == 2

    # Verify data for first task
    task1 = result[0]
    assert task1["taskId"] == 1
    assert task1["taskName"] == "Task 1"
    assert task1["avgCompletionTime"] == 100.5
    assert task1["successRate"] == 85.0
    assert isinstance(task1["errorRate"], float)


def test_get_participant_data(mock_db_connection, study_id):
    conn, cursor = mock_db_connection

    # Mock participant data
    cursor.fetchall.side_effect = [
        [("P001",), ("P002",)],  # Participant IDs
        [(1, 350.2, "completed"), (2, 420.5, "failed")],  # First participants sessions
        [(1, 280.5, "completed")],  # Second participants sessions
    ]

    cursor.fetchone.side_effect = [
        (15,),  # First participants error count
        (8,),  # Second participants error count
    ]

    # Get participant data
    result = get_participant_data(conn, study_id)

    # Verify database queries
    assert cursor.execute.call_count == 5

    # Check result format
    assert isinstance(result, list)
    assert len(result) == 2  # 2 participants

    # Verify first participants data
    p1 = result[0]
    assert p1["participantId"] == "P001"
    assert p1["sessionCount"] == 2
    assert p1["completionTime"] == 350.2 + 420.5
    assert p1["successRate"] == 50.0  # 1 of 2 sessions completed
    assert p1["errorCount"] == 15


@patch("matplotlib.pyplot.savefig")
def test_plot_to_base64(mock_savefig):
    # Test conversion of plot to base64 image
    def mock_plot_function():
        pass

    # Convert plot to base64
    with patch("io.BytesIO") as mock_bytesio:
        mock_bytesio.return_value.read.return_value = b"test_image_data"
        result = plot_to_base64(mock_plot_function)

    # Verify result type
    assert isinstance(result, str)


@patch("app.utility.analytics.visualization_helper.plot_to_base64")
def test_generate_task_completion_chart(mock_plot_to_base64, sample_task_data):
    # Mock the base64 conversion
    mock_plot_to_base64.return_value = "base64_chart_data"

    # Generate chart
    result = generate_task_completion_chart(sample_task_data)

    # Verify result and function call
    assert result == "base64_chart_data"
    assert mock_plot_to_base64.call_count == 1


def test_calculate_interaction_metrics(sample_interaction_data):
    # Calculate metrics for a 60-second duration
    result = calculate_interaction_metrics(sample_interaction_data, 60)

    # Verify structure and values
    assert isinstance(result, dict)
    assert "clicks" in result
    assert "keyPresses" in result
    assert "mouseMoves" in result
    assert "scrolls" in result

    # Check interaction rates
    assert result["clicks"] == 2
    assert result["keyPresses"] == 3
    assert result["mouseMoves"] == 4
    assert result["scrolls"] == 2


def test_calculate_interaction_metrics_empty_data():
    # Test empty dataset
    result = calculate_interaction_metrics([], 60)

    # Check zeros returned
    assert result["clicks"] == 0
    assert result["keyPresses"] == 0
    assert result["mouseMoves"] == 0
    assert result["scrolls"] == 0


def test_calculate_interaction_metrics_zero_duration():
    # Test zero duration edge case
    result = calculate_interaction_metrics([{"type": "mouse_click"}], 0)

    # Check proper handling
    assert result["clicks"] == 0
    assert result["keyPresses"] == 0
    assert result["mouseMoves"] == 0
    assert result["scrolls"] == 0
