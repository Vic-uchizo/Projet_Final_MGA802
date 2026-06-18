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
def generer_graphique_satellites(satellites, orbite_df=None, collisions_df=None, cible=None):
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
    
    # Rendu de la Terre avec un plot_surface semi-transparent
    ax.plot_surface(x_terre, y_terre, z_terre, color='blue', alpha=0.1, edgecolor='lightblue', linewidth=0.3)
    
    # --- DESSIN DES SATELLITES ---
    if not satellites.empty:
        if cible is None:
            # Aucun satellite ciblé : tous les satellites sont bleus
            ax.scatter(satellites['X'], satellites['Y'], satellites['Z'], 
                       color='blue', marker='o', s=5, label='Satellites globaux', alpha=0.6)
        else:
            # Un satellite est ciblé : le reste du catalogue passe en gris pour contraster
            ax.scatter(satellites['X'], satellites['Y'], satellites['Z'], 
                       color='grey', marker='o', s=5, label='Autres satellites', alpha=0.3)
            
    # --- DESSIN DE L'ORBITE CIBLE ---
    if orbite_df is not None and not orbite_df.empty:
        # On dessine la ligne continue de la trajectoire orbitale
        ax.plot(orbite_df['X'], orbite_df['Y'], orbite_df['Z'], 
                color='green', linewidth=2, label=f'Orbite ({cible})')
        # On marque la position actuelle du satellite ciblé avec une grosse étoile
        ax.scatter(orbite_df['X'].iloc[0], orbite_df['Y'].iloc[0], orbite_df['Z'].iloc[0], 
                   color='lime', marker='*', s=100, label='Position Actuelle')

    # --- DESSIN DES COLLISIONS POTENTIELLES ---
    if collisions_df is not None and not collisions_df.empty:
        # Affichage des points de collision en étoiles rouges
        ax.scatter(collisions_df['X'], collisions_df['Y'], collisions_df['Z'], 
                   color='red', marker='*', s=100, label='Collisions potentielles', alpha=0.9)

    # --- PARAMÉTRAGE DES AXES ---
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km)')
    
    # Force les proportions 3D à être égales (évite que la terre ressemble à un œuf)
    ax.set_box_aspect([1, 1, 1]) 
    
    # Positionnement de la légende pour éviter de cacher le centre
    ax.legend(loc='upper right')
    
    return fig

# ==========================================
# FONCTIONS MISES EN CACHE (ÉTAPE 3)
# ==========================================
# Streamlit ré-exécute tout le script à chaque interaction. Ces décorateurs
# évitent de refaire les calculs lourds quand les entrées n'ont pas changé.

@st.cache_resource(show_spinner=False)
def charger_catalogue(chemin_fichier):
    """
    Charge une liste de satellites UNE seule fois et la garde en mémoire.
    @st.cache_resource est adapté aux objets "vivants" (EarthSatellite) qui ne
    se sérialisent pas bien : on ne relit donc plus le fichier TLE à chaque clic.
    """
    return charger_donnees_tle(chemin_fichier)


@st.cache_data(show_spinner=False)
def analyser_satellite(nom_cible, chemin_tle, chemin_debris, n_debris, seuil_km, duree_jours):
    """
    Calcule l'orbite + les collisions d'un satellite, et MET LE RÉSULTAT EN CACHE.
    Si on re-sélectionne le même satellite avec les mêmes paramètres, Streamlit
    renvoie le résultat mémorisé instantanément (aucun recalcul).

    NB : tous les arguments sont "hachables" (texte/nombres) ; c'est ce qui permet
    le cache. On reconstruit les objets satellites à l'intérieur via le cache_resource.
    """
    satellites_tle = charger_catalogue(chemin_tle)
    debris_tle = charger_catalogue(chemin_debris)[:n_debris]

    cible = next((s for s in satellites_tle if s.name == nom_cible), None)
    if cible is None:
        return None, None, []

    ts = load.timescale()
    temps_debut = cible.epoch
    # Orbite (trajectoire sur 120 min) + détection des collisions sur la fenêtre
    df_orbite = calculer_trajectoire_orbite(cible, temps_debut, duree_minutes=120)
    temps_fin = ts.from_datetime(temps_debut.utc_datetime() + timedelta(days=duree_jours))
    df_col = detecter_collisions(cible, debris_tle, temps_debut, temps_fin, seuil_km=seuil_km)

    noms_debris = [d.name.strip() for d in debris_tle]
    return df_orbite, df_col, noms_debris


