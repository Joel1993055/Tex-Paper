"""Actualitza la còpia local del Banc Mundial amb una escriptura atòmica."""
import csv
import gettext
import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen

BASE = "https://api.worldbank.org/v2"
INDICADOR = "LP.LPI.OVRL.XQ"
URL_PAISOS = f"{BASE}/country?format=json&per_page=400"
URL_LPI = f"{BASE}/country/all/indicator/{INDICADOR}?date=2022&format=json&per_page=400"
DESTI = Path(__file__).parent / "dades" / "logistica.csv"


def descarrega(url):
    with urlopen(url, timeout=30) as resposta:
        metadades, files = json.load(resposta)
    if metadades["pages"] != 1 or len(files) != metadades["total"]:
        raise ValueError("Resposta incompleta del Banc Mundial")
    return files


def actualitza(paisos, lpi, data):
    tradueix = gettext.translation("iso_3166-1", localedir="/usr/share/locale", languages=["ca"]).gettext
    cataleg = json.loads(Path("/usr/share/iso-codes/json/iso_3166-1.json").read_text())
    noms = {p["alpha_3"]: tradueix(p["name"]) for p in cataleg["3166-1"]}
    noms.update(XKX="Kosovo")
    zones = {
        "EAS": "Àsia i Pacífic", "SAS": "Àsia i Pacífic",
        "ECS": "Europa i Àsia central", "LCN": "Amèrica Llatina",
        "NAC": "Amèrica del Nord", "MEA": "Orient Mitjà i Àfrica",
        "SSF": "Orient Mitjà i Àfrica", "MNA": "Orient Mitjà i Àfrica",
    }
    valors = {r["countryiso3code"]: r["value"] for r in lpi if r["value"] is not None}
    if len(valors) < 100 or any(not 1 <= v <= 5 for v in valors.values()):
        raise ValueError("Cobertura o escala LPI inesperada")
    temporal = DESTI.with_suffix(".tmp")
    with temporal.open("w", newline="", encoding="utf-8") as fitxer:
        writer = csv.writer(fitxer)
        writer.writerow(["iso", "país", "zona", "LPI", "període", "consulta", "font"])
        for p in paisos:
            regió = p["region"]["id"]
            iso = p["id"]
            if regió != "NA":
                writer.writerow([iso, noms.get(iso, p["name"]),
                                 zones.get(regió, "Altres regions"),
                                 valors.get(iso), 2022, data, URL_LPI])
    temporal.replace(DESTI)


if __name__ == "__main__":
    actualitza(descarrega(URL_PAISOS), descarrega(URL_LPI), date.today().isoformat())
