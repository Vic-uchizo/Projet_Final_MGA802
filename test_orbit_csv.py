"""
Script pour récupérer les TLEs et générer des trajectoires synchronisées en CSV.
Nécessite l'installation de skyfield : pip install skyfield numpy pandas
"""

import csv
import numpy as np
from skyfield.api import load

def generer_csv_trajectoire():
    print("1. Chargement de l'échelle de temps...")
    ts = load.timescale()
    
    # --- CRÉATION DE L'HORLOGE SYNCHRONISÉE ---
    # On crée une simulation qui commence le 10 juin 2026 à 12h00 UTC
    # On simule 120 minutes (2 heures) avec 1 calcul par minute.
    minutes_simul = np.arange(0, 120, 1) 
    temps_synchro = ts.utc(2026, 6, 10, 12, minutes_simul)

    print("2. Téléchargement des vraies données TLE depuis CelesTrak...")
    url_stations = 'https://celestrak.org/NORAD/elements/stations.txt'
    satellites = load.tle_file(url_stations)
    
    # --- CORRECTION ICI : Recherche par mot-clé (plus robuste) ---
    iss = None
    tianhe = None
    
    for sat in satellites:
        # On met le nom en majuscules pour éviter les soucis de casse
        nom_propre = sat.name.upper()
        if 'ISS' in nom_propre and iss is None:
            iss = sat
        elif 'TIANHE' in nom_propre and tianhe is None:
            tianhe = sat
            
    # Vérification
    if not iss or not tianhe:
        print("Erreur : Impossible de trouver les satellites.")
        print("Voici un aperçu des noms disponibles dans le fichier :")
        # Affiche les 10 premiers noms pour vous aider à déboguer au cas où
        for s in satellites[:10]:
            print(f"- '{s.name}'")
        return

    print(f" -> Trouvé : {iss.name}")
    print(f" -> Trouvé : {tianhe.name}")

    print("3. Calcul géométrique et extraction des données...")
    geocentrique_iss = iss.at(temps_synchro)
    geocentrique_tianhe = tianhe.at(temps_synchro)

    def exporter_satellite(geocentrique, temps_array, nom_fichier):
        positions = geocentrique.position.km       
        vitesses = geocentrique.velocity.km_per_s  
        
        with open(nom_fichier, mode='w', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow(['temps_utc', 'x_km', 'y_km', 'z_km', 'vx_km_s', 'vy_km_s', 'vz_km_s'])
            
            for i in range(len(temps_array)):
                writer.writerow([
                    temps_array[i].utc_strftime('%Y-%m-%d %H:%M:%S'), 
                    positions[0][i],  
                    positions[1][i],  
                    positions[2][i],  
                    vitesses[0][i],   
                    vitesses[1][i],   
                    vitesses[2][i]    
                ])
        print(f" -> Fichier {nom_fichier} généré avec succès !")

    # 4. Écriture des fichiers
    exporter_satellite(geocentrique_iss, temps_synchro, 'iss_trajectoire.csv')
    exporter_satellite(geocentrique_tianhe, temps_synchro, 'tianhe_trajectoire.csv')
    
    print("Terminé ! Les données sont parfaitement synchronisées.")

if __name__ == "__main__":
    generer_csv_trajectoire()