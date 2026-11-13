# Texpaper · Intel·ligència de mercats

Aplicació en català per investigar l’expansió internacional de Texpaper Service, S.L. Inclou un mapa mundial, fitxes de mercat, prospectes amb fonts, comparació i simulació de marge.

## Arrencada

Amb Python 3.11 o superior:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Obre l’adreça que indica Streamlit. El selector sota el mapa permet triar qualsevol economia del filtre. La simulació utilitza hipòtesis introduïdes durant la sessió.

## Lliurables

- [Informe executiu](docs/informe.md)
- [Pla d’acció de 90 dies](docs/pla_90_dies.md)
- [Base de prospectes](dades/prospectes.csv)
- [Presentació per a direcció](docs/texpaper_direccio.pptx)

## Actualització

La còpia local del LPI funciona sense consultar l’API a cada visita. El fitxer inclou l’URL, el període i la data de consulta. Per actualitzar-lo, executa `python actualitza_dades.py` en un entorn Linux amb les dades del paquet `iso-codes` i accés a l’API del Banc Mundial. Si falla la validació, es conserva el CSV anterior. El LPI 2023 s’identifica com a 2022 a l’API.

Les fonts dels prospectes es recullen a cada fila. Una absència a la base significa que encara no hi ha evidència pública recopilada. La presència comercial actual requereix informació interna.
