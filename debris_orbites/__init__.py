"""
Package ``debris_orbites`` — Projet final MGA802.

Visualisation 3D et détection de collisions entre satellites et débris en
orbite basse (LEO).

Ce package regroupe la logique métier du projet :

- :mod:`debris_orbites.orbit` — moteur de calculs orbitaux
  (:class:`~debris_orbites.orbit.MoteurOrbital`) : chargement des TLE, positions,
  trajectoires et détection de collisions.
- :mod:`debris_orbites.maneuver` — calcul des manœuvres d'évitement
  (:class:`~debris_orbites.maneuver.Manoeuvre`).
- :mod:`debris_orbites.donnees` — téléchargement des données brutes (CelesTrak).

Les classes principales sont ré-exportées ici pour un accès direct ::

    from debris_orbites import MoteurOrbital, Manoeuvre
"""

from .orbit import MoteurOrbital
from .maneuver import Manoeuvre

__version__ = "0.1.0"

__all__ = ["MoteurOrbital", "Manoeuvre"]
