import unittest


try:
    from fastapi.testclient import TestClient

    from article_format_converter.api import app
except (ImportError, RuntimeError):
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI test dependencies are not installed")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_serves_web_interface(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Конвертор научных статей", response.text)

    def test_analyze_text_endpoint(self):
        response = self.client.post(
            "/analyze-text",
            data={
                "profile_id": "pravoslavny-teolog",
                "text": "Название\nАвтор\n\nАннотация: коротко\nКлючевые слова: одно, два\n\nТекст",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile_id"], "pravoslavny-teolog")
        self.assertIn("results", payload)

    def test_rejects_non_docx_upload(self):
        response = self.client.post(
            "/analyze-docx",
            data={"profile_id": "pravoslavny-teolog"},
            files={"file": ("article.txt", b"plain text", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
