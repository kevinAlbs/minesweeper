import unittest
import leaderboard
import flask
import flask.testing
import pathlib

class TestLeaderboard (unittest.TestCase):
    def setUp(self):
        self.app : flask.Flask = leaderboard.app
        self.app.config.update({
            "TESTING": True,
        })
        self.app.debug = True
        pathlib.Path("test.db").unlink(missing_ok=True)

    def testPostingScore (self):
        client : flask.testing.FlaskClient = self.app.test_client()
        response = client.post("/submit", json={
            "name": "name-test",
            "difficulty": "Beginner",
            "seconds": 123,
            "unix_time": 456,
            "uuid_str": "e1748dc1-3882-4b2b-8c5d-fb72a151a2cf"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"ok": 1})

    def testPostingDuplicateScore (self):
        client : flask.testing.FlaskClient = self.app.test_client()
        response = client.post("/submit", json={
            "name": "name-test",
            "difficulty": "Beginner",
            "seconds": 123,
            "unix_time": 456,
            "uuid_str": "e1748dc1-3882-4b2b-8c5d-fb72a151a2cf"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"ok": 1})

        response = client.post("/submit", json={
            "name": "name-test",
            "difficulty": "Beginner",
            "seconds": 123,
            "unix_time": 456,
            "uuid_str": "e1748dc1-3882-4b2b-8c5d-fb72a151a2cf"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"ok": 0, "description": "Score already saved"})

    def testPostingMissingUUID (self):
        client : flask.testing.FlaskClient = self.app.test_client()
        response = client.post("/submit", json={
            "name": "name-test",
            "difficulty": "Beginner",
            "seconds": 123
        })
        # Gets HTTP 400 (Bad Request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["ok"], 0)

    def testGet (self):
        client : flask.testing.FlaskClient = self.app.test_client()

        response = client.get("/get_top_100")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["Beginner"], [])

        score = {
            "name": "name-test",
            "difficulty": "Beginner",
            "seconds": 123,
            "unix_time": 456,
            "uuid_str": "e1748dc1-3882-4b2b-8c5d-fb72a151a2cf"
        }
        response = client.post("/submit", json=score)
        self.assertEqual(response.status_code, 200)

        response = client.get("/get_top_100")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["Beginner"], [score])

if __name__ == "__main__":
    unittest.main()