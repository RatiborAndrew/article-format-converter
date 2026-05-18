import unittest

from article_format_converter.parser import parse_text
from article_format_converter.service import analyze_text


def _valid_article_text() -> str:
    abstract = " ".join(["слово"] * 100)
    body = " ".join(["Основной текст исследования."] * 600)
    return f"""УДК 2-1
Название статьи
иерей И. И. Иванов

Аннотация: {abstract}
Ключевые слова: богословие, патристика, литургика, экзегеза, традиция

{body}

Список источников и литературы
Иванов И. И. Название книги. М.: Издательство, 2020. 200 с.

Article Title
Abstract: {abstract}
Keywords: theology, patristics, liturgy, exegesis, tradition
References
Ivanov I. I. Book Title. Moscow, 2020.
"""


class ParserAndRulesTest(unittest.TestCase):
    def test_parse_article_blocks(self):
        document = parse_text(_valid_article_text())

        self.assertEqual(document.udc, "2-1")
        self.assertEqual(document.title_ru, "Название статьи")
        self.assertEqual(document.author_ru, "иерей И. И. Иванов")
        self.assertEqual(len(document.keywords_ru), 5)
        self.assertEqual(document.title_en, "Article Title")
        self.assertIsNotNone(document.bibliography)
        self.assertNotIn("Article Title", document.bibliography)
        self.assertIsNotNone(document.references)

    def test_valid_article_passes_critical_checks(self):
        report = analyze_text(_valid_article_text())

        failed_critical = [
            result for result in report.results if result.status.value == "failed" and result.severity.value == "critical"
        ]
        self.assertEqual(failed_critical, [])

    def test_short_abstract_is_reported(self):
        text = _valid_article_text().replace(" ".join(["слово"] * 100), "короткая аннотация", 1)
        report = analyze_text(text)

        abstract_result = next(result for result in report.results if result.rule_id == "volume.abstract_ru")
        self.assertEqual(abstract_result.status.value, "failed")
        self.assertIn("слишком короткая", abstract_result.message)

    def test_missing_bibliography_is_reported(self):
        text = _valid_article_text().split("Список источников и литературы", maxsplit=1)[0]
        report = analyze_text(text)

        bibliography_result = next(result for result in report.results if result.rule_id == "structure.bibliography")
        self.assertEqual(bibliography_result.status.value, "failed")


if __name__ == "__main__":
    unittest.main()
