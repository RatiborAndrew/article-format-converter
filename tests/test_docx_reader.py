import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from article_format_converter.docx_reader import read_docx_text


class DocxReaderTest(unittest.TestCase):
    def test_reads_paragraphs_and_footnotes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "sample.docx"
            _write_minimal_docx(path)

            text, footnotes = read_docx_text(path)

        self.assertIn("Первый абзац", text)
        self.assertIn("Второй абзац", text)
        self.assertEqual(footnotes, ["Текст сноски"])


def _write_minimal_docx(path: Path) -> None:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Первый абзац</w:t></w:r></w:p>
    <w:p><w:r><w:t>Второй абзац</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    footnotes_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:footnote w:id="-1"><w:p><w:r><w:t>separator</w:t></w:r></w:p></w:footnote>
  <w:footnote w:id="1"><w:p><w:r><w:t>Текст сноски</w:t></w:r></w:p></w:footnote>
</w:footnotes>
"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/footnotes.xml", footnotes_xml)


if __name__ == "__main__":
    unittest.main()
