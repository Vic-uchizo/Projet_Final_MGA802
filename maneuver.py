import math
from orbit import charger_donnees_tle, detecter_collisions
from skyfield.api import load
import datetime

# Gravitational constant
GM = 3.986004418e14

def InclinationChange(InclChange, VelAtOrbit):
    """
    Delta-V required for a pure plane-change burn (perpendicular burn).
    InclChange in degrees, VelAtOrbit in m/s.
    """
    DelVplane = 2 * VelAtOrbit * math.sin(math.radians(InclChange) / 2)
    return DelVplane


def orbit_transfer(r1, r2, inclination_change=0.0):
    """
    Computes a Hohmann transfer between two circular orbits r1 (current orbit)
     -> r2 (new orbit), as it is efficient to change the inclination
     (plane change) at apogee burn, if needed this inclination change will be
     performed. Returns a dict with both burns,
      the total delta-v, and the transfer time.
      Current Orbit ----> Target Orbit
      r1 (radius)         r2 (radius)
      v1 (velocity)       v2 (velocity)
    """
    v1 = math.sqrt(GM / r1)

    v2 = math.sqrt(GM / r2)

    # Semi-major axis of the transfer ellipse
    a_t = (r1 + r2) / 2.0

    # Velocity at perigee and apogee of the transfer ellipse
    v_pg = math.sqrt(GM * (2 / r1 - 1 / a_t))
    v_ag = math.sqrt(GM * (2 / r2 - 1 / a_t))

    # Enter transfer ellipse at perigee
    dv1 = abs(v_pg - v1)

    # Exit transfer ellipse at apogee
    if inclination_change != 0.0:
        dv2 = inclination_change(inclination_change,v_ag)
    else:
        dv2 = abs(v2 - v_ag)

    # Transfer time = half the period of the ellipse
    transfer_time = math.pi * math.sqrt(a_t ** 3 / GM)

    return {
        'dv1_m_s': dv1,
        'dv2_m_s': dv2,
        'total_dv_m_s': dv1 + dv2,
        'transfer_time_s': transfer_time,
    }


def orbital_radius(satellite):

    rev_per_day = satellite.model.no_kozai / (2* math.pi) * 1440
    rad_per_sec = (rev_per_day * 2 * math.pi) / 86400
    semi_major_axis = (GM / rad_per_sec**2) ** (1/3)
    return semi_major_axis


def evasive_maneuver(satellite, df_collisions, altitude_evasion_km=10.0,
                     inclination_change=0.0, raise_orbit=True):
    """
    Computes the avoidance maneuver (delta-v + transfer time) needed to move
    'satellite' by altitude_evasion_km, based on the alert DataFrame produced
    by detecter_collisions().

    raise_orbit=True raises the orbit, False lowers it.
    """
    if df_collisions.empty:
        print("No collisions predicted, maintain orbit")
        return []

    r1 = orbital_radius(satellite)
    delta_r = altitude_evasion_km * 1000.0  # km -> m
    r2 = r1 + delta_r if raise_orbit else r1 - delta_r

    transfer = orbit_transfer(r1, r2, inclination_change)

    manoeuvres = []
    for _, row in df_collisions.iterrows():
        manoeuvres.append({
            'Débris': row['Débris'],
            "Heure d'impact": row["Heure d'impact"],
            'Distance Min (km)': row['Distance Min (km)'],
            'r1_m': r1,
            'r2_m': r2,
            **transfer,
        })

    return manoeuvres


if __name__ == "__main__":


    # Imports the loading and detection functions from collision_detection.py

    ts = load.timescale()

    # Load your TLEs (target and debris can come from the same file or not)
    satellites = charger_donnees_tle('donnees/cosmos-2251-debris.txt')

    # Pick the target and the list of debris to monitor
    satellite_cible = satellites[0]
    debris = satellites[1:]

    # Monitoring window: now -> +24h
    t_debut = ts.now()
    t_fin = ts.from_datetime(t_debut.utc_datetime() + datetime.timedelta(hours=24))

    print(f"Recherche de collisions pour {satellite_cible.name}...")
    df_collisions = detecter_collisions(satellite_cible, debris, t_debut, t_fin, seuil_km=5.0)

    if df_collisions.empty:
        print("No collision detected in the next 24 hours")
    else:
        print(f"{len(df_collisions)} Alerts detected in the next 24 hours :")
        print(df_collisions)

        plan = evasive_maneuver(satellite_cible, df_collisions, altitude_evasion_km=10.0)

        print("\nEvasive Maneuver :")
        for m in plan:
            heure = m["Heure d'impact"]
            print(
                f"  vs {m['Débris']} @ {heure} "
                f"(distance min {m['Distance Min (km)']} km) -> "
                f"DeltaV total = {m['total_dv_m_s']:.2f} m/s, "
                f"temps de transfert = {m['transfer_time_s'] / 60:.1f} min"
            )
