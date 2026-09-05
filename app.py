import streamlit as st
import pandas as pd

from config import CORE_TERMS, SIDE_INCOME_TERMS
from pipeline import run


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Personal Job Aggregator",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("Personal Job Aggregator")

st.caption(
    "Remote vacancies: Djinni · DOU · robota.ua"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Search")

    mode = st.multiselect(
        "Tracks",
        [
            "Core/Adjacent BI & Data",
            "Side Income",
        ],
        default=[
            "Core/Adjacent BI & Data",
            "Side Income",
        ],
    )

    extra = st.text_area(
        "Additional search terms",
        "",
        placeholder=(
            "Example:\n"
            "Power BI Developer\n"
            "Technical Writer"
        ),
    )

    max_rows = st.slider(
        "Results",
        min_value=10,
        max_value=200,
        value=50,
    )

    run_search = st.button(
        "Search vacancies",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# SEARCH
# ============================================================

if run_search:

    terms = []

    if (
        "Core/Adjacent BI & Data"
        in mode
    ):
        terms += CORE_TERMS

    if (
        "Side Income"
        in mode
    ):
        terms += SIDE_INCOME_TERMS

    # Additional user terms.
    terms += [
        x.strip()
        for x in extra.splitlines()
        if x.strip()
    ]

    # Remove duplicate search terms.
    terms = list(
        dict.fromkeys(
            terms
        )
    )

    if not terms:

        st.warning(
            "Choose at least one track "
            "or enter additional search terms."
        )

    else:

        with st.spinner(
            "Collecting vacancies…"
        ):

            try:

                vacancies = run(
                    terms
                )

                st.session_state[
                    "vacancies"
                ] = vacancies

                st.session_state[
                    "search_error"
                ] = ""

            except Exception as exc:

                st.session_state[
                    "vacancies"
                ] = []

                st.session_state[
                    "search_error"
                ] = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )


# ============================================================
# RESULTS
# ============================================================

vacancies = st.session_state.get(
    "vacancies",
    [],
)

search_error = st.session_state.get(
    "search_error",
    "",
)


# ============================================================
# ERROR
# ============================================================

if search_error:

    st.error(
        "Search failed"
    )

    st.code(
        search_error
    )


# ============================================================
# SUMMARY
# ============================================================

if vacancies:

    core_count = sum(
        1
        for vacancy in vacancies
        if vacancy.category
        == "Core/Adjacent BI & Data"
    )

    side_count = sum(
        1
        for vacancy in vacancies
        if vacancy.category
        == "Side Income"
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:
        st.metric(
            "Relevant vacancies",
            len(vacancies),
        )

    with col2:
        st.metric(
            "Core / BI & Data",
            core_count,
        )

    with col3:
        st.metric(
            "Side Income",
            side_count,
        )


# ============================================================
# TABLE
# ============================================================

if vacancies:

    rows = []

    for vacancy in vacancies[
        :max_rows
    ]:

        description = (
            vacancy.description
            or ""
        )

        if len(description) > 300:

            description = (
                description[:300]
                + "…"
            )

        rows.append(
            {
                "Category": vacancy.category,
                "Score": round(
                    vacancy.score or 0
                ),
                "Title": vacancy.title,
                "Company": vacancy.company,
                "Employment": (
                    vacancy.employment_type
                ),
                "Remote": vacancy.remote,
                "Salary": vacancy.salary,
                "Source": vacancy.source,
                "Description": description,
                "Vacancy": vacancy.url,
            }
        )

    df = pd.DataFrame(
        rows
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score",
                format="%d",
            ),
            "Remote": st.column_config.CheckboxColumn(
                "Remote",
            ),
            "Vacancy": st.column_config.LinkColumn(
                "Vacancy",
                display_text="Open vacancy",
            ),
        },
    )


# ============================================================
# EMPTY STATE
# ============================================================

elif not search_error:

    st.info(
        "Choose tracks and press "
        "Search vacancies."
    )