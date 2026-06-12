import numpy as np
import streamlit as st
from data_visu_streamlit import generer_graphique_satellites
from table_sat_tempo import get_satellite_dataframe, get_satellite_position
import random

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


df_sat = charger_donnees()

# --- INTERFACE DE LA BARRE LATÉRALE (SIDEBAR) ---
st.sidebar.header("Paramètres de recherche")

choix = st.sidebar.radio(
    "Que souhaitez-vous faire ?",
    options=[
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
            # S'il existe, on récupère son vrai nom et sa position
            vrai_nom = existe_dans_donne.iloc[0]["Satellite"]
            position_array = get_satellite_position(df_sat, nom_recherche)

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
    nom_sat_random=satellite_random.iloc[0]["Satellite"]
    position_array = get_satellite_position(df_sat, nom_sat_random)

    # Calcul des métriques et affichage du graphique
    x, y, z = (
        position_array[0, 0],
        position_array[0, 1],
        position_array[0, 2],
    )
    distance = np.sqrt(x**2 + y**2 + z**2)
    altitude = distance - 6371.0

    st.subheader(f"Donnees du satellites : {nom_sat_random}")
    col1, col2= st.columns(2)
    col1.metric(label="Altitude estimée", value=f"{altitude:.2f} km")
    col2.metric(
        label="Distance au centre Terre", value=f"{distance:.2f} km"
    )

    st.write("---")
    generer_graphique_satellites(position_array, [nom_sat_random])
