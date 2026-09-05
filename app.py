import streamlit as st
import pandas as pd
from config import CORE_TERMS, SIDE_INCOME_TERMS
from pipeline import run

st.set_page_config(page_title="Personal Job Aggregator", layout="wide")
st.title("Personal Job Aggregator")
st.caption("Remote vacancies: Djinni · DOU · robota.ua · Work.ua")

with st.sidebar:
    st.header("Search")
    mode=st.multiselect("Tracks",["Core/Adjacent BI & Data","Side Income"],default=["Core/Adjacent BI & Data","Side Income"])
    extra=st.text_area("Additional search terms","")
    max_rows=st.slider("Results",10,200,50)
    run_search=st.button("Search vacancies",type="primary")

if run_search:
    terms=[]
    if "Core/Adjacent BI & Data" in mode: terms += CORE_TERMS
    if "Side Income" in mode: terms += SIDE_INCOME_TERMS
    terms += [x.strip() for x in extra.splitlines() if x.strip()]
    with st.spinner("Collecting vacancies…"):
        vacancies,errors=run(list(dict.fromkeys(terms)))
    st.session_state["vacancies"]=vacancies
    st.session_state["errors"]=errors

vacancies=st.session_state.get("vacancies",[])
errors=st.session_state.get("errors",[])
if errors:
    st.warning("Some sources could not be collected. The aggregator continues with available sources.")
if vacancies:
    rows=[]
    for v in vacancies[:max_rows]:
        rows.append({"Category":v.category,"Score":round(v.score),"Title":v.title,"Company":v.company,"Employment":v.employment_type,"Remote":v.remote,"Salary":v.salary,"Source":v.source,"Description":(v.description[:240]+"…") if len(v.description)>240 else v.description,"Link":v.url})
    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True,hide_index=True,column_config={"Link":st.column_config.LinkColumn("Vacancy")})
else:
    st.info("Choose tracks and press Search vacancies.")
