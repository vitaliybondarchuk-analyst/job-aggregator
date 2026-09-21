import streamlit as st
import pandas as pd

from config import CORE_TERMS
from pipeline import run


st.set_page_config(
    page_title="Personal Power BI Job Aggregator",
    layout="wide",
)

st.title("Personal Power BI Job Aggregator")

st.caption(
    "Remote Power BI vacancies: Djinni · DOU · robota.ua"
)

with st.sidebar:

    st.header("Search")

    st.info(
        "Search is restricted to vacancies explicitly related "
        "to Power BI."
    )

    max_rows = st.slider(
        "Results",
        min_value=10,
        max_value=200,
        value=50,
    )

    run_search = st.button(
        "Search Power BI vacancies",
        type="primary",
        use_container_width=True,
    )


if run_search:

    with st.spinner(
        "Collecting Power BI vacancies…"
    ):

        try:

            vacancies = run(CORE_TERMS)

            st.session_state["vacancies"] = vacancies
            st.session_state["search_error"] = ""

        except Exception as exc:

            st.session_state["vacancies"] = []
            st.session_state["search_error"] = (
                f"{type(exc).__name__}: {exc}"
            )


vacancies = st.session_state.get("vacancies", [])
search_error = st.session_state.get("search_error", "")


if search_error:

    st.error("Search failed")
    st.code(search_error)


if vacancies:

    st.metric(
        "Power BI vacancies",
        len(vacancies),
    )


if vacancies:

    rows = []

    for vacancy in vacancies[:max_rows]:

        description = vacancy.description or ""

        if len(description) > 300:
            description = description[:300] + "…"

        rows.append(
            {
                "Score": round(vacancy.score or 0),
                "Title": vacancy.title,
                "Company": vacancy.company,
                "Employment": vacancy.employment_type,
                "Remote": vacancy.remote,
                "Salary": vacancy.salary,
                "Source": vacancy.source,
                "Description": description,
                "Vacancy": vacancy.url,
            }
        )

    df = pd.DataFrame(rows)

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

elif not search_error:

    st.info(
        "Press Search Power BI vacancies to start."
    )
