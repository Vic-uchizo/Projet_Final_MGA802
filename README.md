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

La doc HTML est générée à partir des docstrings du code. Elle n'est **pas**
versionnée (le dossier `docs/_build/` est ignoré par Git) : il faut la
(re)générer en local.

**1. Installer Sphinx + le thème** (l'option `[docs]` est indispensable, sinon
erreur « no theme named 'sphinx_rtd_theme' ») :

```bash
pip install -e ".[docs]"
```

**2. Générer la doc :**

```bash
# macOS / Linux
cd docs && make html

# Windows (invite de commandes ou PowerShell)
cd docs
make html
```

**3. Ouvrir** le fichier `docs/_build/html/index.html` dans un navigateur.

> Si `make` est introuvable, la commande directe marche sur tous les systèmes :
> ```bash
> python -m sphinx -b html docs docs/_build/html
> ```

## Utilisation du package en Python

```python
from debris_orbites import MoteurOrbital

moteur = MoteurOrbital()
satellites = moteur.charger_tle("donnees_tle/starlink.txt")
positions = moteur.positions_instantanees(satellites, moteur.ts.now())
```
