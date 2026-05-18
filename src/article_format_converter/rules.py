from __future__ import annotations

from collections.abc import Callable

from article_format_converter.models import (
    AnalysisReport,
    ArticleDocument,
    CheckResult,
    CheckStatus,
    JournalProfile,
    Rule,
    Severity,
)


RuleChecker = Callable[[ArticleDocument, JournalProfile, Rule], CheckResult]


def run_profile_checks(document: ArticleDocument, profile: JournalProfile) -> AnalysisReport:
    results = [checker(document, profile, rule) for rule, checker in _RULES]
    overall_status = _overall_status(results)
    return AnalysisReport(
        profile_id=profile.id,
        profile_name=profile.name,
        status=overall_status,
        results=results,
        metrics={
            "body_characters_with_spaces": document.body_characters_with_spaces,
            "abstract_ru_words": document.abstract_ru_words,
            "keywords_ru_count": len(document.keywords_ru),
            "footnotes_count": len(document.footnotes),
        },
    )


def _overall_status(results: list[CheckResult]) -> CheckStatus:
    has_failed_critical = any(
        result.status == CheckStatus.FAILED and result.severity == Severity.CRITICAL for result in results
    )
    return CheckStatus.FAILED if has_failed_critical else CheckStatus.PASSED


def _required_field(field_name: str, label: str, location: str, suggestion: str) -> RuleChecker:
    def checker(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
        value = getattr(document, field_name)
        if value:
            return CheckResult(
                rule_id=rule.id,
                title=rule.title,
                severity=rule.severity,
                status=CheckStatus.PASSED,
                message=f"Блок «{label}» найден.",
                location=location,
            )
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.FAILED,
            message=f"Блок «{label}» не найден.",
            location=location,
            suggested_fix=suggestion,
        )

    return checker


def _body_volume(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
    count = document.body_characters_with_spaces
    if profile.body_min_chars <= count <= profile.body_max_chars:
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.PASSED,
            message=f"Объем основного текста соответствует требованиям: {count} знаков с пробелами.",
            location="Основной текст",
            details={"count": count, "min": profile.body_min_chars, "max": profile.body_max_chars},
        )
    if count < profile.body_min_chars:
        message = f"Основной текст слишком короткий: {count} знаков с пробелами."
        suggestion = f"Увеличить основной текст минимум до {profile.body_min_chars} знаков с пробелами."
    else:
        message = f"Основной текст слишком длинный: {count} знаков с пробелами."
        suggestion = f"Сократить основной текст максимум до {profile.body_max_chars} знаков с пробелами."
    return CheckResult(
        rule_id=rule.id,
        title=rule.title,
        severity=rule.severity,
        status=CheckStatus.FAILED,
        message=message,
        location="Основной текст",
        suggested_fix=suggestion,
        details={"count": count, "min": profile.body_min_chars, "max": profile.body_max_chars},
    )


def _abstract_volume(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
    count = document.abstract_ru_words
    if count >= profile.abstract_min_words:
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.PASSED,
            message=f"Аннотация содержит {count} слов.",
            location="Аннотация",
            details={"count": count, "min": profile.abstract_min_words},
        )
    return CheckResult(
        rule_id=rule.id,
        title=rule.title,
        severity=rule.severity,
        status=CheckStatus.FAILED,
        message=f"Аннотация слишком короткая: {count} слов.",
        location="Аннотация",
        suggested_fix=f"Расширить аннотацию минимум до {profile.abstract_min_words} слов.",
        details={"count": count, "min": profile.abstract_min_words},
    )


def _keywords_count(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
    count = len(document.keywords_ru)
    if profile.keywords_min <= count <= profile.keywords_max:
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.PASSED,
            message=f"Количество ключевых слов соответствует требованиям: {count}.",
            location="Ключевые слова",
            details={"count": count, "min": profile.keywords_min, "max": profile.keywords_max},
        )
    return CheckResult(
        rule_id=rule.id,
        title=rule.title,
        severity=rule.severity,
        status=CheckStatus.FAILED,
        message=f"Некорректное количество ключевых слов: {count}.",
        location="Ключевые слова",
        suggested_fix=f"Указать от {profile.keywords_min} до {profile.keywords_max} ключевых слов или словосочетаний.",
        details={"count": count, "min": profile.keywords_min, "max": profile.keywords_max},
    )


