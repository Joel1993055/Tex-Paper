from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from model import simula

DADES = Path(__file__).parent / "dades"
VERIFICAT = "Procés verificat"
st.set_page_config(page_title="Texpaper | Expansió internacional", layout="wide")
st.title("Texpaper · Expansió internacional")
st.caption("Exploració de mercats i validació comercial per a papers tècnics")


@st.cache_data
def carrega():
    països = pd.read_csv(DADES / "logistica.csv").set_index("iso")
    mercats = pd.read_csv(DADES / "mercats.csv").set_index("iso")
    països = països.join(mercats.drop(columns="font"))
    països["Evidència comercial"] = països["historial"].map(
        {"Sí": "Enviaments històrics documentats"}
    ).fillna("Presència pendent de confirmar")
    return països, pd.read_csv(DADES / "prospectes.csv").fillna(""), mercats


paisos, prospectes, mercats = carrega()
with st.sidebar:
    st.header("Filtres")
    zona = st.selectbox("Zona", ["Tot el món", *sorted(paisos.zona.unique())])
    estrategia = st.selectbox("Via comercial", [
        "Totes", "Mercats amb enviaments històrics", "Venda directa", "Canal o fabricant d’equips"
    ])
    categoria = st.selectbox("Paper", ["Tots", *sorted(prospectes.categoria.unique())])
    capa = st.radio("Capa del mapa", ["Evidència comercial", "Logística"])
    with st.expander("Prioritats de revisió"):
        pes_log = st.slider("Logística", 0, 100, 50)
        pes_proc = st.slider("Procés identificat", 0, 100, 50)

vista = paisos.copy()
p = prospectes.copy()
if categoria != "Tots":
    p = p[p.categoria.eq(categoria)]
if estrategia == "Venda directa":
    p = p[p.estat.eq(VERIFICAT)]
    vista = vista[vista.index.isin(p.iso)]
elif estrategia == "Canal o fabricant d’equips":
    p = p[p.estat.eq("Canal potencial") | p.empresa.eq("Margot")]
    vista = vista[vista.index.isin(p.iso)]
elif estrategia == "Mercats amb enviaments històrics":
    vista = vista[vista.historial.eq("Sí")]
if zona != "Tot el món":
    vista = vista[vista.zona.eq(zona)]
p = p[p.iso.isin(vista.index)]
comptes = p[p.estat.eq(VERIFICAT)].groupby("iso").size()
vista["Processos documentats"] = comptes.reindex(vista.index).astype("Int64")
vista["Senyal"] = "Evidència comercial insuficient"
vista.loc[vista.historial.eq("Sí"), "Senyal"] = "Enviaments històrics"
vista.loc[vista["Processos documentats"].notna(), "Senyal"] = "Procés documentat"
vista.loc[vista.historial.eq("Sí") & vista["Processos documentats"].notna(), "Senyal"] = "Procés i historial"

