from config import CORE_TERMS, SIDE_INCOME_TERMS


def normalize(text: str) -> str:
    """
    Normalize text for scoring.
    """

    return " ".join(
        (text or "")
        .lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


# ============================================================
# ROLE SIGNALS
# ============================================================

CORE_STRONG = (
    "power bi",
    "power bi developer",
    "power bi analyst",
    "power bi engineer",
    "business intelligence",
    "business intelligence analyst",
    "business intelligence developer",
    "bi analyst",
    "bi developer",
    "bi engineer",
    "data analyst",
    "data analytics",
    "data visualization",
    "reporting analyst",
    "report developer",
    "reporting developer",
)

CORE_ADJACENT = (
    "business analyst",
    "technical business analyst",
    "system analyst",
    "systems analyst",
    "product analyst",
    "product data analyst",
    "sql analyst",
    "analytics specialist",
    "data specialist",
    "reporting",
    "analytics",
)

SIDE_STRONG = (
    "technical writer",
    "technical content writer",
    "seo writer",
    "seo content writer",
    "article writer",
    "content writer",
    "copywriter",
    "content editor",
    "proofreader",
    "research writer",
)

SIDE_GENERAL = (
    "editor",
    "content specialist",
)


# ============================================================
# SCORE
# ============================================================

def score(vacancy):
    """
    Calculate vacancy relevance score.

    IMPORTANT:
    The score is based primarily on the TITLE.
    Description keywords have lower weight because a vacancy
    may mention many technologies or professions that are not
    the actual role.
    """

    title = normalize(
        vacancy.title
    )

    description = normalize(
        vacancy.description
    )

    # --------------------------------------------------------
    # CORE
    # --------------------------------------------------------

    core_strong_hits = sum(
        1
        for term in CORE_STRONG
        if term in title
    )

    core_adjacent_hits = sum(
        1
        for term in CORE_ADJACENT
        if term in title
    )

    # Additional evidence from description.
    #
    # Only a small contribution because description can contain
    # incidental references.
    core_description_hits = sum(
        1
        for term in CORE_STRONG
        if term in description
    )

    # --------------------------------------------------------
    # SIDE INCOME
    # --------------------------------------------------------

    side_strong_hits = sum(
        1
        for term in SIDE_STRONG
        if term in title
    )

    side_general_hits = sum(
        1
        for term in SIDE_GENERAL
        if term in title
    )

    side_description_hits = sum(
        1
        for term in SIDE_STRONG
        if term in description
    )

    # --------------------------------------------------------
    # Determine primary role
    # --------------------------------------------------------

    core_score = (
        core_strong_hits * 25
        + core_adjacent_hits * 18
        + min(core_description_hits, 2) * 5
    )

    side_score = (
        side_strong_hits * 25
        + side_general_hits * 15
        + min(side_description_hits, 2) * 4
    )

    # --------------------------------------------------------
    # Category
    #
    # Core wins when both tracks are present.
    # --------------------------------------------------------

    if core_score >= side_score and core_score > 0:

        vacancy.category = (
            "Core/Adjacent BI & Data"
        )

        role_score = core_score

    elif side_score > 0:

        vacancy.category = (
            "Side Income"
        )

        role_score = side_score

    else:

        vacancy.category = (
            "Other"
        )

        role_score = 0

    # --------------------------------------------------------
    # Remote bonus
    # --------------------------------------------------------

    remote_bonus = (
        10
        if vacancy.remote
        else 0
    )

    # --------------------------------------------------------
    # Part-time bonus
    #
    # Particularly useful for Side Income.
    # --------------------------------------------------------

    employment = normalize(
        vacancy.employment_type
    )

    part_time_bonus = 0

    if (
        "part time" in employment
        or "неповна зайнятість" in employment
        or "часткова зайнятість" in employment
    ):

        if vacancy.category == "Side Income":
            part_time_bonus = 10
        else:
            part_time_bonus = 5

    # --------------------------------------------------------
    # Seniority bonus
    #
    # Junior is already excluded by pipeline.
    # --------------------------------------------------------

    seniority_bonus = 0

    if any(
        marker in title
        for marker in (
            "senior",
            "lead",
            "principal",
            "head",
            "director",
        )
    ):
        seniority_bonus = 5

    elif "middle" in title:
        seniority_bonus = 3

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    vacancy.score = min(
        100,
        30
        + role_score
        + remote_bonus
        + part_time_bonus
        + seniority_bonus,
    )

    return vacancy