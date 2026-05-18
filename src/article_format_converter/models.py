from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"
    INFO = "info"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: Severity
    requirement: str


@dataclass
class CheckResult:
    rule_id: str
    title: str
    severity: Severity
    status: CheckStatus
    message: str
    location: str | None = None
    suggested_fix: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "location": self.location,
            "suggested_fix": self.suggested_fix,
            "details": self.details,
        }


@dataclass
class ArticleDocument:
    raw_text: str
    title_ru: str | None = None
    author_ru: str | None = None
    udc: str | None = None
    abstract_ru: str | None = None
    keywords_ru: list[str] = field(default_factory=list)
    body: str = ""
    bibliography: str | None = None
    title_en: str | None = None
    abstract_en: str | None = None
    keywords_en: list[str] = field(default_factory=list)
    references: str | None = None
    footnotes: list[str] = field(default_factory=list)

    @property
    def body_characters_with_spaces(self) -> int:
        return len(self.body)

    @property
    def abstract_ru_words(self) -> int:
        if not self.abstract_ru:
            return 0
        return len([word for word in self.abstract_ru.split() if word.strip()])


@dataclass(frozen=True)
class JournalProfile:
    id: str
    name: str
    version: str
    source_urls: tuple[str, ...]
    body_min_chars: int
    body_max_chars: int
    abstract_min_words: int
    keywords_min: int
    keywords_max: int


@dataclass
class AnalysisReport:
    profile_id: str
    profile_name: str
    status: CheckStatus
    results: list[CheckResult]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "status": self.status.value,
            "metrics": self.metrics,
            "results": [result.to_dict() for result in self.results],
        }
