import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import subprocess
import sys
import os



def generer_graphique_satellites(positions_satellites,names):

        # Configuration de la page Streamlit
    st.set_page_config(page_title="Satellites Tracker", layout="centered")
    st.title(" Visualisation des Satellites autour de la Terre")
    # Initialisation de la figure Matplotlib
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 1. DESSIN DE LA TERRE (Rayon 6371 km)
    rayon_terre = 6371.0
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    
    x_terre = rayon_terre * np.outer(np.cos(u), np.sin(v))
    y_terre = rayon_terre * np.outer(np.sin(u), np.sin(v))
    z_terre = rayon_terre * np.outer(np.ones(np.size(u)), np.cos(v))
    
    # Affichage de la Terre
    ax.plot_wireframe(x_terre, y_terre, z_terre, color='royalblue', alpha=0.4, linewidth=0.5, label='Terre')

    # 2. DESSIN DES SATELLITES
    sat_x = positions_satellites[:, 0]
    sat_y = positions_satellites[:, 1]
    sat_z = positions_satellites[:, 2]

    
    # Affichage des points
    ax.scatter(sat_x, sat_y, sat_z, color='orange', s=50, marker='o', label='Satellites')
    
    # Ajout des étiquettes textuelles
    if isinstance(names, str):
        ax.text(sat_x[0] + 100,sat_y[0] + 100,sat_z[0] + 100,names,color="black",fontsize=10,weight="bold",)
        
    # Si jamais plusieurs satellites
    else:
        for i, (x, y, z) in enumerate(positions_satellites):
            ax.text(x + 100,y + 100,z + 100,str(names[i]),color="black",fontsize=9,)

    # 3. CONFIGURATION DES AXES
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km)')
    ax.set_aspect('equal')
    ax.legend()
    
    st.pyplot(fig)
    return fig

# --- Test d'interface ---

 # Code qui s'exécute dans Streamlit
positions = np.array([
 [7000, 0, 0],           # Sat 1
 [0, 7000, 0],           # Sat 2
])
names = ['Galile','Starlink']
# Génération du graphique
fig_espace = generer_graphique_satellites(positions,names)

# Affichage sécurisé dans Streamlit
st.pyplot(fig_espace)

