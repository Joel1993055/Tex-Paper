"""Llegeix les instal·lacions tèxtils de la compilació WWF / Open Supply Hub."""
import pandas as pd

FONT = "https://zenodo.org/records/7804659"
CSV = f"{FONT}/files/assets_cleaned.csv?download=1"
SECTOR = "Textiles, Apparel & Luxury Good Production"


def carrega_registre(origen=CSV):
    camps = ["id_original", "site_name", "industry", "country", "adm1", "duplicated"]
    dades = pd.read_csv(origen, usecols=camps, dtype=str)
    dades = dades[dades.industry.eq(SECTOR) & dades["duplicated"].eq("no")].copy()
    dades = dades.dropna(subset=["id_original", "site_name", "country"])
    dades = dades.drop_duplicates("id_original")
    if len(dades) < 10_000:
        raise ValueError("El registre descarregat és incomplet.")
    dades["Font"] = "https://opensupplyhub.org/facilities/" + dades.id_original
    return dades.rename(columns={
        "site_name": "Instal·lació", "country": "País (registre)", "adm1": "Regió",
        "id_original": "Identificador",
    })[["Instal·lació", "País (registre)", "Regió", "Identificador", "Font"]].fillna("")
