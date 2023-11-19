import unittest
import leaderboard
import flask
import flask.testing

class TestLeaderboard (unittest.TestCase):
    def setUp(self):
        self.app : flask.Flask = leaderboard.app
        self.app.config.update({
            "TESTING": True,
        })

    def testPostingScore (self):
        client : flask.testing.FlaskClient = self.app.test_client()
        response = client.post("/submit", json={
            "time": "10",
            "difficulty": "easy"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"ok": 1})

if __name__ == "__main__":
    unittest.main()