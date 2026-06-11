'''
Script pour récuperer en entrée un .txt rempli de TLE et 
le transformer en orbite au travers d'un .csv avec un 
temps universel pour synchroniser les mouvements
'''

import csv
from skyfield.api import load
import numpy as np

def generer_csv_orbite(nom_fichier):
    ts = load.timescale()
    
    # --- CRÉATION DE L'HORLOGE SYNCHRONISÉE ---
    # On crée une simulation qui commence le 10 juin 2026 à 12h00 UTC
    # On simule 120 minutes (2 heures) avec 1 calcul par minute.
    minutes_simul = np.arange(0, 120, 1) 
    temps_synchro = ts.utc(2026, 6, 10, 12, minutes_simul)

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
    
    