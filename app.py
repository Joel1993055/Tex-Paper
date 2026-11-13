from pathlib import Path

import pandas as pd
import streamlit as st

DADES = Path(__file__).parent / "dades"

st.set_page_config(page_title="Texpaper · Compradors potencials", layout="wide")
st.title("Compradors potencials de Texpaper")

països = pd.read_csv(DADES / "logistica.csv").set_index("iso")["país"]
empreses = pd.read_csv(DADES / "prospectes.csv").fillna("")
empreses = empreses[empreses.estat.ne("Canal potencial")].copy()
empreses["País"] = empreses.iso.map(països)
empreses["Validació"] = empreses.estat.replace({"Procés verificat": "Procés documentat"})

controls = st.columns(2)
país = controls[0].selectbox("País", ["Tot el món", *sorted(països.unique())])
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
