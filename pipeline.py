from config import (
    CORE_TERMS,
    EXCLUDE_TERMS,
    SOURCES,
)

from collectors import (
    DjinniCollector,
    DOUCollector,
    RobotaCollector,
)

from dedupe import dedupe
from scoring import score


def normalize(text: str) -> str:
    """
    Normalize text for matching.
    """

    return " ".join(
        (text or "")
        .lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def vacancy_text(vacancy) -> str:
    """
    Full searchable vacancy text.
    """

    return normalize(
        " ".join(
            [
                vacancy.title or "",
                vacancy.company or "",
                vacancy.description or "",
                vacancy.employment_type or "",
                vacancy.location or "",
            ]
        )
    )


# ============================================================
# STRICT POWER BI GATE
# ============================================================

POWER_BI_TERMS = (
    "power bi",
    "powerbi",
)


def is_power_bi_vacancy(vacancy) -> bool:
    """
    A vacancy is accepted only when Power BI is explicitly
    present in its title.

    This intentionally excludes generic BI/Data/Analytics
    vacancies that merely mention Power BI in the description.
    """

    title = normalize(vacancy.title)

    return any(
        term in title
        for term in POWER_BI_TERMS
    )


# ============================================================
# HARD EXCLUSIONS
# ============================================================

LEVEL_EXCLUDE = (
    "junior",
    "intern",
    "internship",
    "trainee",
    "entry level",
    "entrylevel",
    "no experience",
    "без досвіду",
    "без опыта",
    "початківець",
    "стажер",
    "стажування",
)

SALES_EXCLUDE = (
    "direct manager",
    "sales manager",
    "sales representative",
    "sales specialist",
    "sales executive",
    "sales agent",
    "account executive",
    "business development",
    "business development manager",
    "business development specialist",
    "lead generation",
    "lead generator",
    "chat manager",
    "chat administrator",
    "менеджер з продажу",
    "менеджер з продажів",
    "менеджер по продажам",
    "продажі",
    "продажи",
    "лідогенератор",
    "лідогенерація",
    "оператор чату",
    "адміністратор чату",
)

SMM_EXCLUDE = (
    "smm",
    "smm manager",
    "smm specialist",
    "social media manager",
    "social media specialist",
    "social media marketing",
    "social media content manager",
    "social media content specialist",
    "influencer manager",
    "community manager",
    "community specialist",
    "менеджер соціальних мереж",
    "менеджер соцмереж",
    "соціальні мережі",
)

DESIGN_EXCLUDE = (
    "video editor",
    "video editing",
    "video producer",
    "video production",
    "motion designer",
    "motion design",
    "motion graphics",
    "graphic designer",
    "graphic design",
    "ui designer",
    "ux designer",
    "ui/ux designer",
    "ux/ui designer",
    "product designer",
    "web designer",
    "visual designer",
    "3d designer",
    "3d artist",
    "animator",
    "animation designer",
    "відеомонтажер",
    "відеоредактор",
    "відео редактор",
    "моушн дизайнер",
    "графічний дизайнер",
    "дизайнер",
    "дизайнер ui",
    "дизайнер ux",
)

CONTENT_PRODUCTION_EXCLUDE = (
    "scriptwriter",
    "script writer",
    "youtube scriptwriter",
    "youtube script writer",
    "ai scriptwriter",
    "ai script writer",
    "content producer",
    "content production manager",
    "content production associate",
    "content production specialist",
    "content creator",
    "video content creator",
    "content production",
    "контент мейкер",
    "контентмейкер",
    "контент продюсер",
    "сценарист",
)

MARKETING_EXCLUDE = (
    "marketing manager",
    "marketing specialist",
    "marketing coordinator",
    "marketing executive",
    "digital marketing manager",
    "digital marketing specialist",
    "performance marketing manager",
    "affiliate manager",
    "affiliate marketing manager",
    "email marketing manager",
    "crm manager",
)

NON_REMOTE_EXCLUDE = (
    "office only",
    "office-based",
    "office based",
    "on-site only",
    "onsite only",
    "on site only",
    "office work only",
    "офісна робота",
    "робота в офісі",
    "тільки в офісі",
    "тільки офіс",
    "на місці",
)


def has_excluded_level(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in LEVEL_EXCLUDE
    )


def has_excluded_sales_role(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in SALES_EXCLUDE
    )


def has_excluded_smm_role(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in SMM_EXCLUDE
    )


def has_excluded_design_role(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in DESIGN_EXCLUDE
    )


def has_excluded_content_production_role(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in CONTENT_PRODUCTION_EXCLUDE
    )


def has_excluded_marketing_role(vacancy) -> bool:
    title = normalize(vacancy.title)

    return any(
        term in title
        for term in MARKETING_EXCLUDE
    )


def has_non_remote_marker(vacancy) -> bool:
    text = vacancy_text(vacancy)

    return any(
        term in text
        for term in NON_REMOTE_EXCLUDE
    )


def hard_excluded(vacancy) -> bool:
    """
    Hard exclusion layer.

    Any excluded vacancy is removed before scoring.
    """

    if has_excluded_level(vacancy):
        return True

    if has_excluded_sales_role(vacancy):
        return True

    if has_excluded_smm_role(vacancy):
        return True

    if has_excluded_design_role(vacancy):
        return True

    if has_excluded_content_production_role(vacancy):
        return True

    if has_excluded_marketing_role(vacancy):
        return True

    if has_non_remote_marker(vacancy):
        return True

    text = vacancy_text(vacancy)

    if any(
        normalize(term) in text
        for term in EXCLUDE_TERMS
    ):
        return True

    return False


def relevant(vacancy) -> bool:
    """
    Final relevance gate.

    ONLY explicit Power BI vacancies are allowed.
    """

    return (
        is_power_bi_vacancy(vacancy)
        and not hard_excluded(vacancy)
    )


def assign_category(vacancy) -> str:
    """
    All accepted vacancies belong to the Power BI category.
    """

    if is_power_bi_vacancy(vacancy):
        return "Power BI"

    return "Other"


def build_collectors():

    collector_map = {
        "Djinni": DjinniCollector,
        "DOU": DOUCollector,
        "robota.ua": RobotaCollector,
        "Robota.ua": RobotaCollector,
    }

    collectors = []

    for source in SOURCES:

        collector_class = collector_map.get(
            source
        )

        if collector_class:
            collectors.append(
                collector_class()
            )

    return collectors


def run(terms=None, with_stats=False):
    """
    Full Power BI vacancy aggregation pipeline.

    Steps:
    1. Collect from sources using Power BI search.
    2. Remote-only filtering.
    3. Strict Power BI title gate.
    4. Hard exclusions.
    5. Deduplication.
    6. Category assignment.
    7. Scoring.
    8. Final safety validation.
    """

    # Search is deliberately fixed to Power BI.
    terms = ["power bi"]

    vacancies = []
    source_stats = []

    for collector in build_collectors():

        try:

            collected = collector.collect(
                terms
            )

            # Detailed Robota pipeline diagnostics: show exactly where
            # collected vacancies disappear after the collector returns them.
            if collector.source == "robota.ua":
                details = getattr(collector, "last_stats", {})
                details["pipeline_titles"] = [
                    vacancy.title for vacancy in collected
                ]

                remote_items = [
                    vacancy for vacancy in collected
                    if vacancy.remote
                ]
                title_items = [
                    vacancy for vacancy in remote_items
                    if is_power_bi_vacancy(vacancy)
                ]
                hard_items = [
                    vacancy for vacancy in title_items
                    if not hard_excluded(vacancy)
                ]
                relevant_items = [
                    vacancy for vacancy in hard_items
                    if relevant(vacancy)
                ]

                details["pipeline_counts"] = {
                    "collected": len(collected),
                    "remote": len(remote_items),
                    "power_bi_title": len(title_items),
                    "after_hard_exclusions": len(hard_items),
                    "relevant": len(relevant_items),
                }
                details["pipeline_exclusion_reasons"] = {}

                for vacancy in collected:
                    reasons = []
                    if not vacancy.remote:
                        reasons.append("not_remote")
                    if not is_power_bi_vacancy(vacancy):
                        reasons.append("no_power_bi_in_title")
                    if has_excluded_level(vacancy):
                        reasons.append("excluded_level")
                    if has_excluded_sales_role(vacancy):
                        reasons.append("excluded_sales")
                    if has_excluded_smm_role(vacancy):
                        reasons.append("excluded_smm")
                    if has_excluded_design_role(vacancy):
                        reasons.append("excluded_design")
                    if has_excluded_content_production_role(vacancy):
                        reasons.append("excluded_content_production")
                    if has_excluded_marketing_role(vacancy):
                        reasons.append("excluded_marketing")
                    if has_non_remote_marker(vacancy):
                        reasons.append("non_remote_marker")

                    text = vacancy_text(vacancy)
                    if any(
                        normalize(term) in text
                        for term in EXCLUDE_TERMS
                    ):
                        reasons.append("config_exclude_term")

                    details["pipeline_exclusion_reasons"][
                        vacancy.title
                    ] = reasons or ["passes_pipeline_filters"]

            vacancies.extend(
                collected
            )

            source_stats.append(
                {
                    "source": collector.source,
                    "collected": len(collected),
                    "error": "",
                    "details": getattr(
                        collector,
                        "last_stats",
                        {},
                    ),
                }
            )

        except Exception as exc:
            # One broken source must not kill the pipeline.
            source_stats.append(
                {
                    "source": collector.source,
                    "collected": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                    "details": getattr(
                        collector,
                        "last_stats",
                        {},
                    ),
                }
            )
            continue

    vacancies = [
        vacancy
        for vacancy in vacancies
        if vacancy.remote
    ]

    vacancies = [
        vacancy
        for vacancy in vacancies
        if is_power_bi_vacancy(vacancy)
    ]

    vacancies = [
        vacancy
        for vacancy in vacancies
        if not hard_excluded(vacancy)
    ]

    vacancies = [
        vacancy
        for vacancy in vacancies
        if relevant(vacancy)
    ]

    vacancies = dedupe(vacancies)

    for vacancy in vacancies:
        vacancy.category = assign_category(vacancy)

    scored = []

    for vacancy in vacancies:

        try:
            scored.append(score(vacancy))
        except Exception:
            scored.append(vacancy)

    vacancies = scored

    # Final safety gate after scoring.
    vacancies = [
        vacancy
        for vacancy in vacancies
        if vacancy.remote
        and is_power_bi_vacancy(vacancy)
        and not hard_excluded(vacancy)
    ]

    vacancies.sort(
        key=lambda vacancy: (
            -(vacancy.score or 0),
            vacancy.title.lower(),
        )
    )

    if with_stats:
        return vacancies, source_stats

    return vacancies