mapa, perfil, clients, cas, fonts = st.tabs(
    ["Mapa mundial", "Fitxa de mercat", "Prospectes", "Comparació i simulació", "Fonts i metodologia"]
)
with mapa:
    for columna, (etiqueta, valor) in zip(st.columns(4), [
        ("Economies al filtre", len(vista)),
        ("Amb indicador logístic", vista.LPI.count()),
        ("Prospectes amb procés documentat", comptes.sum()),
        ("Amb historial d’enviaments", vista.historial.eq("Sí").sum()),
    ]):
        columna.metric(etiqueta, valor)
    if vista.empty:
        st.info("Cap economia coincideix amb aquests filtres.")
    else:
        dades_mapa = vista.reset_index()
        opcions = dict(locations="iso", hover_name="país", projection="natural earth",
                       hover_data={"iso": False, "LPI": True, "Senyal": True})
        if capa == "Logística":
            fig = px.choropleth(dades_mapa, color="LPI", range_color=(1, 5),
                                color_continuous_scale="Teal", **opcions)
        else:
            fig = px.choropleth(dades_mapa, color="Senyal", color_discrete_map={
                "Evidència comercial insuficient": "#dbe5ed", "Enviaments històrics": "#517da4",
                "Procés documentat": "#20a393", "Procés i historial": "#075d60"
            }, **opcions)
        fig.update_geos(showframe=False, showcountries=True, showcoastlines=True,
                        landcolor="#edf2f6", bgcolor="rgba(0,0,0,0)")
        fig.update_layout(height=530, margin=dict(l=0, r=0, t=0, b=0), dragmode="pan",
                          legend_title_text="Evidència pública")
        seleccio = st.plotly_chart(fig, key="mapa_" + capa, on_select="rerun",
                                   selection_mode="points", config={"scrollZoom": True})
        punts = seleccio.selection.points
        codis = vista.sort_values("país").index.tolist()
        desti = punts[-1].get("location") if punts else None
        anterior = st.session_state.get("punt_anterior")
        if desti != anterior and desti in codis:
            st.session_state["mercat"] = desti
        st.session_state["punt_anterior"] = desti
        if st.session_state.get("mercat") not in codis:
            st.session_state["mercat"] = "PRT" if "PRT" in codis else codis[0]
        iso = st.selectbox("Mercat seleccionat", codis, format_func=vista.país.get, key="mercat")
        st.subheader("Ordre de revisió dels mercats amb prospectes")
        revisio = vista.dropna(subset=["Processos documentats", "LPI"]).copy()
        if pes_log + pes_proc and not revisio.empty:
            log = (revisio.LPI - 1) * 25
            procés = 100 * revisio["Processos documentats"] / revisio["Processos documentats"].max()
            revisio["Índex de revisió"] = (log * pes_log + procés * pes_proc) / (pes_log + pes_proc)
            revisio["Posició només logística"] = log.rank(method="min", ascending=False).astype(int)
            revisio["Posició només prospectes"] = procés.rank(method="min", ascending=False).astype(int)
            st.dataframe(revisio.sort_values("Índex de revisió", ascending=False)[[
                "país", "LPI", "Processos documentats", "Índex de revisió",
                "Posició només logística", "Posició només prospectes"
            ]].round(1), hide_index=True)
        st.caption("L’ordre orienta la recerca. La cobertura de prospectes varia segons el país. L’atractiu comercial global continua pendent de validació.")

