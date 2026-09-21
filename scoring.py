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


def score(vacancy):
    """
    Calculate relevance score for Power BI vacancies.

    The pipeline already applies a strict Power BI title gate,
    so scoring is used only to rank accepted Power BI roles.
    """

    title = normalize(vacancy.title)
    description = normalize(vacancy.description)

    score_value = 50

    if "power bi developer" in title:
        score_value += 20
    elif "power bi analyst" in title:
        score_value += 20
    elif "power bi engineer" in title:
        score_value += 20
    elif "power bi consultant" in title:
        score_value += 18
    elif "power bi specialist" in title:
        score_value += 15
    elif "power bi" in title:
        score_value += 10

    if vacancy.remote:
        score_value += 10

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
        score_value += 5
    elif "middle" in title:
        score_value += 3

    description_hits = sum(
        1
        for term in (
            "power bi",
            "powerbi",
            "dax",
            "power query",
            "power query m",
            "m language",
        )
        if term in description
    )

    score_value += min(description_hits * 2, 10)

    vacancy.score = min(100, score_value)
    vacancy.category = "Power BI"

    return vacancy
