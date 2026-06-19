import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os # AJOUT
# # --- ANCIEN CODE SUPPRIME ---
# from orbit import charger_donnees_tle, calculer_trajectoire_orbite, detecter_collisions # AJOUT
# --- NOUVEAU CODE ---
from orbit import charger_donnees_tle, calculer_trajectoire_orbite, detecter_collisions, obtenir_positions_instantanees # AJOUT
from maneuver import evasive_maneuver
# --------------------
from skyfield.api import load # AJOUT
from datetime import timedelta # AJOUT

###Fonction obligatoire pour faire tourner le code avec streamlit en parallele

@st.cache_data(show_spinner=False)
def analyser_satellite(nom_cible, chemin_tle, chemin_debris, seuil_km, duree_jours,n_debris):
    """Calcule l'orbite + les collisions d'un satellite et met le résultat en cache."""
    satellites_tle = charger_catalogue(chemin_tle)
    if n_debris is not None :
        debris_tle = charger_catalogue(chemin_debris)[:n_debris]
    else :
        debris_tle = charger_catalogue(chemin_debris)

    cible = next((s for s in satellites_tle if s.name == nom_cible), None)
    if cible is None:
        return None, None, []

    ts = load.timescale()
    temps_debut = cible.epoch
    
    df_orbite = calculer_trajectoire_orbite(cible, temps_debut, duree_minutes=120)
    temps_fin = ts.from_datetime(temps_debut.utc_datetime() + timedelta(days=duree_jours))
    df_col = detecter_collisions(cible, debris_tle, temps_debut, temps_fin, seuil_km=seuil_km)

    noms_debris = [d.name.strip() for d in debris_tle]
    return df_orbite, df_col, noms_debris

@st.cache_resource(show_spinner=False)
def charger_catalogue(chemin_fichier):
    """Charge une liste de satellites UNE seule fois et la garde en mémoire."""
    return charger_donnees_tle(chemin_fichier)

@st.cache_data
def _calculer_positions_cache(chemin_tle_fichier, chemin_csv_fichier):
    """Fonction isolée pour permettre à Streamlit de mettre les données en cache efficacement."""
    satellites_tle = charger_donnees_tle(chemin_tle_fichier)
    ts = load.timescale()
    maintenant = ts.now()
    
    df = obtenir_positions_instantanees(satellites_tle, maintenant)
    
    os.makedirs(os.path.dirname(chemin_csv_fichier), exist_ok=True)
    df.to_csv(chemin_csv_fichier, index=False)
    return df

####


class Graphique:
    @staticmethod
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


class Analyse:
    @staticmethod
    def analyser_satellite(nom_cible, chemin_tle, chemin_debris, seuil_km, duree_jours,n_debris=None):
        # On délègue le travail à la fonction cachée
        return analyser_satellite(nom_cible, chemin_tle, chemin_debris, seuil_km, duree_jours,n_debris)

