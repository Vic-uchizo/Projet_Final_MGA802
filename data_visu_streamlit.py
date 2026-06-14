import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os # AJOUT
# # --- ANCIEN CODE SUPPRIME ---
# from orbit import charger_donnees_tle, calculer_trajectoire_orbite, detecter_collisions # AJOUT
# --- NOUVEAU CODE ---
from orbit import charger_donnees_tle, calculer_trajectoire_orbite, detecter_collisions, obtenir_positions_instantanees # AJOUT
# --------------------
from skyfield.api import load # AJOUT
from datetime import timedelta # AJOUT

# 1. Configuration de la page (Doit TOUJOURS être le premier appel Streamlit)
st.set_page_config(page_title="Satellites Tracker", layout="centered")

# # --- ANCIEN CODE SUPPRIME ---
# def generer_graphique_satellites(satellites):

# --- NOUVEAU CODE ---
def generer_graphique_satellites(satellites, orbite_df=None):
# --------------------
    """
    Génère une figure Matplotlib 3D affichant la Terre et des satellites.
    Prend en entrée un DataFrame Pandas contenant 'Nom', 'X', 'Y', 'Z'.
    """
    # Initialisation de la figure Matplotlib
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # --- DESSIN DE LA TERRE (Rayon 6371 km) ---
    rayon_terre = 6371.0
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    
    x_terre = rayon_terre * np.outer(np.cos(u), np.sin(v))
    y_terre = rayon_terre * np.outer(np.sin(u), np.sin(v))
    z_terre = rayon_terre * np.outer(np.ones(np.size(u)), np.cos(v))
    
    # # --- ANCIEN CODE SUPPRIME ---
    # # Affichage de la Terre (wireframe pour être léger)
    # ax.plot_wireframe(x_terre, y_terre, z_terre, color='lightblue', alpha=0.3)
    
    # --- NOUVEAU CODE ---
    # Rendu de la Terre un peu plus propre avec un plot_surface semi-transparent
    ax.plot_surface(x_terre, y_terre, z_terre, color='blue', alpha=0.1, edgecolor='lightblue', linewidth=0.3)
    # --------------------
    
    # --- DESSIN DES SATELLITES ---
    # On ajoute les points correspondants aux coordonnées X, Y, Z
    if not satellites.empty:
        # # --- ANCIEN CODE SUPPRIME ---
        # ax.scatter(satellites['X'], satellites['Y'], satellites['Z'], 
        #            color='red', marker='o', s=20, label='Satellites')
        # 
        # # Optionnel: Ajouter des annotations pour les noms (limité à qq uns pour lisibilité)
        # for i, row in satellites.head(10).iterrows():
        #     ax.text(row['X'], row['Y'], row['Z'], row['Nom'], size=8, zorder=1, color='black')
        
        # --- NOUVEAU CODE ---
        ax.scatter(satellites['X'], satellites['Y'], satellites['Z'], 
                   color='red', marker='o', s=5, label='Satellites globaux', alpha=0.5)
        
    if orbite_df is not None and not orbite_df.empty:
        # On dessine la ligne continue de la trajectoire orbitale
        ax.plot(orbite_df['X'], orbite_df['Y'], orbite_df['Z'], 
                color='green', linewidth=2, label='Orbite (90 min)')
        # On marque la position actuelle du satellite ciblé avec une grosse étoile
        ax.scatter(orbite_df['X'].iloc[0], orbite_df['Y'].iloc[0], orbite_df['Z'].iloc[0], 
                   color='lime', marker='*', s=100, label='Position Actuelle')
        # --------------------
    
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km)')
    
    # Force les proportions 3D à être égales (évite que la terre ressemble à un œuf)
    ax.set_box_aspect([1, 1, 1]) 
    
    ax.legend()
    
    return fig

