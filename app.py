from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from registre_textil import FONT, carrega_registre

DADES = Path(__file__).parent / "dades"

st.set_page_config(page_title="Texpaper · Compradors potencials", layout="wide")
st.title("Compradors potencials de Texpaper")

vista = st.radio("Directori", ["Registre tèxtil mundial", "Prospectes qualificats"], horizontal=True)
if vista == "Registre tèxtil mundial":
    carrega = st.cache_data(ttl=86400, show_spinner="Carregant el registre mundial…")(carrega_registre)
    try:
        registre = carrega()
    except (OSError, ValueError):
        st.error("Ara mateix el registre mundial no està disponible. Torna-ho a provar d’aquí a uns minuts.")
        st.link_button("Obre la font", FONT)
        st.stop()
    mètriques = st.columns(2)
    mètriques[0].metric("Instal·lacions tèxtils", f"{len(registre):,}".replace(",", "."))
    mètriques[1].metric("Països i territoris", registre["País (registre)"].nunique())
    st.caption("Còpia de desembre de 2022. Cal comprovar que la planta segueix activa i si compra paper de sublimació.")
    st.link_button("Font i metodologia del registre", FONT)
    resum = registre.groupby("País (registre)").size().rename("Instal·lacions").reset_index()
    mapa = px.choropleth(resum, locations="País (registre)", locationmode="country names",
                         color="Instal·lacions", hover_name="País (registre)",
                         projection="natural earth", color_continuous_scale="Teal")
    mapa.update_geos(showframe=False, showland=True, landcolor="#e7eef2")
    mapa.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(mapa, config={"scrollZoom": True})
    controls = st.columns(2)
    països_registre = sorted(registre["País (registre)"].unique())
    país_registre = controls[0].selectbox("País", ["Tot el món", *països_registre])
    cerca_registre = controls[1].text_input("Nom de la planta o regió")
    if país_registre != "Tot el món":
        registre = registre[registre["País (registre)"].eq(país_registre)]
    if cerca_registre.strip():
        text = registre["Instal·lació"] + " " + registre["Regió"]
        registre = registre[text.str.contains(cerca_registre.strip(), case=False, regex=False)]
    st.subheader(f"{len(registre):,} resultats".replace(",", "."))
    registre = registre.sort_values(["País (registre)", "Instal·lació"])
    st.dataframe(registre, hide_index=True, column_config={"Font": st.column_config.LinkColumn("Fitxa de la planta")})
    st.download_button("Descarrega la llista filtrada", registre.to_csv(index=False).encode("utf-8-sig"),
                       "registre_textil.csv", "text/csv")
    st.stop()

països = pd.read_csv(DADES / "logistica.csv").set_index("iso")["país"]
empreses = pd.read_csv(DADES / "prospectes.csv").fillna("")
empreses = empreses[empreses.estat.ne("Canal potencial")].copy()
empreses["País"] = empreses.iso.map(països)
empreses["Validació"] = empreses.estat.replace({"Procés verificat": "Procés documentat"})

comptes = empreses.groupby("iso").size()
dades_mapa = països.rename("País").reset_index()
dades_mapa["Empreses identificades"] = dades_mapa.iso.map(comptes)
fig = px.choropleth(
    dades_mapa, locations="iso", hover_name="País", color="Empreses identificades",
    color_continuous_scale="Teal", projection="natural earth",
    hover_data={"iso": False},
)
fig.update_geos(showframe=False, showland=True, landcolor="#e4ebee", showcountries=True)
fig.update_layout(height=470, margin=dict(l=0, r=0, t=0, b=0), dragmode="pan")
clic = st.plotly_chart(fig, key="mapa_compradors", on_select="rerun",
                       selection_mode="points", config={"scrollZoom": True})
punts = clic.selection.points
codi = punts[-1].get("location") if punts else None
if codi in països.index and codi != st.session_state.get("últim_clic"):
    st.session_state["país_compradors"] = països[codi]
st.session_state["últim_clic"] = codi
st.caption("Els països en gris encara no tenen compradors identificats a la base.")

controls = st.columns(2)
país = controls[0].selectbox("País", ["Tot el món", *sorted(països.unique())], key="país_compradors")
cerca = controls[1].text_input("Cerca una empresa")
if país != "Tot el món":
    empreses = empreses[empreses["País"].eq(país)]
if cerca.strip():
    empreses = empreses[empreses.empresa.str.contains(cerca.strip(), case=False, regex=False)]

taula = empreses.rename(columns={
    "empresa": "Empresa", "ciutat": "Ciutat", "categoria": "Producte possible",
    "evidencia": "Què fa i què cal confirmar", "font": "Font",
})[["País", "Empresa", "Ciutat", "Producte possible", "Què fa i què cal confirmar",
    "Validació", "Font"]].sort_values(["País", "Empresa"]).reset_index(drop=True)

if taula.empty:
    st.info("Encara no hi ha compradors identificats per a aquest país o cerca.")
else:
    st.caption(f"{len(taula)} empreses · {taula['País'].nunique()} països")
    resultat = st.dataframe(
        taula, hide_index=True, on_select="rerun", selection_mode="multi-row",
        key=f"compradors_{país}_{cerca}",
        column_config={"Font": st.column_config.LinkColumn("Font")},
    )
    files = resultat.selection.rows
    selecció = taula.iloc[files] if files else taula
    st.download_button(
        "Descarrega les seleccionades" if files else "Descarrega la llista",
        selecció.to_csv(index=False).encode("utf-8-sig"), "compradors_texpaper.csv", "text/csv",
    )
