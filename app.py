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

            vacancies, source_stats = run(
                CORE_TERMS,
                with_stats=True,
            )

            st.session_state["vacancies"] = vacancies
            st.session_state["source_stats"] = source_stats
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


source_stats = st.session_state.get("source_stats", [])

if source_stats:
    with st.expander("Collector diagnostics", expanded=True):
        for item in source_stats:
            st.markdown(
                f"**{item['source']}** — collected: "
                f"{item['collected']}"
            )

            if item["error"]:
                st.error(item["error"])

            details = item.get("details") or {}

            if details:
                st.json(details)


if vacancies:

    st.metric(
        "Power BI vacancies",
        len(vacancies),
    )


if vacancies:

    rows = []

    for vacancy in vacancies:

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

    def esc(value):
        return (
            str(value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    table_rows = []

    for row in rows:
        remote = "✓" if row["Remote"] else "—"
        table_rows.append(
            f"""
            <tr>
                <td class="score">{esc(row["Score"])}</td>
                <td class="title">{esc(row["Title"])}</td>
                <td>{esc(row["Company"])}</td>
                <td>{esc(row["Employment"])}</td>
                <td class="remote">{remote}</td>
                <td>{esc(row["Salary"])}</td>
                <td>{esc(row["Source"])}</td>
                <td class="description">{esc(row["Description"])}</td>
                <td><a href="{esc(row["Vacancy"])}" target="_blank">Open vacancy</a></td>
            </tr>
            """
        )

    table_html = f"""
    <style>
        .vacancy-table-wrap {{
            width: 100%;
            max-height: 900px;
            overflow: auto;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 8px;
        }}
        .vacancy-table {{
            width: 100%;
            min-width: 900px;
            border-collapse: collapse;
            table-layout: fixed;
            font-size: 14px;
        }}
        .vacancy-table th,
        .vacancy-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.18);
            vertical-align: top;
            text-align: left;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
            line-height: 1.35;
        }}
        .vacancy-table th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: var(--background-color);
            font-weight: 600;
        }}
        .vacancy-table th:nth-child(1) {{ width: 6%; }}
        .vacancy-table th:nth-child(2) {{ width: 20%; }}
        .vacancy-table th:nth-child(3) {{ width: 11%; }}
        .vacancy-table th:nth-child(4) {{ width: 9%; }}
        .vacancy-table th:nth-child(5) {{ width: 6%; }}
        .vacancy-table th:nth-child(6) {{ width: 10%; }}
        .vacancy-table th:nth-child(7) {{ width: 8%; }}
        .vacancy-table th:nth-child(8) {{ width: 24%; }}
        .vacancy-table th:nth-child(9) {{ width: 6%; }}
        .vacancy-table .score {{ font-weight: 700; }}
        .vacancy-table .remote {{ text-align: center; }}
        .vacancy-table a {{
            white-space: nowrap;
        }}
    </style>
    <div class="vacancy-table-wrap">
        <table class="vacancy-table">
            <thead>
                <tr>
                    <th>Score</th>
                    <th>Title</th>
                    <th>Company</th>
                    <th>Employment</th>
                    <th>Remote</th>
                    <th>Salary</th>
                    <th>Source</th>
                    <th>Description</th>
                    <th>Vacancy</th>
                </tr>
            </thead>
            <tbody>
                {"".join(table_rows)}
            </tbody>
        </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)

elif not search_error:

    st.info(
        "Press Search Power BI vacancies to start."
    )