def main():
    # ==========================================
    # INTERFACE STREAMLIT
    # ==========================================
    st.title("🛰️ Visualisation des Satellites autour de la Terre")

    # # --- ANCIEN CODE SUPPRIME ---
    # st.markdown("Ceci est une interface de test pour vérifier l'affichage 3D de la Terre et de quelques objets en orbite.")
    # 
    # # 1. On crée nos fausses données pour le test
    # donnees_test = [
    #     {'Nom': 'ISS', 'X': 6800.0, 'Y': 0.0, 'Z': 0.0},
    #     {'Nom': 'STARLINK-A', 'X': 0.0, 'Y': 6900.0, 'Z': 1000.0},
    #     {'Nom': 'STARLINK-B', 'X': -4000.0, 'Y': -5000.0, 'Z': 4000.0},
    # ]
    # df_satellites = pd.DataFrame(donnees_test)
    # 
    # st.write("### Tableau des données actuelles")
    # st.dataframe(df_satellites)
    # 
    # # 2. Générer et afficher le graphique
    # st.write("### Visualisation 3D")
    # fig = generer_graphique_satellites(df_satellites)
    # st.pyplot(fig)
    
    # --- NOUVEAU CODE ---
    chemin_csv = os.path.join('donnees', 'positions_instantanees.csv')
    chemin_tle = os.path.join('donnees', 'starlink.txt')
    chemin_debris = os.path.join('donnees', 'cosmos-2251-debris.txt')
    
    # # --- ANCIEN CODE SUPPRIME ---
    # if not os.path.exists(chemin_csv):
    #     st.error("⚠️ Fichier CSV introuvable. Veuillez exécuter l'option 1 dans main.py d'abord pour générer l'instantané.")
    #     return
    #     
    # # 1. Chargement des données globales
    # df_satellites = pd.read_csv(chemin_csv)
    
    # --- NOUVEAU CODE ---
    if not os.path.exists(chemin_tle) or not os.path.exists(chemin_debris):
        st.error("⚠️ Fichiers bruts TLE introuvables. Veuillez exécuter l'option 1 dans main.py d'abord pour les télécharger.")
        return
        
    @st.cache_data
    def charger_ou_generer_donnees_globales(chemin_tle_fichier, chemin_csv_fichier):
        """Génère le CSV si manquant (au lancement de Streamlit) ou le charge s'il existe déjà."""
        if not os.path.exists(chemin_csv_fichier):
            satellites_tle = charger_donnees_tle(chemin_tle_fichier)
            ts = load.timescale()
            maintenant = ts.now()
            # Génération à l'instant T
            df = obtenir_positions_instantanees(satellites_tle, maintenant)
            # On le sauvegarde pour éviter de tout refaire à chaque fois
            os.makedirs(os.path.dirname(chemin_csv_fichier), exist_ok=True)
            df.to_csv(chemin_csv_fichier, index=False)
            return df
        else:
            return pd.read_csv(chemin_csv_fichier)
            
    with st.spinner("Initialisation et calcul des positions instantanées (peut prendre quelques secondes)..."):
        df_satellites = charger_ou_generer_donnees_globales(chemin_tle, chemin_csv)
    # --------------------
    
    st.write(f"### 🌐 Vue Globale ({len(df_satellites)} satellites en direct)")
    st.dataframe(df_satellites.head(50)) # Aperçu
    
    st.write("---")
    st.write("### 🎯 Sélection et Analyse Orbitale")
    liste_noms = df_satellites['Nom'].tolist()
    sat_choisi = st.selectbox("Choisissez un satellite à tracer et analyser :", liste_noms)
    
    if st.button("Lancer l'analyse (Trajectoire & Collisions)"):
        with st.spinner("Analyse orbitale en cours... (Cela peut prendre quelques secondes)"):
            # On recharge les objets TLE pour les calculs poussés
            satellites_tle = charger_donnees_tle(chemin_tle)
            debris_tle = charger_donnees_tle(chemin_debris)
            
            # Récupération de l'objet satellite exact choisi par l'utilisateur
            cible = next((s for s in satellites_tle if s.name == sat_choisi), None)
            
            if cible:
                ts = load.timescale()
                maintenant = ts.now()
                
                # Calcul de son path (orbite sur 90 min)
                df_orbite = calculer_trajectoire_orbite(cible, maintenant, duree_minutes=90)
                
                # Affichage Graphique
                st.write("#### 1. Visualisation 3D")
                # On affiche un échantillon aléatoire des autres satellites pour ne pas faire ramer matplotlib
                echantillon_fond = df_satellites.sample(min(200, len(df_satellites)))
                fig = generer_graphique_satellites(echantillon_fond, orbite_df=df_orbite)
                st.pyplot(fig)
                
                # Détection des collisions
                st.write("#### 2. Rapport de Collisions (sur 24h)")
                
                # --- NOUVEAU CODE : DIAGNOSTIC ---
                noms_debris = [d.name.strip() for d in debris_tle]
                st.info(f"🔍 DEBUG: {len(debris_tle)} débris ont été chargés depuis le fichier txt.")
                
                with st.expander("👀 Voir la liste de tous les débris chargés en mémoire"):
                    st.dataframe(pd.DataFrame({'Nom du débris': noms_debris}))
                # ---------------------------------
                
                demain = ts.from_datetime(maintenant.utc_datetime() + timedelta(days=1))
                
                # On analyse désormais TOUTE la liste des débris
                df_col = detecter_collisions(cible, debris_tle, maintenant, demain, seuil_km=50.0)
                
                if df_col.empty:
                    st.success(f"✅ Aucune collision critique (seuil 50km) détectée pour {sat_choisi} dans les prochaines 24h.")
                else:
                    st.error(f"⚠️ DANGER : Rapprochements critiques détectés pour {sat_choisi} !")
                    st.dataframe(df_col)
            else:
                st.error("Erreur : Impossible de retrouver les paramètres orbitaux du satellite.")
    # --------------------

if __name__ == "__main__":
    main()