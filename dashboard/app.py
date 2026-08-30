from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "enade.duckdb"

st.set_page_config(page_title="ENADE 2023 | Unifor", layout="wide")
st.title("ENADE 2023 — desempenho acadêmico")

if not DB_PATH.exists():
    st.error("Execute o pipeline antes de abrir o dashboard.")
    st.stop()

con = duckdb.connect(str(DB_PATH), read_only=True)
co_ies = 555
st.sidebar.success("Universidade de Fortaleza — UNIFOR (IES 555)")

unifor = con.execute(
    """
    SELECT * FROM gold_desempenho_curso
    WHERE co_ies = ?
    ORDER BY media_nt_ger DESC NULLS LAST
    """,
    [co_ies],
).df()

c1, c2, c3 = st.columns(3)
c1.metric("Cursos", f"{unifor['co_curso'].nunique():,}".replace(",", "."))
c2.metric("Áreas", f"{unifor['co_grupo'].nunique():,}".replace(",", "."))
c3.metric("Notas válidas", f"{int(unifor['quantidade_notas_validas'].sum()):,}".replace(",", "."))

st.subheader("Cursos e áreas da IES")
st.dataframe(
    unifor[["co_curso", "nome_area", "modalidade", "media_nt_ger"]],
    use_container_width=True,
    hide_index=True,
)

modalidades = con.execute("SELECT * FROM gold_modalidade").df()
st.subheader("Presencial x EaD — Brasil")
st.plotly_chart(
    px.bar(modalidades, x="modalidade", y="media_nt_ger", text_auto=".2f"),
    use_container_width=True,
)

st.subheader("Top 10 cursos da IES")
top10 = unifor.dropna(subset=["media_nt_ger"]).head(10)
st.plotly_chart(
    px.bar(
        top10.sort_values("media_nt_ger"),
        x="media_nt_ger",
        y="nome_area",
        orientation="h",
        text_auto=".2f",
        labels={"nome_area": "Curso/área", "media_nt_ger": "Nota média"},
    ),
    use_container_width=True,
)