class Interface:
    def __init__(self,chemin_csv,chemin_csv_d,chemin_tle,chemin_debris):
        self.chemin_csv=chemin_csv
        self.chemin_csv_d=chemin_csv_d
        self.chemin_tle=chemin_tle
        self.chemin_debris=chemin_debris
    
    def verifier_fichier(self):
        if not os.path.exists(self.chemin_tle) or not os.path.exists(self.chemin_debris):
            st.error(" Fichiers bruts TLE introuvables. Veuillez exécuter l'option 1 dans main.py d'abord pour les télécharger.")
            return False
        return True
        
    def charger_ou_generer_donnees_globales(self, type_donnees='satellites'):
        """Génère le CSV si manquant ou le charge s'il existe déjà."""
        # On choisit les bons chemins selon qu'on charge les satellites ou les débris
        chemin_tle_fichier = self.chemin_tle if type_donnees == 'satellites' else self.chemin_debris
        chemin_csv_fichier = self.chemin_csv if type_donnees == 'satellites' else self.chemin_csv_d

        # On appelle une fonction statique (définie plus bas) pour que le cache Streamlit fonctionne
        return _calculer_positions_cache(chemin_tle_fichier, chemin_csv_fichier)

    def chargement_initial(self):
        with st.spinner("Initialisation et calcul des positions instantanées (peut prendre quelques secondes)..."):
            self.df_satellites = self.charger_ou_generer_donnees_globales('satellites')
            self.df_debris = self.charger_ou_generer_donnees_globales('debris')
            
    def afficher_interface(self):
        # On ajoute une option pour tout voir par défaut au début de la liste
        options_affichage = ["🌐 Vue Globale (Tous les satellites)"] + self.df_satellites['Nom'].tolist()
        
        st.write("### 🎯 Paramètres d'affichage")
        sat_choisi = st.selectbox("Choisissez la vue globale ou un satellite spécifique :", options_affichage)
        st.write("---")

        st.write("### 🌍 Carte 3D en Direct")
        
        # On prépare un échantillon de fond pour ne pas surcharger Matplotlib
        echantillon_fond = self.df_satellites.sample(min(200, len(self.df_satellites)))

        # ==========================================
        # LOGIQUE D'AFFICHAGE DYNAMIQUE
        # ==========================================
        if sat_choisi == "🌐 Vue Globale (Tous les satellites)":
            # 1. CAS VUE GLOBALE : On affiche juste la terre et tous les satellites bleus
            fig = Graphique.generer_graphique_satellites(echantillon_fond, cible=None)
            st.pyplot(fig)
            
            # Affichage des données sous la carte
            st.write(f"#### 📊 Données Brutes ({len(self.df_satellites)} satellites actifs)")
            st.dataframe(self.df_satellites)
            
            with st.expander("Voir les données des débris"):
                st.dataframe(self.df_debris)

        else:
            # 2. CAS SATELLITE CIBLÉ : On calcule l'orbite et les collisions
            # L'appel est mis en cache : ~2s au 1er calcul, INSTANTANÉ ensuite
            # (re-sélection du même satellite, ouverture d'un expander, etc.)
            with st.spinner(f"Analyse orbitale de {sat_choisi} en cours..."):
                df_orbite, df_col, noms_debris = Analyse.analyser_satellite(
                    sat_choisi, self.chemin_tle, self.chemin_debris,
                     seuil_km=300.0, duree_jours=1,n_debris=None
                )

            if df_orbite is not None:
                # Génération de la carte 3D mise à jour (fond gris, orbite verte, collisions rouges)
                fig = Graphique.generer_graphique_satellites(
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
                    # 1. Calcul de la manœuvre d'évitement
                    evasive = evasive_maneuver(sat_choisi, df_col, altitude_evasion_km=10.0, inclination_change=0.0, eleve_orbit=True)

                    # 2. Affichage propre dans Streamlit
                    if evasive: # Si la liste n'est pas vide
                        st.write("#### Plan de Manœuvre d'Évitement")
                        st.warning("Recommandation de poussée pour esquiver les impacts :")            
                        # Conversion de la liste de dicts en DataFrame Pandas
                        df_manoeuvres = pd.DataFrame(evasive)
                        st.dataframe(df_manoeuvres, use_container_width=True)
                        
                    else:
                        st.info("Aucune manœuvre d'évitement requise.")


                # Optionnel : garder le module de diagnostic caché
                with st.expander("🔍 Diagnostics Débris"):
                    st.info(f"{len(noms_debris)} débris analysés.")
                    st.dataframe(pd.DataFrame({'Nom du débris': noms_debris}))

            else:
                st.error("Erreur : Impossible de retrouver les paramètres orbitaux du satellite.")
def main():
    # Chemins des fichiers
    chemin_csv = os.path.join('donnees', 'positions_instantanees.csv')
    chemin_csv_d = os.path.join('donnees', 'positions_instantanees_debris.csv')
    chemin_tle = os.path.join('donnees', 'starlink.txt')
    chemin_debris = os.path.join('donnees', 'cosmos-2251-debris.txt')

    # Initialisation de l'interface
    app = Interface(chemin_csv, chemin_csv_d, chemin_tle, chemin_debris)
    
    # Exécution de l'application s'il n'y a pas d'erreur de fichiers
    if app.verifier_fichier():
        app.chargement_initial()   # Récupère et met en cache les données
        app.afficher_interface()   # Lance le rendu de la page Streamlit

if __name__ == "__main__":
    main()