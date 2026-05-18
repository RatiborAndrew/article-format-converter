from __future__ import annotations

from pathlib import Path
from typing import Iterable
from zipfile import ZipFile
import xml.etree.ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}


def read_docx_text(path: str | Path) -> tuple[str, list[str]]:
    """Extract paragraphs and footnotes from a DOCX file using OOXML directly."""
    file_path = Path(path)
    with ZipFile(file_path) as archive:
        document_xml = archive.read("word/document.xml")
        footnotes_xml = archive.read("word/footnotes.xml") if "word/footnotes.xml" in archive.namelist() else None

    paragraphs = _extract_paragraphs(document_xml)
    footnotes = _extract_footnotes(footnotes_xml) if footnotes_xml else []
    return "\n".join(paragraphs), footnotes


def _extract_paragraphs(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        text = _join_text_nodes(paragraph)
        if text.strip():
            paragraphs.append(text.strip())
    return paragraphs


def _extract_footnotes(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    footnotes: list[str] = []
    for footnote in root.findall(".//w:footnote", NS):
        footnote_id = footnote.attrib.get(f"{{{WORD_NS}}}id")
        if footnote_id in {"-1", "0"}:
            continue
        text = " ".join(_join_text_nodes(paragraph) for paragraph in footnote.findall(".//w:p", NS)).strip()
        if text:
            footnotes.append(text)
    return footnotes


def _join_text_nodes(element: ET.Element) -> str:
    parts: Iterable[str] = (text_node.text or "" for text_node in element.findall(".//w:t", NS))
    return "".join(parts)
