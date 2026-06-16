import numpy as np
import pandas as pd
from skyfield.api import EarthSatellite, load

# Initialisation de Skyfield
ts = load.timescale()


def parse_tle_file_robust(filepath):
    """Filtre d'abord toutes les lignes vides pour recoller les blocs TLE

    qui ont été éclatés par des sauts de ligne.
    """
    satellites = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="cp1252") as f:
            raw_lines = f.readlines()

    # --- LE NETTOYAGE CRUCIAL ---
    # On ne garde QUE les lignes qui contiennent du texte après avoir enlevé les espaces
    cleaned_lines = [line.strip() for line in raw_lines if line.strip()]

    # Maintenant que le fichier est "recollé", on avance de 3 en 3 de manière propre
    i = 0
    while i < len(cleaned_lines):
        # On s'assure qu'on a bien un bloc complet de 3 lignes valides
        if (
            i + 2 < len(cleaned_lines)
            and cleaned_lines[i + 1].startswith("1")
            and cleaned_lines[i + 2].startswith("2")
        ):
            satellites.append(
                {
                    "name": cleaned_lines[i],
                    "tle_line1": cleaned_lines[i + 1],
                    "tle_line2": cleaned_lines[i + 2],
                }
            )
            i += 3  # On saute au satellite suivant
        else:
            # Si jamais une ligne parasite s'est glissée, on avance de 1 pour ne pas bloquer
            i += 1

    print(f"--- PARSING REUSSI ---")
    print(f"Satellites correctement extraits : {len(satellites)}")
    return satellites


def get_satellite_dataframe(filepath, target_time=None):
    """Calcule les positions (x, y, z) en kilomètres par rapport au centre de la Terre."""
    if target_time is None:
        target_time = ts.now()

    tle_data = parse_tle_file_robust(filepath)
    results = []

    for sat_data in tle_data:
        try:
            satellite = EarthSatellite(
                sat_data["tle_line1"], sat_data["tle_line2"], sat_data["name"]
            )
            geocentric = satellite.at(target_time)
            x_km, y_km, z_km = geocentric.position.km

            results.append(
                {
                    "Satellite": sat_data["name"],
                    "x (km)": x_km,
                    "y (km)": y_km,
                    "z (km)": z_km,
                }
            )
        except Exception as e:
            # Sécurité si un TLE précis est corrompu dans la masse
            print(f"Erreur de calcul avec {sat_data['name']}: {e}")

    return pd.DataFrame(results)


def get_satellite_position(df, satellite_name):
    """Méthode de récupération rapide et flexible par nom (sensible au numéro)."""
    if df.empty:
        print("⚠️ Le DataFrame est vide.")
        return None

    match = df[df["Satellite"].str.contains(satellite_name, case=False, na=False)]

    if match.empty:
        print(f"⚠️ Le satellite '{satellite_name}' n'a pas été trouvé.")
        return None

    row = match.iloc[0]
    x, y, z = row["x (km)"], row["y (km)"], row["z (km)"]
    distance = np.sqrt(x**2 + y**2 + z**2)

    print(f"DONNÉES DE TRAJECTOIRE : {row['Satellite']}")
    print("")
    print(f"Coordonnées X : {x:.4f} km")
    print(f"Coordonnées Y : {y:.4f} km")
    print(f"Coordonnées Z : {z:.4f} km")
    print(f"Distance au centre de la Terre : {distance:.2f} km")
    return np.array([[x, y, z]])



# ==========================================
# EXÉCUTION
# ==========================================
if __name__ == "__main__":
    print("Analyse et nettoyage du fichier géant...")
    df_sat = get_satellite_dataframe("donnees/starlink.txt")

    if not df_sat.empty:
        print(f"DataFrame créé avec succès ({len(df_sat)} lignes).")

        # Lancement de la recherche (on cherche ton satellite 37096)
        pos = get_satellite_position(df_sat, "37096")

        if pos:
            print("\n--- POSITION DU SATELLITE TROUVÉE ---")
            print(f"Nom : {pos['name']}")
            print(f"X : {pos['x']:.2f} km")
            print(f"Y : {pos['y']:.2f} km")
            print(f"Z : {pos['z']:.2f} km")
            print(f"Distance centre Terre : {pos['distance_centre_terre_km']:.2f} km")
    else:
        print("\n❌ Échec critique : le DataFrame est resté vide.")