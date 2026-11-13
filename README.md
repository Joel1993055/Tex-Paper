# Texpaper · Intel·ligència de mercats

Directori en català de compradors potencials. Tria un país, consulta el procés públic de cada empresa i exporta les files seleccionades.

## Arrencada

Amb Python 3.11 o superior:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Obre l’adreça que indica Streamlit.

## Lliurables

- [Informe executiu](docs/informe.md)
- [Pla d’acció de 90 dies](docs/pla_90_dies.md)
- [Base de prospectes](dades/prospectes.csv)
- [Presentació per a direcció](docs/texpaper_direccio.pptx)

## Actualització

La còpia local del LPI funciona sense consultar l’API a cada visita. El fitxer inclou l’URL, el període i la data de consulta. Per actualitzar-lo, executa `python actualitza_dades.py` en un entorn Linux amb les dades del paquet `iso-codes` i accés a l’API del Banc Mundial. Si falla la validació, es conserva el CSV anterior. El LPI 2023 s’identifica com a 2022 a l’API.

Les fonts dels prospectes es recullen a cada fila. Una absència a la base significa que encara no hi ha evidència pública recopilada. La presència comercial actual requereix informació interna.
