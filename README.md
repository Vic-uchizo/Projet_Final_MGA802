# Projet_Final_MGA802 — Débris & satellites en orbite (LEO)

Visualisation 3D et **détection de collisions** entre une constellation de
satellites (**Starlink**) et un nuage de **débris** (**Cosmos 2251**) en orbite
terrestre basse. Interface **Streamlit + matplotlib 3D**, propagation orbitale
via **skyfield/SGP4**.

## Structure du projet

```
Projet_Final_MGA802/
├── main.py                  # point d'entrée : menu (télécharger / lancer l'interface)
├── data_visu_streamlit.py   # interface 3D (Streamlit)
├── debris_orbites/          # LE PACKAGE installable (logique métier)
│   ├── orbit.py             #   moteur de calculs orbitaux (MoteurOrbital)
│   ├── maneuver.py          #   manœuvres d'évitement (Manoeuvre)
│   └── donnees/             #   téléchargement des TLE (CelesTrak)
├── donnees_tle/             # données TLE (.txt) — re-téléchargées automatiquement
├── docs/                    # documentation Sphinx
└── pyproject.toml           # packaging
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate   # (ou .venv\Scripts\activate sous Windows)
pip install -e .                                    # installe le package et ses dépendances
```

## Lancement

```bash
python main.py
#   option 1 : télécharger les données depuis CelesTrak (une seule fois)
#   option 2 : lancer l'interface 3D interactive (Streamlit)
```

On peut aussi lancer directement l'interface :

```bash
streamlit run data_visu_streamlit.py
```

## Documentation (Sphinx)

```bash
pip install -e ".[docs]"          # installe Sphinx
cd docs && make html              # génère docs/_build/html/index.html
```

## Utilisation du package en Python

```python
from debris_orbites import MoteurOrbital

moteur = MoteurOrbital()
satellites = moteur.charger_tle("donnees_tle/starlink.txt")
positions = moteur.positions_instantanees(satellites, moteur.ts.now())
```