def _footnotes_present(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
    if document.footnotes:
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.PASSED,
            message=f"Найдено подстрочных сносок: {len(document.footnotes)}.",
            location="Сноски",
            details={"count": len(document.footnotes)},
        )
    return CheckResult(
        rule_id=rule.id,
        title=rule.title,
        severity=rule.severity,
        status=CheckStatus.SKIPPED,
        message="Подстрочные сноски не найдены. Проверка будет актуальна для статей с цитированием источников.",
        location="Сноски",
        suggested_fix="Если в статье есть цитаты и источники, оформить ссылки постраничными подстрочными сносками.",
        details={"count": 0},
    )


def _english_metadata(document: ArticleDocument, profile: JournalProfile, rule: Rule) -> CheckResult:
    missing = []
    if not document.title_en:
        missing.append("английское название")
    if not document.abstract_en:
        missing.append("Abstract")
    if not document.keywords_en:
        missing.append("Keywords")
    if not document.references:
        missing.append("References")

    if not missing:
        return CheckResult(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            status=CheckStatus.PASSED,
            message="Английские метаданные найдены.",
            location="Английский блок",
        )
    return CheckResult(
        rule_id=rule.id,
        title=rule.title,
        severity=rule.severity,
        status=CheckStatus.FAILED,
        message="Не хватает элементов английского блока: " + ", ".join(missing) + ".",
        location="Английский блок",
        suggested_fix="Добавить английское название, сведения об авторе, Abstract, Keywords и References.",
        details={"missing": missing},
    )


_RULES: list[tuple[Rule, RuleChecker]] = [
    (
        Rule(
            id="structure.udc",
            title="УДК",
            severity=Severity.WARNING,
            requirement="В левом верхнем углу документа должен быть указан УДК.",
        ),
        _required_field("udc", "УДК", "Начало документа", "Добавить УДК в левый верхний угол документа."),
    ),
    (
        Rule(
            id="structure.title_ru",
            title="Название статьи",
            severity=Severity.CRITICAL,
            requirement="Статья должна содержать название на русском языке.",
        ),
        _required_field("title_ru", "Название статьи", "Начало документа", "Добавить название статьи на русском языке."),
    ),
    (
        Rule(
            id="structure.author_ru",
            title="Сведения об авторе",
            severity=Severity.CRITICAL,
            requirement="Статья должна содержать сведения об авторе.",
        ),
        _required_field("author_ru", "Сведения об авторе", "Начало документа", "Добавить строку автора: сан, инициалы и фамилия."),
    ),
    (
        Rule(
            id="structure.abstract_ru",
            title="Аннотация",
            severity=Severity.CRITICAL,
            requirement="Статья должна содержать аннотацию на русском языке.",
        ),
        _required_field("abstract_ru", "Аннотация", "Аннотация", "Добавить аннотацию на русском языке."),
    ),
    (
        Rule(
            id="structure.keywords_ru",
            title="Ключевые слова",
            severity=Severity.CRITICAL,
            requirement="Статья должна содержать ключевые слова на русском языке.",
        ),
        _required_field("keywords_ru", "Ключевые слова", "Ключевые слова", "Добавить 5-10 ключевых слов."),
    ),
    (
        Rule(
            id="volume.body",
            title="Объем основного текста",
            severity=Severity.CRITICAL,
            requirement="Объем основного материала должен быть от 12 000 до 40 000 знаков с пробелами.",
        ),
        _body_volume,
    ),
    (
        Rule(
            id="volume.abstract_ru",
            title="Объем аннотации",
            severity=Severity.CRITICAL,
            requirement="Аннотация должна содержать не менее 100 слов.",
        ),
        _abstract_volume,
    ),
    (
        Rule(
            id="volume.keywords_ru",
            title="Количество ключевых слов",
            severity=Severity.CRITICAL,
            requirement="Ключевые слова должны содержать от 5 до 10 слов или словосочетаний.",
        ),
        _keywords_count,
    ),
    (
        Rule(
            id="structure.bibliography",
            title="Список источников и литературы",
            severity=Severity.CRITICAL,
            requirement="После основного текста должен быть список источников и литературы.",
        ),
        _required_field(
            "bibliography",
            "Список источников и литературы",
            "После основного текста",
            "Добавить список источников и литературы после основного текста.",
        ),
    ),
    (
        Rule(
            id="structure.english_metadata",
            title="Английские метаданные",
            severity=Severity.WARNING,
            requirement="После русского списка должны быть английское название, данные автора, аннотация, ключевые слова и References.",
        ),
        _english_metadata,
    ),
    (
        Rule(
            id="citations.footnotes",
            title="Подстрочные сноски",
            severity=Severity.RECOMMENDATION,
            requirement="Ссылки на источники, кроме Священного Писания, оформляются постраничными подстрочными сносками.",
        ),
        _footnotes_present,
    ),
]
