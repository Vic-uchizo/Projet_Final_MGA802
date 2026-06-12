import numpy as np
import streamlit as st
from data_visu_streamlit import generer_graphique_satellites
from table_sat_tempo import get_satellite_dataframe, get_satellite_position
import random

def initiliasation_streamlit():
    # Configuration globale de la page Web Streamlit
    st.set_page_config(page_title="Simulateur de Satellites Starlink", layout="wide")

    st.title("Simulateur & Visualisation de Satellites ")
    st.caption(
        "Données calculées en temps réel par rapport au centre de la Terre (en kilomètres)"
    )

# Chargement du DataFrame (mis en cache par Streamlit pour éviter de relire le fichier de 10 000 lignes à chaque clic)
@st.cache_data
def charger_donnees():
    return get_satellite_dataframe("donnees/starlink.txt")

def extraire_nom_satellite(df_sat, nom_sat_ou_dataframe):
    """Extrait le vrai nom et le nom de recherche d'un satellite, qu'il soit fourni sous forme de texte ou de DataFrame.
        Fonction faite a l'aide de l'ia
    """
    if isinstance(nom_sat_ou_dataframe, str):
        # Si c'est du texte, on cherche le vrai nom dans le DataFrame
        match = df_sat[
            df_sat["Satellite"].str.contains(
                nom_sat_ou_dataframe, case=False, na=False
            )
        ]
        vrai_nom = match.iloc[0]["Satellite"]
        # Pour la recherche, on garde le texte saisi pour get_satellite_position
        nom_pour_position = nom_sat_ou_dataframe
    else:
        # Si c'est déjà une ligne de DataFrame (tirage au sort)
        vrai_nom = nom_sat_ou_dataframe.iloc[0]["Satellite"]
        nom_pour_position = vrai_nom

    return vrai_nom, nom_pour_position

def affichage_sat(df_sat,nom_sat):

    vrai_nom, nom_pour_position = extraire_nom_satellite(df_sat, nom_sat)
    position_array = get_satellite_position(df_sat, nom_pour_position)

        # Calcul des métriques et affichage du graphique
    x, y, z = (
        position_array[0, 0],
        position_array[0, 1],
        position_array[0, 2],
    )
    distance = np.sqrt(x**2 + y**2 + z**2)
    altitude = distance - 6371.0

    st.subheader(f"Donnees du satellites : {vrai_nom}")
    col1, col2= st.columns(2)
    col1.metric(label="Altitude estimée", value=f"{altitude:.2f} km")
    col2.metric(
        label="Distance au centre Terre", value=f"{distance:.2f} km"
    )

    st.write("---")
    generer_graphique_satellites(position_array, [vrai_nom])

def fenetre_streamlit():
    initiliasation_streamlit()
    df_sat = charger_donnees()

    # --- INTERFACE DE LA BARRE LATÉRALE (SIDEBAR) ---
    st.sidebar.header("Paramètres de recherche")

    choix = st.sidebar.radio(
        "Que souhaitez-vous faire ?",
        options=[
            "Voir plusieurs satellites",
            "Voir un satellite en particulier",
            "Voir un satellite au hasard",
        ],
    )

    # Option : Voir un satellite spécifique
    if choix == "Voir un satellite en particulier":
        nom_recherche = st.sidebar.text_input(
            "Entrez le numéro ou le nom du satellite :"
        )

        if nom_recherche:
            # On extrait la position (Tableau Numpy)
            existe_dans_donne = df_sat[df_sat["Satellite"].str.contains(nom_recherche, case=False, na=False)]

            if not existe_dans_donne.empty:
                affichage_sat(df_sat,nom_recherche)
            else:
                # Si le sous-tableau est vide, le nom n'est pas dans la liste !
                st.error(
                    f" Le satellite '{nom_recherche}' n'existe pas dans la base de données. Réessayez."
                )

    # Option : Au hasard 
    elif choix == "Voir un satellite au hasard":
        if st.sidebar.button("Prendre un autre satellite"):
            st.rerun()
        satellite_random = df_sat.sample(n=1)
        affichage_sat(df_sat,satellite_random)

    elif choix=="Voir plusieurs satellites":
        liste_position=[]
        liste_nom=[]
        satellite_choisies=[]
        for i in range(3):
            nom = st.sidebar.text_input(
                f"Entrez le numéro ou le nom du satellite {i+1} :",
                key=f"sat_input_{i}"
            )
            if nom.strip():
                satellite_choisies.append(nom.strip())

        for nom_recherche in satellite_choisies :
            existe_dans_donne = df_sat[df_sat["Satellite"].str.contains(nom_recherche, case=False, na=False)]
            if not existe_dans_donne.empty :
                vrai_nom = existe_dans_donne.iloc[0]["Satellite"]
                position_array = get_satellite_position(df_sat, nom_recherche)
                liste_nom.append(vrai_nom)
                liste_position.append(position_array[0])
        if liste_position:
            st.subheader(f"Visualisation de {len(liste_nom)} satellite(s) en simultané")
            
            # Convertit la liste de coordonnées en un seul tableau NumPy (matrice de taille N x 3)
            positions_combinees = np.array(liste_position)
            
            # On envoie TOUT d'un coup au graphique
            generer_graphique_satellites(positions_combinees, liste_nom)
        
if __name__ == "__main__":
    fenetre_streamlit()