from __future__ import annotations

import re

from article_format_converter.models import ArticleDocument


_UDC_RE = re.compile(r"^\s*УДК\b[:\s]*(?P<value>.+)$", re.IGNORECASE)
_ABSTRACT_RE = re.compile(r"^\s*(Аннотация|Аннотация\.|Резюме)\s*[:.]?\s*(?P<value>.*)$", re.IGNORECASE)
_KEYWORDS_RE = re.compile(
    r"^\s*(Ключевые\s+слова|Ключевые\s+слова\.|Keywords|Key\s+words)\s*[:.]?\s*(?P<value>.*)$",
    re.IGNORECASE,
)
_BIBLIOGRAPHY_RE = re.compile(
    r"^\s*(Список\s+источников\s+и\s+литературы|Источники\s+и\s+литература|Список\s+литературы|Литература|Источники)\s*$",
    re.IGNORECASE,
)
_REFERENCES_RE = re.compile(r"^\s*References\s*$", re.IGNORECASE)
_ABSTRACT_EN_RE = re.compile(r"^\s*Abstract\s*[:.]?\s*(?P<value>.*)$", re.IGNORECASE)


def parse_text(raw_text: str, footnotes: list[str] | None = None) -> ArticleDocument:
    """Parse a plain-text article draft into coarse logical blocks."""
    lines = [line.strip() for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    non_empty = [line for line in lines if line]
    doc = ArticleDocument(raw_text=raw_text, footnotes=footnotes or [])

    body_lines: list[str] = []
    bibliography_lines: list[str] = []
    references_lines: list[str] = []
    section = "front_matter"
    for index, line in enumerate(lines):
        if not line:
            continue

        udc_match = _UDC_RE.match(line)
        if udc_match and doc.udc is None:
            doc.udc = udc_match.group("value").strip()
            continue

        abstract_match = _ABSTRACT_RE.match(line)
        if abstract_match and doc.abstract_ru is None:
            doc.abstract_ru = _collect_inline_or_following_text(lines, index, abstract_match.group("value"))
            section = "front_matter"
            continue

        keywords_match = _KEYWORDS_RE.match(line)
        if keywords_match:
            keywords = _split_keywords(keywords_match.group("value"))
            if "keyword" in keywords_match.group(1).lower():
                doc.keywords_en = keywords
                section = "english"
            elif not doc.keywords_ru:
                doc.keywords_ru = keywords
                section = "body"
            continue

        abstract_en_match = _ABSTRACT_EN_RE.match(line)
        if abstract_en_match and doc.abstract_en is None:
            doc.abstract_en = _collect_inline_or_following_text(lines, index, abstract_en_match.group("value"))
            section = "english"
            continue

        if _BIBLIOGRAPHY_RE.match(line):
            section = "bibliography"
            continue

        if _REFERENCES_RE.match(line):
            section = "references"
            doc.title_en = doc.title_en or _infer_english_title(lines)
            continue

        if section == "bibliography" and _next_content_line_matches(lines, index, _ABSTRACT_EN_RE):
            doc.title_en = line
            section = "english"
            continue

        if section == "bibliography":
            bibliography_lines.append(line)
        elif section == "references":
            references_lines.append(line)
        elif section == "body" or _looks_like_body_start(doc, line):
            section = "body"
            body_lines.append(line)

    _infer_title_and_author(doc, non_empty)
    doc.body = "\n".join(body_lines).strip()
    doc.bibliography = "\n".join(bibliography_lines).strip() or None
    doc.references = "\n".join(references_lines).strip() or None
    doc.title_en = doc.title_en or _infer_english_title(lines)
    return doc


def _collect_inline_or_following_text(lines: list[str], index: int, inline_value: str) -> str:
    if inline_value.strip():
        return inline_value.strip()

    collected: list[str] = []
    for next_line in lines[index + 1 :]:
        stripped = next_line.strip()
        if not stripped:
            if collected:
                break
            continue
        if _KEYWORDS_RE.match(stripped) or _BIBLIOGRAPHY_RE.match(stripped) or _REFERENCES_RE.match(stripped):
            break
        collected.append(stripped)
    return " ".join(collected).strip()


def _split_keywords(value: str) -> list[str]:
    if not value:
        return []
    return [keyword.strip(" .;") for keyword in re.split(r"[,;]", value) if keyword.strip(" .;")]


def _infer_title_and_author(doc: ArticleDocument, non_empty_lines: list[str]) -> None:
    candidates = [line for line in non_empty_lines if not _UDC_RE.match(line)]
    candidates = [
        line
        for line in candidates
        if not _ABSTRACT_RE.match(line)
        and not _KEYWORDS_RE.match(line)
        and not _BIBLIOGRAPHY_RE.match(line)
        and not _REFERENCES_RE.match(line)
    ]
    if candidates and doc.title_ru is None:
        doc.title_ru = candidates[0]
    if len(candidates) > 1 and doc.author_ru is None:
        doc.author_ru = candidates[1]


def _infer_english_title(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if _ABSTRACT_EN_RE.match(line) and index > 0:
            previous = lines[index - 1].strip()
            if previous and not _KEYWORDS_RE.match(previous):
                return previous
    return None


def _next_content_line_matches(lines: list[str], index: int, pattern: re.Pattern[str]) -> bool:
    for next_line in lines[index + 1 :]:
        stripped = next_line.strip()
        if not stripped:
            continue
        return bool(pattern.match(stripped))
    return False


def _looks_like_body_start(doc: ArticleDocument, line: str) -> bool:
    if not doc.abstract_ru and not doc.keywords_ru:
        return False
    return not (
        _ABSTRACT_RE.match(line)
        or _KEYWORDS_RE.match(line)
        or _BIBLIOGRAPHY_RE.match(line)
        or _REFERENCES_RE.match(line)
    )