if not vista.empty:
    fila = vista.loc[iso]
    with perfil:
        st.header(fila.país)
        st.write(fila["Evidència comercial"])
        st.metric("Logística · LPI 2023 (1–5)", f"{fila.LPI:.1f}" if pd.notna(fila.LPI) else "Sense dada")
        st.subheader(fila.acció if pd.notna(fila.acció) else "Evidència insuficient")
        st.write(fila.justificació if pd.notna(fila.justificació) else "Cal documentar processos compatibles i validar el canal comercial.")
        if iso in mercats.index and pd.notna(mercats.at[iso, "font"]):
            st.link_button("Consultar l’evidència", mercats.at[iso, "font"])
        st.write("Ubicacions documentades", ", ".join(sorted(set(p.loc[p.iso.eq(iso), "ciutat"]) - {""})) or "Pendents")
        st.write("Per cotitzar cal confirmar la referència, l’origen, el codi duaner, el lloc d’entrega, la mida de comanda i la moneda.")
        st.link_button("Consultar Access2Markets", "https://trade.ec.europa.eu/access-to-markets/ca/home")
    with clients:
        només = st.toggle("Només el mercat seleccionat", value=True)
        filtrats = p[p.iso.eq(iso)] if només else p
        taula = filtrats.assign(país=filtrats.iso.map(paisos.país)).drop(columns="iso")
        st.dataframe(taula, hide_index=True, column_config={"font": st.column_config.LinkColumn("Font")})
        st.download_button("Descarrega el CSV", taula.to_csv(index=False).encode("utf-8-sig"),
                           "prospectes_texpaper.csv", "text/csv")
    with cas:
        tria = st.multiselect("Mercats per comparar", codis, default=[iso],
                              max_selections=4, format_func=vista.país.get, key=f"compara_{iso}")
        if tria:
            comparacio = vista.loc[tria, ["país", "LPI", "Processos documentats", "Evidència comercial", "acció"]]
            st.dataframe(comparacio, hide_index=True)
            st.plotly_chart(px.bar(comparacio.dropna(subset=["LPI"]), x="país", y="LPI",
                                   range_y=[0, 5], labels={"país": "Mercat", "LPI": "Índex logístic"}))
        st.subheader(f"Simulació comercial · {fila.país}")
        st.caption("Introdueix les hipòtesis anuals. Els valors són propis de cada mercat i escenari.")
        escenari = st.radio("Escenari", ["Conservador", "Base", "Optimista"], horizontal=True)
        clau = f"{iso}_{escenari}"
        camps = [
            ("Compradors accessibles", None), ("Conversió (%)", 100.0),
            ("Comandes anuals per client", None), ("Preu net per comanda (€)", None),
            ("Cost variable entregat per comanda (€)", None), ("Cost de captació per client (€)", None),
            ("Cost fix anual incremental (€)", None), ("Inversió inicial (€)", None),
        ]
        valors = [
            columna.number_input(nom, min_value=0.0, max_value=màxim, value=None, key=f"{clau}_{i}")
            for i, ((nom, màxim), columna) in enumerate(zip(camps, st.columns(4) * 2))
        ]
        if all(v is not None for v in valors):
            resultat = simula(*valors)
            st.table(pd.DataFrame([
                (k, f"{v:,.2f}" if v is not None else "Sense llindar amb aquestes hipòtesis")
                for k, v in resultat.items()
            ], columns=["Resultat calculat", "Valor"]))
        st.caption("Inclou transport, aranzels, descomptes i comissions on correspongui. Exclou impostos sobre beneficis, finançament i circulant. Recuperació simple al ritme operatiu del primer any.")

with fonts:
    st.markdown("""
**Empresa i productes.** [Història oficial](https://www.texpaper.es/nosotros/) ·
[Protecció de calandra](https://www.texpaper.es/productos/proteccion-calandra/) ·
[Protecció de planxa](https://www.texpaper.es/productos/proteccion-plancha/).

**Logística.** [Banc Mundial, LPI](https://data.worldbank.org/indicator/LP.LPI.OVRL.XQ).
Enquesta de 2022 publicada com a edició 2023, escala 1–5, llicència CC BY 4.0.
L’índex resumeix percepcions sobre la logística del país. Les cotitzacions per ruta s’han de recollir per separat.

**Historial.** [Panjiva](https://panjiva.com/Texpaper-Service-S-L/41432153) i
[registre colombià publicat per Veritrade](https://www.veritradecorp.com/es/colombia/importaciones-y-exportaciones-tiimpal-sas/nit-901647812).
Cobertura parcial i període complet sense verificar. L’activitat actual requereix confirmació al CRM.

**Competència i canal.** [Texo Trade Services](https://www.texo-trade.com/en_US/) comercialitza
paper de protecció i transferència. [ATS Service](https://www.ats360.co/en) ofereix equips i consumibles.

**Metodologia.** Índex de revisió = mitjana ponderada de `25 × (LPI − 1)` i
`100 × prospectes documentats / màxim del filtre`. Les posicions extremes mostren la sensibilitat als pesos.
El recompte mesura la cobertura de la recerca. La demanda efectiva, el risc, la intensitat competitiva
i la rendibilitat comparable queden pendents de dades. Consulta documental dels prospectes i enviaments el 13/11/2026.
""")
    st.caption(f"Còpia de l’API del Banc Mundial consultada el {paisos.consulta.iloc[0]}.")
