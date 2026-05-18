import unittest
from pathlib import Path


WEB_DIR = Path(__file__).parents[1] / "src" / "article_format_converter" / "web"


class WebAssetsTest(unittest.TestCase):
    def test_web_assets_exist(self):
        self.assertTrue((WEB_DIR / "index.html").exists())
        self.assertTrue((WEB_DIR / "styles.css").exists())
        self.assertTrue((WEB_DIR / "app.js").exists())

    def test_index_links_static_assets(self):
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('/static/styles.css', html)
        self.assertIn('/static/app.js', html)


if __name__ == "__main__":
    unittest.main()
