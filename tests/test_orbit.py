"""
Tests unitaires du projet MGA802 (moteur orbital + manœuvre).

Méthode du cours : coder -> tester -> corriger.
Lancer :  pytest -v        (ou  python -m pytest -v  si pytest est introuvable)

Un bon test est court, clair, et centré sur UN seul comportement à vérifier.
"""

import math
from pathlib import Path

import pandas as pd

from debris_orbites import MoteurOrbital, Manoeuvre
from debris_orbites.donnees.telechargement import TelechargeurTLE

# Fichier TLE de débris présent dans le dépôt ; chemin indépendant du dossier courant.
RACINE = Path(__file__).resolve().parents[1]
FICHIER_DEBRIS = str(RACINE / "donnees_tle" / "cosmos-2251-debris.txt")
RAYON_TERRE_KM = 6371.0


def test_charger_tle_retourne_des_satellites():
    """Charger le fichier de débris doit renvoyer une liste non vide."""
    moteur = MoteurOrbital()
    debris = moteur.charger_tle(FICHIER_DEBRIS)
    assert len(debris) > 0


def test_charger_tle_fichier_absent_retourne_liste_vide():
    """Un fichier inexistant ne doit pas planter : on renvoie une liste vide."""
    moteur = MoteurOrbital()
    assert moteur.charger_tle("fichier_qui_nexiste_pas.txt") == []


def test_perigee_apogee_ordre_de_grandeur_leo():
    """En LEO, périgée <= apogée et tous deux ~6800-7200 km du CENTRE de la Terre."""
    moteur = MoteurOrbital()
    debris = moteur.charger_tle(FICHIER_DEBRIS)
    rp, ra = moteur.perigee_apogee(debris[0])
    assert rp <= ra
    assert RAYON_TERRE_KM < rp < 9000   # au-dessus de la surface, altitude LEO
    assert RAYON_TERRE_KM < ra < 9000


def test_positions_instantanees_colonnes_et_lignes():
    """positions_instantanees renvoie un DataFrame avec UNE ligne par satellite."""
    moteur = MoteurOrbital()
    debris = moteur.charger_tle(FICHIER_DEBRIS)[:5]
    df = moteur.positions_instantanees(debris, moteur.ts.now())
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Nom", "ID", "X", "Y", "Z"]
    assert len(df) == 5


def test_calculer_trajectoire_nombre_de_points():
    """La trajectoire contient exactement duree_minutes points (colonnes X, Y, Z)."""
    moteur = MoteurOrbital()
    debris = moteur.charger_tle(FICHIER_DEBRIS)
    df = moteur.calculer_trajectoire(debris[0], debris[0].epoch, duree_minutes=10)
    assert list(df.columns) == ["X", "Y", "Z"]
    assert len(df) == 10


def test_hohmann_delta_v_coherent():
    """Transfert de Hohmann : delta-v positifs et total = somme des deux poussées."""
    m = Manoeuvre("TEST", pd.DataFrame())     # df_collision non utilisé par orbit_transfer
    transfert = m.orbit_transfer(7.0e6, 7.1e6)  # rayons en mètres
    dv1 = transfert["Poussee d évitemment (m/s)"]
    dv2 = transfert["Pousse de re-circularisation (m/s)"]
    total = transfert["total delta de vitesse (m/s)"]
    assert dv1 > 0 and dv2 > 0
    assert math.isclose(total, dv1 + dv2)
    assert transfert["Temps de transfert (s)"] > 0


def test_telechargeur_chemin_fichier():
    """chemin_fichier construit bien <dossier>/<groupe>.txt (sans accès réseau)."""
    t = TelechargeurTLE(dossier="/tmp/data")
    assert t.chemin_fichier("starlink").endswith("starlink.txt")
