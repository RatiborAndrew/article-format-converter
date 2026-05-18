from article_format_converter.models import JournalProfile


PRAVOSLAVNY_TEOLOG_PROFILE = JournalProfile(
    id="pravoslavny-teolog",
    name="Православный теолог",
    version="2026-05-19",
    source_urls=(
        "https://xn--80ai6adde.xn--p1ai/zhurnal-pravoslavnyy-teolog/informatsiya-dlya-avtorov/",
        "https://xn--80ai6adde.xn--p1ai/zhurnal-pravoslavnyy-teolog/pravila-oformleniya-statey/",
    ),
    body_min_chars=12_000,
    body_max_chars=40_000,
    abstract_min_words=100,
    keywords_min=5,
    keywords_max=10,
)
