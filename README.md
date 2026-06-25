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
├── presentation/            # support de présentation (deck Streamlit + export PDF)
├── requirements.txt         # dépendances figées
└── pyproject.toml           # packaging
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate   # (ou .venv\Scripts\activate sous Windows)
pip install -e .                                    # installe le package et ses dépendances
```

**Dépendances principales** (installées automatiquement, versions figées dans
`requirements.txt`) : `numpy`, `pandas`, `matplotlib`, `requests`, `skyfield`,
`streamlit`. Pour reproduire l'environnement exact : `pip install -r requirements.txt`.

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

## Tests

```bash
pip install -e ".[test]"   # installe pytest
pytest -v                   # lance les tests unitaires (ou : python -m pytest -v)
```

Les tests (`tests/test_orbit.py`) vérifient le chargement des TLE, les ordres de
grandeur orbitaux (périgée/apogée en LEO), les trajectoires et la cohérence du
transfert de Hohmann.

## Utilisation du package en Python

```python
from debris_orbites import MoteurOrbital

moteur = MoteurOrbital()
satellites = moteur.charger_tle("donnees_tle/starlink.txt")
positions = moteur.positions_instantanees(satellites, moteur.ts.now())
```

## Références & sources

### Données
- **CelesTrak** — catalogues TLE publics (satellites & débris), MAJ quotidienne :
  <https://celestrak.org/NORAD/elements/>
  - Constellation **Starlink** : `GROUP=starlink`
  - Débris **Cosmos 2251** (collision Iridium 33 / Cosmos 2251, 2009) : `GROUP=cosmos-2251-debris`
- Format **TLE** (Two-Line Element) — description : <https://en.wikipedia.org/wiki/Two-line_element_set>

### Bibliothèques & modèles
- **Skyfield** — propagation orbitale haute précision : <https://rhodesmill.org/skyfield/>
- **SGP4** — modèle standard de propagation des TLE (Vallado et al., *Revisiting Spacetrack Report #3*, AIAA 2006) : <https://pypi.org/project/sgp4/>
- **Streamlit** (interface web) : <https://streamlit.io/> · **Matplotlib** (3D `mplot3d`) : <https://matplotlib.org/>

### Méthodes
- **Transfert de Hohmann** — manœuvre d'évitement à deux impulsions (équation *vis-viva*) :
  <https://en.wikipedia.org/wiki/Hohmann_transfer_orbit>
- **TCA / conjunction screening** — recherche de l'instant de plus proche approche
  (résolution semi-analytique par Newton-Raphson sur Δr·Δv = 0), cf. `debris_orbites/orbit.py`.
