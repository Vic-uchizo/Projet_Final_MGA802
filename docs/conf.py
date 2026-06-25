"""Configuration Sphinx pour la documentation du projet MGA802 (debris_orbites)."""

import os
import sys

# On ajoute la racine du projet au chemin pour qu'autodoc puisse importer
# le package debris_orbites (déjà installé en editable, mais on sécurise).
sys.path.insert(0, os.path.abspath(".."))

# -- Informations sur le projet ---------------------------------------------
project = "debris_orbites"
copyright = "2026, Équipe MGA802"
author = "Équipe MGA802"
release = "0.1.0"
language = "fr"

# -- Configuration générale -------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",      # génère la doc à partir des docstrings
    "sphinx.ext.napoleon",     # supporte les styles Google/NumPy en plus du reST
    "sphinx.ext.viewcode",     # ajoute des liens vers le code source
    "sphinx.ext.autosummary",  # tables de résumé automatiques
]

autosummary_generate = True
autodoc_member_order = "bysource"   # garde l'ordre du code source
autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options de sortie HTML -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
