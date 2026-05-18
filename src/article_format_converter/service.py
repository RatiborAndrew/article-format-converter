from __future__ import annotations

from pathlib import Path

from article_format_converter.docx_reader import read_docx_text
from article_format_converter.models import AnalysisReport
from article_format_converter.parser import parse_text
from article_format_converter.profiles import PROFILES
from article_format_converter.rules import run_profile_checks


def analyze_text(raw_text: str, profile_id: str = "pravoslavny-teolog") -> AnalysisReport:
    profile = _get_profile(profile_id)
    document = parse_text(raw_text)
    return run_profile_checks(document, profile)


def analyze_docx(path: str | Path, profile_id: str = "pravoslavny-teolog") -> AnalysisReport:
    profile = _get_profile(profile_id)
    raw_text, footnotes = read_docx_text(path)
    document = parse_text(raw_text, footnotes=footnotes)
    return run_profile_checks(document, profile)


def _get_profile(profile_id: str):
    try:
        return PROFILES[profile_id]
    except KeyError as error:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown profile '{profile_id}'. Available profiles: {available}") from error
