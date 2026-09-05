from config import (
    CORE_TERMS,
    SIDE_INCOME_TERMS,
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


# ============================================================
# NORMALIZATION
# ============================================================

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
# HARD EXCLUSIONS
# ============================================================

# ------------------------------------------------------------
# Junior / beginner / no experience
# ------------------------------------------------------------

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
    "початківець",
    "стажер",
    "стажування",
)


# ------------------------------------------------------------
# Sales / direct management / lead generation
# ------------------------------------------------------------

SALES_EXCLUDE = (
    "direct manager",
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


# ------------------------------------------------------------
# SMM / social media
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Video / Motion / Graphic / UI / UX design
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Content-production roles that are NOT writing/editing
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Marketing roles that are not analytics
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Physical / office-only work
# ------------------------------------------------------------

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


# ============================================================
# ROLE-SPECIFIC EXCLUSIONS
# ============================================================

def has_excluded_level(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    description = normalize(
        vacancy.description
    )

    # Level should primarily be checked in title.
    # This prevents a description such as
    # "you will work with junior analysts"
    # from incorrectly excluding a senior vacancy.

    return any(
        term in title
        for term in LEVEL_EXCLUDE
    )


def has_excluded_sales_role(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    return any(
        term in title
        for term in SALES_EXCLUDE
    )


def has_excluded_smm_role(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    return any(
        term in title
        for term in SMM_EXCLUDE
    )


def has_excluded_design_role(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    return any(
        term in title
        for term in DESIGN_EXCLUDE
    )


def has_excluded_content_production_role(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    return any(
        term in title
        for term in CONTENT_PRODUCTION_EXCLUDE
    )


def has_excluded_marketing_role(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Do not exclude analytical marketing roles:
    #
    # Marketing Analyst
    # Marketing Data Analyst
    # Senior Marketing Data Analyst
    # Product Growth Analyst
    #
    # These belong to Core/Adjacent BI & Data.
    # --------------------------------------------------------

    analytical_markers = (
        "marketing analyst",
        "marketing data analyst",
        "marketing analytics",
        "marketing data",
        "growth analyst",
        "product growth analyst",
    )

    if any(
        marker in title
        for marker in analytical_markers
    ):
        return False

    return any(
        term in title
        for term in MARKETING_EXCLUDE
    )


def has_non_remote_marker(
    vacancy,
) -> bool:

    text = vacancy_text(
        vacancy
    )

    return any(
        term in text
        for term in NON_REMOTE_EXCLUDE
    )


def hard_excluded(
    vacancy,
) -> bool:
    """
    Hard exclusion layer.

    If any of these conditions is true, the vacancy
    must not reach scoring or the final result.
    """

    if has_excluded_level(
        vacancy
    ):
        return True

    if has_excluded_sales_role(
        vacancy
    ):
        return True

    if has_excluded_smm_role(
        vacancy
    ):
        return True

    if has_excluded_design_role(
        vacancy
    ):
        return True

    if has_excluded_content_production_role(
        vacancy
    ):
        return True

    if has_excluded_marketing_role(
        vacancy
    ):
        return True

    if has_non_remote_marker(
        vacancy
    ):
        return True

    # Existing global exclusions from config.py.
    text = vacancy_text(
        vacancy
    )

    if any(
        normalize(term) in text
        for term in EXCLUDE_TERMS
    ):
        return True

    return False


# ============================================================
# CORE ROLE SIGNALS
# ============================================================

CORE_STRONG_TERMS = (
    "power bi",
    "business intelligence",
    "bi analyst",
    "bi developer",
    "bi engineer",
    "power bi developer",
    "power bi analyst",
    "power bi engineer",
    "data analyst",
    "data analytics",
    "data visualization",
    "reporting analyst",
    "report developer",
    "reporting developer",
    "analytics specialist",
    "business intelligence analyst",
    "business intelligence developer",
    "business intelligence engineer",
)


CORE_ADJACENT_TERMS = (
    "business analyst",
    "technical business analyst",
    "system analyst",
    "systems analyst",
    "product analyst",
    "product data analyst",
    "data reporting",
    "reporting",
    "sql analyst",
    "data specialist",
    "analytics",
)


# ============================================================
# SIDE INCOME SIGNALS
# ============================================================

SIDE_WRITING_TERMS = (
    "content writer",
    "seo content writer",
    "seo writer",
    "seo copywriter",
    "article writer",
    "technical writer",
    "technical content writer",
    "technical copywriter",
    "copywriter",
    "content editor",
    "proofreader",
    "research writer",
    "content specialist",
    "editor",
)


# ============================================================
# TECHNICAL SUPPORT / NON-ANALYTICAL EXCLUSION
# ============================================================

TECHNICAL_SUPPORT_EXCLUDE = (
    "technical support",
    "support engineer",
    "help desk",
    "service desk",
    "customer support",
    "it support",
    "support specialist",
    "технічна підтримка",
    "служба підтримки",
)


# ============================================================
# BUSINESS ANALYST VALIDATION
# ============================================================

def valid_business_analyst(
    vacancy,
) -> bool:
    """
    Business Analyst is allowed when it is actually an
    analytical / IT / business-analysis role.

    Sales-oriented Business Development / Account roles
    are already removed by hard_excluded().
    """

    title = normalize(
        vacancy.title
    )

    description = normalize(
        vacancy.description
    )

    if "business analyst" not in title:
        return True

    analytical_signals = (
        "requirements",
        "requirements analysis",
        "business requirements",
        "functional requirements",
        "process analysis",
        "business process",
        "process modeling",
        "sql",
        "power bi",
        "data",
        "analytics",
        "reporting",
        "erp",
        "crm",
        "it",
        "system analysis",
        "systems analysis",
        "stakeholder",
        "documentation",
        "technical specification",
        "technical requirements",
        "user stories",
        "acceptance criteria",
        "бізнес процес",
        "аналіз вимог",
        "вимоги",
        "процеси",
        "sql",
        "дані",
        "аналітика",
        "erp",
        "crm",
    )

    return any(
        signal in description
        for signal in analytical_signals
    )


# ============================================================
# SIDE INCOME VALIDATION
# ============================================================

def valid_side_income(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    description = normalize(
        vacancy.description
    )

    # --------------------------------------------------------
    # Writing roles are valid.
    # --------------------------------------------------------

    if any(
        term in title
        for term in SIDE_WRITING_TERMS
    ):
        return True

    # --------------------------------------------------------
    # Technical Writer is especially relevant.
    # --------------------------------------------------------

    if (
        "technical writer" in title
        or "technical content writer" in title
    ):
        return True

    # --------------------------------------------------------
    # Content/editor roles.
    # --------------------------------------------------------

    if (
        "editor" in title
        or "proofreader" in title
    ):
        return True

    return False


# ============================================================
# CORE VALIDATION
# ============================================================

def valid_core(
    vacancy,
) -> bool:

    title = normalize(
        vacancy.title
    )

    description = normalize(
        vacancy.description
    )

    combined = (
        f"{title} {description}"
    )

    # --------------------------------------------------------
    # Strong Core terms.
    # --------------------------------------------------------

    if any(
        term in combined
        for term in CORE_STRONG_TERMS
    ):
        return True

    # --------------------------------------------------------
    # Adjacent analytical roles.
    # --------------------------------------------------------

    if any(
        term in combined
        for term in CORE_ADJACENT_TERMS
    ):

        # Technical support should not become Data/BI.
        if any(
            term in title
            for term in TECHNICAL_SUPPORT_EXCLUDE
        ):
            return False

        return True

    # --------------------------------------------------------
    # Business Analyst.
    # --------------------------------------------------------

    if "business analyst" in title:
        return valid_business_analyst(
            vacancy
        )

    return False


# ============================================================
# RELEVANCE
# ============================================================

def relevant(
    vacancy,
) -> bool:
    """
    Final relevance gate.

    A vacancy must belong either to:
    - Core / Adjacent BI & Data
    - Side Income writing/editorial
    """

    if hard_excluded(
        vacancy
    ):
        return False

    core = valid_core(
        vacancy
    )

    side = valid_side_income(
        vacancy
    )

    # --------------------------------------------------------
    # Core takes priority for mixed roles.
    #
    # Example:
    # Business Analyst / Technical Writer
    #
    # This is an analytical/IT role, therefore Core.
    # --------------------------------------------------------

    if core:
        return True

    if side:
        return True

    return False


# ============================================================
# CATEGORY
# ============================================================

def assign_category(
    vacancy,
) -> str:
    """
    Assign final category.

    Core takes priority over Side Income for hybrid roles.
    """

    if valid_core(
        vacancy
    ):
        return "Core/Adjacent BI & Data"

    if valid_side_income(
        vacancy
    ):
        return "Side Income"

    return "Other"


# ============================================================
# COLLECTORS
# ============================================================

def build_collectors():

    collector_map = {
        "Djinni": DjinniCollector,
        "DOU": DOUCollector,
        "robota.ua": RobotaCollector,
        "Robota.ua": RobotaCollector,
    }

    collectors = []

    for source in SOURCES:

        collector_class = (
            collector_map.get(
                source
            )
        )

        if collector_class:
            collectors.append(
                collector_class()
            )

    return collectors


# ============================================================
# PIPELINE
# ============================================================

def run(
    terms=None,
):
    """
    Full vacancy aggregation pipeline.

    Steps:

    1. Collect from sources.
    2. Remote-only filtering.
    3. Hard exclusions.
    4. Relevance filtering.
    5. Deduplication.
    6. Category assignment.
    7. Scoring.
    8. Final validation.
    """

    # --------------------------------------------------------
    # Search terms
    # --------------------------------------------------------

    if terms is None:

        terms = (
            CORE_TERMS
            + SIDE_INCOME_TERMS
        )

    # Remove duplicate search terms.
    terms = list(
        dict.fromkeys(
            terms
        )
    )

    # --------------------------------------------------------
    # Collection
    # --------------------------------------------------------

    vacancies = []

    for collector in build_collectors():

        try:

            collected = (
                collector.collect(
                    terms
                )
            )

            vacancies.extend(
                collected
            )

        except Exception:
            # One broken source must not kill the pipeline.
            continue

    # --------------------------------------------------------
    # Remote-only filter
    # --------------------------------------------------------

    vacancies = [
        vacancy
        for vacancy in vacancies
        if vacancy.remote
    ]

    # --------------------------------------------------------
    # Hard exclusions BEFORE scoring.
    # --------------------------------------------------------

    vacancies = [
        vacancy
        for vacancy in vacancies
        if not hard_excluded(
            vacancy
        )
    ]

    # --------------------------------------------------------
    # Relevance filter.
    # --------------------------------------------------------

    vacancies = [
        vacancy
        for vacancy in vacancies
        if relevant(
            vacancy
        )
    ]

    # --------------------------------------------------------
    # Deduplication.
    # --------------------------------------------------------

    vacancies = dedupe(
        vacancies
    )

    # --------------------------------------------------------
    # Category.
    # --------------------------------------------------------

    for vacancy in vacancies:

        vacancy.category = (
            assign_category(
                vacancy
            )
        )

    # --------------------------------------------------------
    # Scoring.
    # --------------------------------------------------------

    scored = []

    for vacancy in vacancies:

        try:

            scored.append(
                score(
                    vacancy
                )
            )

        except Exception:

            scored.append(
                vacancy
            )

    vacancies = scored

    # --------------------------------------------------------
    # Final category assignment.
    #
    # scoring.py may modify category, so restore our
    # business-rule category.
    # --------------------------------------------------------

    for vacancy in vacancies:

        vacancy.category = (
            assign_category(
                vacancy
            )
        )

    # --------------------------------------------------------
    # Final safety filter.
    #
    # This guarantees that an unwanted vacancy cannot
    # re-enter the result because of scoring.
    # --------------------------------------------------------

    vacancies = [
        vacancy
        for vacancy in vacancies
        if vacancy.remote
        and not hard_excluded(
            vacancy
        )
        and relevant(
            vacancy
        )
    ]

    # --------------------------------------------------------
    # Sort
    #
    # Core first, then Side Income.
    # Within category, score descending.
    # --------------------------------------------------------

    category_order = {
        "Core/Adjacent BI & Data": 0,
        "Side Income": 1,
    }

    vacancies.sort(
        key=lambda vacancy: (
            category_order.get(
                vacancy.category,
                99,
            ),
            -(vacancy.score or 0),
            vacancy.title.lower(),
        )
    )

    return vacancies