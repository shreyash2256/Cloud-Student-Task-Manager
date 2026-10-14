"""
Unit & Integration Test Suite for Cloud-Based Student Task Manager
-----------------------------------------------------------------
Academic Practical Testing for GMIU Practical Examination
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import app as flask_app


class StudentTaskManagerTestCase(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_01_home_page_renders_successfully(self):
        """Verify the main web dashboard loads with HTTP 200 and expected branding."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html_data = response.data.decode("utf-8")
        self.assertIn("Student Task Manager", html_data)
        self.assertIn("GMIU Practical Examination", html_data)
        self.assertIn("Google Cloud Firestore", html_data)
        self.assertIn("Google Cloud Run", html_data)

    def test_02_status_endpoint_reports_diagnostics(self):
        """Verify /api/status endpoint returns structured diagnostic JSON."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn("cloud_compute", data)
        self.assertIn("cloud_database", data)
        self.assertIn("server_time", data)

    def test_03_create_task_validation_missing_title(self):
        """Verify input validation rejects empty task title with HTTP 400."""
        # Even if firestore client is mocked or checked, input validation occurs
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_get_client.return_value = (mock_db, None)

            response = self.client.post(
                "/api/tasks",
                data=json.dumps({"title": "", "subject": "Cloud Computing"}),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("title is required", data["error"].lower())

    def test_04_create_task_validation_title_too_long(self):
        """Verify input validation rejects excessively long task title."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_get_client.return_value = (mock_db, None)

            response = self.client.post(
                "/api/tasks",
                data=json.dumps({"title": "A" * 150, "subject": "Cloud Computing"}),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertIn("120 characters", data["error"])

    def test_05_local_store_fallback(self):
        """Verify API responds gracefully with local persistent storage when Firestore is not configured."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_get_client.return_value = (None, "Credentials not configured")

            response = self.client.get("/api/tasks")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["storage"], "local_store")
            self.assertIsInstance(data["tasks"], list)

    def test_06_mocked_firestore_create_and_fetch(self):
        """Verify task creation and retrieval flow with Firestore client."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc_ref = MagicMock()

            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc_ref

            mock_get_client.return_value = (mock_db, None)

            # Test Create Task
            payload = {
                "title": "Submit Cloud Computing Practical Record",
                "subject": "Cloud Computing",
                "priority": "High",
                "due_date": "2026-10-30",
                "description": "Complete GMIU practical file with screenshots"
            }
            response = self.client.post(
                "/api/tasks",
                data=json.dumps(payload),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 201)
            create_data = response.get_json()
            self.assertTrue(create_data["success"])
            self.assertEqual(create_data["task"]["title"], payload["title"])
            self.assertFalse(create_data["task"]["is_completed"])

            # Verify Firestore set() was called
            mock_doc_ref.set.assert_called_once()

    def test_07_mocked_firestore_toggle_completion(self):
        """Verify task toggle endpoint flips is_completed flag in Firestore."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc_ref = MagicMock()
            mock_doc_snapshot = MagicMock()

            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value = mock_doc_snapshot

            mock_doc_snapshot.exists = True
            mock_doc_snapshot.to_dict.return_value = {
                "task_id": "test-id-123",
                "title": "Study Cloud Architecture",
                "is_completed": False
            }

            mock_get_client.return_value = (mock_db, None)

            response = self.client.patch("/api/tasks/test-id-123/toggle")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertTrue(data["is_completed"])
            mock_doc_ref.update.assert_called_once()

    def test_08_mocked_firestore_delete_task(self):
        """Verify task deletion endpoint invokes delete() on Firestore document."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_doc_ref = MagicMock()
            mock_doc_snapshot = MagicMock()

            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value = mock_doc_snapshot

            mock_doc_snapshot.exists = True
            mock_get_client.return_value = (mock_db, None)

            response = self.client.delete("/api/tasks/test-id-123")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            mock_doc_ref.delete.assert_called_once()

    def test_09_mocked_firestore_seed_samples(self):
        """Verify seeding demo tasks writes batch into Firestore."""
        with patch.object(flask_app, "get_firestore_client") as mock_get_client:
            mock_db = MagicMock()
            mock_batch = MagicMock()
            mock_db.batch.return_value = mock_batch
            mock_get_client.return_value = (mock_db, None)

            response = self.client.post("/api/seed-samples")
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertGreater(data["count"], 0)
            mock_batch.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
