from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from registre_textil import FONT, carrega_registre

DADES = Path(__file__).parent / "dades"

st.set_page_config(page_title="Texpaper · Compradors potencials", layout="wide")
st.title("Compradors potencials de Texpaper")

vista = st.radio("Directori", ["Prospecció comercial", "Registre tèxtil mundial"], horizontal=True)
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
    st.subheader("A qui trucar")
    taula = taula.sort_values("Validació", ascending=False, kind="stable").reset_index(drop=True)
    seguiment = st.session_state.setdefault("seguiment_comercial", {})
    empresa = st.selectbox("Obre una fitxa comercial", taula.Empresa.tolist())
    fitxa = taula.loc[taula.Empresa.eq(empresa)].iloc[0]
    producte = fitxa["Producte possible"]
    if producte == "Protecció de calandra":
        pregunta = "Quin paper protector utilitzeu a la calandra, de quina amplada i quants rotlles consumiu al mes?"
        pas = "Si compren paper protector, demana les especificacions actuals i acorda una prova amb producció."
    elif producte == "Paper de transferència":
        pregunta = "Imprimiu sobre paper de transferència a la vostra planta? Quin format, gramatge i consum mensual teniu?"
        pas = "Si fan la impressió internament, demana una mostra del paper actual per preparar una proposta."
    else:
        pregunta = "Feu la sublimació internament? Si la subcontracteu, quin taller fa l’estampació i compra el paper?"
        pas = "Identifica qui compra el paper abans de preparar una oferta."
    with st.container(border=True):
        st.markdown(f"**{empresa}** · {fitxa['Ciutat'] or fitxa['País']}")
        st.write(fitxa["Què fa i què cal confirmar"])
        st.markdown(f"**Producte a validar** · {producte}")
        st.markdown(f"**Pregunta per al primer contacte** · {pregunta}")
        st.markdown(f"**Pas següent** · {pas}")
        st.link_button("Consulta la font", fitxa["Font"])
        estats = ["Pendent de contactar", "Ja és client", "Contactat", "Consum confirmat",
                  "Mostra enviada", "Descartat"]
        anterior = seguiment.get(empresa, (estats[0], ""))
        estat = st.selectbox("Estat comercial", estats, index=estats.index(anterior[0]), key=f"estat_{empresa}")
        notes = st.text_area("Notes de seguiment", value=anterior[1], key=f"notes_{empresa}")
        seguiment[empresa] = (estat, notes)
        st.caption("El seguiment dura la sessió. Exporta el CSV per conservar-lo.")
    taula["Estat comercial"] = taula.Empresa.map(lambda nom: seguiment.get(nom, (estats[0], ""))[0])
    taula["Notes"] = taula.Empresa.map(lambda nom: seguiment.get(nom, (estats[0], ""))[1])
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