def main():
    # ==========================================
    # INTERFACE STREAMLIT
    # ==========================================
    st.title(" Visualisation des Satellites autour de la Terre")

    chemin_csv = os.path.join('donnees', 'positions_instantanees.csv')
    chemin_csv_d = os.path.join('donnees', 'positions_instantanees_debris.csv')
    chemin_tle = os.path.join('donnees', 'starlink.txt')
    chemin_debris = os.path.join('donnees', 'cosmos-2251-debris.txt')
    
    if not os.path.exists(chemin_tle) or not os.path.exists(chemin_debris):
        st.error(" Fichiers bruts TLE introuvables. Veuillez exécuter l'option 1 dans main.py d'abord pour les télécharger.")
        return
        
    @st.cache_data
    def charger_ou_generer_donnees_globales(chemin_tle_fichier, chemin_csv_fichier):
        """Génère le CSV si manquant (au lancement de Streamlit) ou le charge s'il existe déjà."""
        satellites_tle = charger_donnees_tle(chemin_tle_fichier)
        ts = load.timescale()
        maintenant = ts.now()
        # Génération à l'instant T
        df = obtenir_positions_instantanees(satellites_tle, maintenant)
        # On le sauvegarde pour éviter de tout refaire à chaque fois
        os.makedirs(os.path.dirname(chemin_csv_fichier), exist_ok=True)
        df.to_csv(chemin_csv_fichier, index=False)
        return df

    # Chargement initial
    with st.spinner("Initialisation et calcul des positions instantanées (peut prendre quelques secondes)..."):
        df_satellites = charger_ou_generer_donnees_globales(chemin_tle, chemin_csv)
        df_debris = charger_ou_generer_donnees_globales(chemin_debris, chemin_csv_d)

    # --- SÉLECTION DE LA VUE ---
    # On ajoute une option pour tout voir par défaut au début de la liste
    options_affichage = ["🌐 Vue Globale (Tous les satellites)"] + df_satellites['Nom'].tolist()
    
    st.write("### 🎯 Paramètres d'affichage")
    sat_choisi = st.selectbox("Choisissez la vue globale ou un satellite spécifique :", options_affichage)
    st.write("---")

    st.write("### 🌍 Carte 3D en Direct")
    
    # On prépare un échantillon de fond pour ne pas surcharger Matplotlib
    echantillon_fond = df_satellites.sample(min(200, len(df_satellites)))

    # ==========================================
    # LOGIQUE D'AFFICHAGE DYNAMIQUE
    # ==========================================
    if sat_choisi == "🌐 Vue Globale (Tous les satellites)":
        # 1. CAS VUE GLOBALE : On affiche juste la terre et tous les satellites bleus
        fig = generer_graphique_satellites(echantillon_fond, cible=None)
        st.pyplot(fig)
        
        # Affichage des données sous la carte
        st.write(f"#### 📊 Données Brutes ({len(df_satellites)} satellites actifs)")
        st.dataframe(df_satellites)
        
        with st.expander("Voir les données des débris"):
            st.dataframe(df_debris)

    else:
        # 2. CAS SATELLITE CIBLÉ : On calcule l'orbite et les collisions
        # L'appel est mis en cache : ~2s au 1er calcul, INSTANTANÉ ensuite
        # (re-sélection du même satellite, ouverture d'un expander, etc.)
        with st.spinner(f"Analyse orbitale de {sat_choisi} en cours..."):
            df_orbite, df_col, noms_debris = analyser_satellite(
                sat_choisi, chemin_tle, chemin_debris,
                n_debris=50, seuil_km=300.0, duree_jours=1
            )

        if df_orbite is not None:
            # Génération de la carte 3D mise à jour (fond gris, orbite verte, collisions rouges)
            fig = generer_graphique_satellites(
                echantillon_fond,
                orbite_df=df_orbite,
                collisions_df=df_col if not df_col.empty else None,
                cible=sat_choisi
            )
            st.pyplot(fig)

            # --- AFFICHAGE DES RAPPORTS SOUS LA CARTE ---
            st.write("####  Rapport de Collisions (sur 24h)")
            if df_col.empty:
                st.success(f" Aucune collision critique détectée pour {sat_choisi} dans les prochaines 24h.")
            else:
                st.error(f" DANGER : Rapprochements critiques détectés pour {sat_choisi} !")
                st.dataframe(df_col)

            # Optionnel : garder le module de diagnostic caché
            with st.expander("🔍 Diagnostics Débris"):
                st.info(f"{len(noms_debris)} débris analysés.")
                st.dataframe(pd.DataFrame({'Nom du débris': noms_debris}))

        else:
            st.error("Erreur : Impossible de retrouver les paramètres orbitaux du satellite.")

if __name__ == "__main__":
    main()