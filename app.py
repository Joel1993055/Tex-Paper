from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DADES = Path(__file__).parent / "dades"

st.set_page_config(page_title="Texpaper · Compradors potencials", layout="wide")
st.title("Compradors potencials de Texpaper")

catàleg = pd.read_csv(DADES / "logistica.csv").set_index("iso")
països = catàleg["país"].to_dict()
països.setdefault("TWN", "Taiwan")
empreses = pd.read_csv(DADES / "prospectes.csv").fillna("")
empreses = empreses[empreses.estat.ne("Canal potencial") & ~empreses.iso.isin(["AUS", "NZL", "ZAF"])].copy()
zones = {
    "Europa": ["ESP", "PRT", "FRA", "DEU", "NLD", "CZE", "POL", "ITA", "GBR"],
    "Àsia": ["TUR", "ARE", "IND", "BGD", "VNM", "THA", "TWN"],
    "Amèrica": ["USA", "CAN", "MEX", "COL", "BRA", "CHL", "ARG", "PER"],
}
regions = {iso: regió for regió, codis in zones.items() for iso in codis}
empreses["País"] = empreses.iso.map(països)
empreses["Regió"] = empreses.iso.map(regions)
regió = st.radio("Regió", ["Totes", *zones], horizontal=True)
if regió != "Totes":
    empreses = empreses[empreses["Regió"].eq(regió)]
països = empreses.drop_duplicates("iso").set_index("iso")["País"]

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
    st.session_state[f"país_{regió}"] = països[codi]
st.session_state["últim_clic"] = codi
st.caption("El color indica quantes empreses hem documentat al directori per país.")

controls = st.columns(2)
país = controls[0].selectbox("País", ["Tots els països", *sorted(països.unique())], key=f"país_{regió}")
cerca = controls[1].text_input("Cerca una empresa")
if país != "Tots els països":
    empreses = empreses[empreses["País"].eq(país)]
if cerca.strip():
    empreses = empreses[empreses.empresa.str.contains(cerca.strip(), case=False, regex=False)]

st.subheader("Empreses")
st.caption(f"{len(empreses)} empreses · {empreses['País'].nunique()} països")
if empreses.empty:
    st.info("Cap empresa coincideix amb aquests filtres.")
for fila in empreses.sort_values(["País", "empresa"]).itertuples(index=False):
    with st.expander(f"{fila.empresa} · {fila.País}"):
        if fila.ciutat:
            st.caption(fila.ciutat)
        st.write(fila.evidencia)
        st.markdown(f"**Què podem oferir** · {fila.categoria}")
        st.link_button("Font de l’activitat", fila.font)
