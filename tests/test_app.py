"""Автоматизовані тести API та сторінок (ізольована тимчасова БД)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server

class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(server, "DB", Path(self.temp.name) / "test.db")
        self.db_patch.start()
        server.app.config.update(TESTING=True, SECRET_KEY="testing-only")
        server.init_db()
        self.client = server.app.test_client()

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def test_homepage_and_css(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/styles.css").status_code, 200)

    def test_invalid_message_rejected(self):
        response = self.client.post("/api/messages", json={"name":"A", "email":"bad", "message":"hi"})
        self.assertEqual(response.status_code, 400)

    def test_create_and_list_message(self):
        response = self.client.post("/api/messages", json={"name":"Олег", "email":"test@example.com", "message":"Тестове повідомлення"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/messages").status_code, 401)
        with self.client.session_transaction() as session:
            session["admin"] = True
        messages = self.client.get("/api/messages").get_json()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["name"], "Олег")

    def test_delete_requires_auth_and_removes_record(self):
        created = self.client.post("/api/messages", json={"name":"Test", "email":"test@example.com", "message":"Message for delete"}).get_json()
        message_id = created["id"]
        self.assertEqual(self.client.delete(f"/api/messages/{message_id}").status_code, 401)
        with self.client.session_transaction() as session:
            session["admin"] = True
        self.assertEqual(self.client.delete(f"/api/messages/{message_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/messages").get_json(), [])

if __name__ == "__main__":
    unittest.main()
