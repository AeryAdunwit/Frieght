import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_public_config_endpoint(self):
        response = self.client.get("/public-config")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("admin_auth_enabled", payload)
        self.assertIn("scg_recaptcha_site_key", payload)


if __name__ == "__main__":
    unittest.main()
