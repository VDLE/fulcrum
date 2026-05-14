import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from io import BytesIO

# Setup import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes.analytics import analytics_bp
from flask import Flask


class TestAnalyticsRoutes(unittest.TestCase):
    def setUp(self):
        # Create Flask test app with our blueprint
        self.app = Flask(__name__)
        self.app.register_blueprint(analytics_bp)
        self.client = self.app.test_client()

        # Mock the database connection
        self.db_patcher = patch("app.routes.analytics.get_db_connection")
        self.mock_db = self.db_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_db.return_value = self.mock_conn

    def tearDown(self):
        # Clean up patchers
        self.db_patcher.stop()

    @patch("app.routes.analytics.get_study_summary")
    def test_get_study_summary(self, mock_get_summary):
        # Setup mock summary data
        mock_summary = {
            "participantCount": 25,
            "avgCompletionTime": 342.5,
            "successRate": 87.2,
            "metrics": [],
        }
        mock_get_summary.return_value = mock_summary

        # Send request to the endpoint
        response = self.client.get("/api/analytics/123/summary")

        # Check response code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), mock_summary)
        mock_get_summary.assert_called_once_with(self.mock_conn, "123")
        self.mock_conn.close.assert_called_once()

    @patch("app.routes.analytics.get_learning_curve_data")
    def test_get_learning_curve(self, mock_get_learning_curve):
        # Setup mock learning curve data
        mock_data = [
            {
                "taskId": 1,
                "taskName": "Task 1",
                "attempt": 1,
                "completionTime": 120.5,
                "errorCount": 2.5,
            },
            {
                "taskId": 1,
                "taskName": "Task 1",
                "attempt": 2,
                "completionTime": 95.2,
                "errorCount": 1.8,
            },
        ]
        mock_get_learning_curve.return_value = mock_data

        # Send request to the endpoint
        response = self.client.get("/api/analytics/123/learning-curve")

        # Check response code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), mock_data)
        mock_get_learning_curve.assert_called_once_with(self.mock_conn, "123")
        self.mock_conn.close.assert_called_once()

    @patch("app.routes.analytics.get_task_performance_data")
    def test_get_task_performance(self, mock_get_task_performance):
        # Setup mock task performance data
        mock_data = [
            {
                "taskId": 1,
                "taskName": "Task 1",
                "avgCompletionTime": 120.5,
                "successRate": 85.0,
                "errorRate": 2.3,
                "avgErrors": 3.1,
            }
        ]
        mock_get_task_performance.return_value = mock_data

        # Send request to the endpoint
        response = self.client.get("/api/analytics/123/task-performance")

        # Check response code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), mock_data)
        mock_get_task_performance.assert_called_once_with(self.mock_conn, "123")
        self.mock_conn.close.assert_called_once()

    @patch("app.routes.analytics.get_participant_data")
    def test_get_participants(self, mock_get_participant_data):
        # Setup mock participant data
        mock_data = [
            {
                "participantId": "P001",
                "sessionCount": 2,
                "completionTime": 450.2,
                "successRate": 75.0,
                "errorCount": 12,
            }
        ]
        mock_get_participant_data.return_value = mock_data

        # Send request to the endpoint
        response = self.client.get("/api/analytics/123/participants")

        # Check response code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), mock_data)
        mock_get_participant_data.assert_called_once_with(self.mock_conn, "123")
        self.mock_conn.close.assert_called_once()

    @patch("app.routes.analytics.get_study_summary")
    @patch("app.routes.analytics.get_task_performance_data")
    @patch("app.routes.analytics.get_participant_data")
    def test_export_data_csv(
        self, mock_get_participant_data, mock_get_task_performance, mock_get_summary
    ):
        # Setup mock data for all three data sources
        mock_summary = {
            "participantCount": 25,
            "avgCompletionTime": 342.5,
            "successRate": 87.2,
        }
        mock_task_performance = [
            {
                "taskId": 1,
                "taskName": "Task 1",
                "avgCompletionTime": 120.5,
                "successRate": 85.0,
                "errorRate": 2.3,
            }
        ]
        mock_participants = [
            {
                "participantId": "P001",
                "sessionCount": 2,
                "completionTime": 450.2,
                "successRate": 75.0,
                "errorCount": 12,
            }
        ]

        mock_get_summary.return_value = mock_summary
        mock_get_task_performance.return_value = mock_task_performance
        mock_get_participant_data.return_value = mock_participants

        # Request CSV export
        response = self.client.get("/api/analytics/123/export?format=csv")

        # Check response headers and status
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertTrue("attachment" in response.headers["Content-Disposition"])

        # Verify CSV content contains our data
        csv_data = response.data.decode("utf-8")
        self.assertIn("Study Summary", csv_data)
        self.assertIn("Task Performance", csv_data)
        self.assertIn("Participant Data", csv_data)
        self.assertIn("Task 1", csv_data)
        self.assertIn("P001", csv_data)

    @patch("app.routes.analytics.get_study_summary")
    @patch("app.routes.analytics.get_task_performance_data")
    @patch("app.routes.analytics.get_participant_data")
    def test_export_data_json(
        self, mock_get_participant_data, mock_get_task_performance, mock_get_summary
    ):
        # Setup mock data for all three data sources
        mock_summary = {
            "participantCount": 25,
            "avgCompletionTime": 342.5,
            "successRate": 87.2,
        }
        mock_task_performance = [
            {
                "taskId": 1,
                "taskName": "Task 1",
                "avgCompletionTime": 120.5,
                "successRate": 85.0,
                "errorRate": 2.3,
            }
        ]
        mock_participants = [
            {
                "participantId": "P001",
                "sessionCount": 2,
                "completionTime": 450.2,
                "successRate": 75.0,
                "errorCount": 12,
            }
        ]

        mock_get_summary.return_value = mock_summary
        mock_get_task_performance.return_value = mock_task_performance
        mock_get_participant_data.return_value = mock_participants

        # Request JSON export
        response = self.client.get("/api/analytics/123/export?format=json")

        # Check response headers and status
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertTrue("attachment" in response.headers["Content-Disposition"])

        # Verify JSON content has all three data sections
        json_data = json.loads(response.data)
        self.assertEqual(json_data["summary"], mock_summary)
        self.assertEqual(json_data["taskPerformance"], mock_task_performance)
        self.assertEqual(json_data["participants"], mock_participants)

    def test_export_data_invalid_format(self):
        # Test error handling for unsupported export format
        response = self.client.get("/api/analytics/123/export?format=xml")

        # Check for error response
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn("error", response_data)
        self.assertIn("Unsupported export format", response_data["error"])

    @patch("app.routes.analytics.get_study_summary")
    def test_error_handling(self, mock_get_summary):
        # Simulate database error
        mock_get_summary.side_effect = Exception("Database error")

        # Send request and check error handling
        response = self.client.get("/api/analytics/123/summary")

        # Check error response
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "Database error")

    @patch("app.routes.analytics.get_task_performance_data")
    @patch("app.routes.analytics.generate_task_completion_chart")
    def test_get_task_completion_chart(self, mock_generate_chart, mock_get_task_data):
        # Setup mock data
        mock_task_data = [{"taskName": "Task 1", "successRate": 85.0}]
        mock_get_task_data.return_value = mock_task_data
        mock_generate_chart.return_value = "base64_chart_data"

        # Send request to visualization endpoint
        response = self.client.get("/api/analytics/123/visualizations/task-completion")

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["chartType"], "taskCompletion")
        self.assertEqual(response_data["imageData"], "base64_chart_data")
        self.assertEqual(response_data["format"], "base64")

    @patch("app.routes.analytics.get_task_performance_data")
    @patch("app.routes.analytics.generate_error_rate_chart")
    def test_get_error_rate_chart(self, mock_generate_chart, mock_get_task_data):
        # Setup mock data
        mock_task_data = [{"taskName": "Task 1", "errorRate": 2.5}]
        mock_get_task_data.return_value = mock_task_data
        mock_generate_chart.return_value = "base64_chart_data"

        # Send request to visualization endpoint
        response = self.client.get("/api/analytics/123/visualizations/error-rate")

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["chartType"], "errorRate")
        self.assertEqual(response_data["imageData"], "base64_chart_data")
        self.assertEqual(response_data["format"], "base64")

    @patch("app.routes.analytics.get_learning_curve_data")
    @patch("app.routes.analytics.plot_to_base64")
    def test_get_learning_curve_chart(
        self, mock_plot_to_base64, mock_get_learning_data
    ):
        # Setup mock data
        mock_learning_data = [
            {"taskName": "Task 1", "attempt": 1, "completionTime": 120.5},
            {"taskName": "Task 1", "attempt": 2, "completionTime": 95.2},
        ]
        mock_get_learning_data.return_value = mock_learning_data
        mock_plot_to_base64.return_value = "base64_chart_data"

        # Send request to visualization endpoint
        response = self.client.get("/api/analytics/123/visualizations/learning-curve")

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["chartType"], "learningCurve")
        self.assertEqual(response_data["imageData"], "base64_chart_data")
        self.assertEqual(response_data["format"], "base64")


if __name__ == "__main__":
    unittest.main()
