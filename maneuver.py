import math
from sgp4.propagation import false

from orbit import charger_donnees_tle, detecter_collisions
from skyfield.api import load
from datetime import timedelta

# Gravitational constant
GM = 3.986004418e14

def InclinationChange(InclChange, VelAtOrbit):
    """
    Delta-V requis pour une combustion perpendiculaire (changement de plan pur).
    InclChangement en degrés, VelAtOrbit en m/s.
    """
    DelVplane = 2 * VelAtOrbit * math.sin(math.radians(InclChange) / 2)
    return DelVplane


def orbit_transfer(r1, r2, inclination_change=0.0):
    """
    Calcule un transfert de Hohmann entre deux orbites circulaires r1 (orbite actuelle)
    → r2 (nouvelle orbite), car il est efficace de modifier l'inclinaison
    (changement de plan) lors de la manœuvre d'apogée. Si nécessaire, ce changement d'inclinaison sera
    effectué. Renvoie un dictionnaire contenant les deux manœuvres,
    le delta-v total et la durée du transfert.
      Current actuelle ----> Orbit cible
      r1 (rayon)         r2 (rayon)
      v1 (vitesse)       v2 (vitesse)
    """

    v1 = math.sqrt(GM / r1)
    v2 = math.sqrt(GM / r2)

    # Demi-grand axe de l'ellipse de transfert
    a_t = (r1 + r2) / 2.0

    # Vitesse au périgée et à l'apogée de l'ellipse de transfert
    v_pg = math.sqrt(GM * (2 / r1 - 1 / a_t))
    v_ag = math.sqrt(GM * (2 / r2 - 1 / a_t))

    # Entrez l'ellipse de transfert au périgée
    dv1 = abs(v_pg - v1)

    # Sortir de l'ellipse de transfert à l'apogée, si spécifié,
    # effectuer un changement d'inclinaison
    if inclination_change != 0.0:
        dv2 = inclination_change(inclination_change,v_ag)
    else:
        dv2 = abs(v2 - v_ag)

    # Temps de transfert = la moitié de la période de l'ellipse
    transfer_time = math.pi * math.sqrt(a_t ** 3 / GM)

    return {
        'dv1_m_s': dv1,
        'dv2_m_s': dv2,
        'total_dv_m_s': dv1 + dv2,
        'transfer_time_s': transfer_time,
    }


def orbital_radius(satellite):

    rev_par_jour = satellite.model.no_kozai / (2* math.pi) * 1440
    rad_par_sec = (rev_par_jour * 2 * math.pi) / 86400
    demi_major_axis = (GM / rad_par_sec**2) ** (1/3)
    return demi_major_axis


def evasive_maneuver(satellite, df_collisions, altitude_evasion_km=10.0,
                     inclination_change=0.0, eleve_orbit=True):
    """
    Calcule la manœuvre d'évitement (delta-v + temps de transfert) nécessaire pour déplacer
    «satellite» de altitude_evasion_km, en se basant sur le DataFrame d'alerte produit
    par detecter_collisions().
    raise_orbit=True relève l'orbite, False l'abaisse.
    """
    if df_collisions.empty:
        print("Aucune collision prévue, maintien de l'orbite")
        return []

    r1 = orbital_radius(satellite)

    delta_r = altitude_evasion_km * 1000.0  # km -> m
    r2 = r1 + delta_r if eleve_orbit else r1 - delta_r

    transfer = orbit_transfer(r1, r2, inclination_change)

    manoeuvres = []
    for _, row in df_collisions.iterrows():
        manoeuvres.append({
            'Débris': row['Débris'],
            "Heure d'impact": row["Heure d'impact"],
            'Distance Min (km)': row['Distance Min (km)'],
            'r1 valeur en mètres': r1,
            'r2 valeur en mètres': r2,
            **transfer,
        })

    return manoeuvres


if __name__ == "__main__":
    ts = load.timescale()

    #----------------------------------------------------------------------------------
    # Étape 1 : Charger les TLE pour les satellites et les débris
    #----------------------------------------------------------------------------------
    satellites_starlink = charger_donnees_tle('donnees/starlink.txt')
    debris = charger_donnees_tle('donnees/cosmos-2251-debris.txt')

    #----------------------------------------------------------------------------------
    # Étape 2 : Définir la fenêtre temporelle à analyser
    #----------------------------------------------------------------------------------
    temps_debut = ts.now()
    temps_fin = ts.from_datetime(temps_debut.utc_datetime() + timedelta(hours=24*7))

    #----------------------------------------------------------------------------------
    # Étape 3 : Choisir UN satellite spécifique pour l'analyse de collision
    #----------------------------------------------------------------------------------
    satellite_cible = next(s for s in satellites_starlink if s.name == "STARLINK-5893")
    Collision = detecter_collisions(satellite_cible, debris, temps_debut, temps_fin, seuil_km=10.0)
    evasive = evasive_maneuver(satellite_cible, Collision, 5,0.0,false)

    print("Detected collision :",Collision)

    print("Evasive maneuver",evasive)
