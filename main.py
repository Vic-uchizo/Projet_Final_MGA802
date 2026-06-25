"""
Script principal (Point d'entrée) du projet MGA802.
Permet de gérer l'exécution des différents modules avec un menu interactif.

Toute la logique est encapsulée dans la classe :class:`Application`.
"""

import os
import sys
import subprocess
from debris_orbites.donnees.telechargement import obtenir_fichier_tle, GROUPES


class Application:
    """Application en ligne de commande du projet MGA802.

    Encapsule la configuration (dossier de données, fichiers TLE, script de
    l'interface) et les actions du menu interactif : télécharger les données
    et lancer l'interface 3D Streamlit.

    :param dossier_donnees: dossier où se trouvent les fichiers TLE,
        defaults to ``'donnees_tle'``
    :type dossier_donnees: str, optional
    """

    #: Script Streamlit lancé par l'option 2 du menu.
    SCRIPT_INTERFACE = 'data_visu_streamlit.py'

    def __init__(self, dossier_donnees='donnees_tle'):
        self.dossier_donnees = dossier_donnees
        self.fichier_tle = os.path.join(dossier_donnees, 'starlink.txt')
        self.fichier_debris = os.path.join(dossier_donnees, 'cosmos-2251-debris.txt')

    def gerer_donnees(self):
        """Gère l'option 1 : Téléchargement des TLE en .txt.

        :return: None
        :rtype: None
        """
        # 1. Vérification si les données existent déjà
        if os.path.exists(self.fichier_tle) and os.path.exists(self.fichier_debris):
            print(f"\n[INFO] Des fichiers TLE existants ont été détectés.")
            confirmation = input("Voulez-vous vraiment re-télécharger les TLE ? (o/n) : ")

            if confirmation.lower() != 'o':
                print("Action annulée. Retour au menu.")
                return

        # 2. Lancement du téléchargement
        print("\n--- Téléchargement des données ---")
        try:
            # On s'assure que le dossier existe
            os.makedirs(self.dossier_donnees, exist_ok=True)

            # On itère sur les groupes configurés dans telechargement.py
            for groupe in GROUPES:
                # On stocke temporairement dans le dossier actuel pour correspondre à telechargement.py
                obtenir_fichier_tle(groupe)

            print("\n[SUCCÈS] Toutes les données brutes ont été téléchargées.")
            print("Vous pouvez maintenant utiliser l'option 2 pour la visualisation interactive. Les positions seront calculées au lancement.")

        except Exception as e:
            print(f"\n[ERREUR] Un problème est survenu lors du téléchargement : {e}")

    def lancer_interface(self):
        """Gère l'option 2 : Lancement de l'interface graphique via Streamlit.

        :return: None
        :rtype: None
        """
        print("\nLancement de l'interface Streamlit...")
        print("Pour arrêter l'interface, faites Ctrl+C dans ce terminal.")
        try:
            # sys.executable correspond au chemin exact du Python utilisé actuellement.
            # Cela force l'appel à "python -m streamlit run data_visu_streamlit.py" et
            # règle les problèmes de PATH.
            subprocess.run([sys.executable, "-m", "streamlit", "run", self.SCRIPT_INTERFACE])
        except Exception as e:
            print(f"ERREUR inattendue lors du lancement : {e}")
            print("Assurez-vous de l'avoir installé : pip install streamlit")

    def menu_principal(self):
        """Boucle principale du programme : affiche le menu et route les choix.

        :return: None
        :rtype: None
        """
        while True:
            print("\n" + "="*50)
            print("   PROJET MGA802 - SIMULATEUR ORBITAL")
            print("="*50)
            print(" 1. Récupérer les données spatiales")
            print(" 2. Lancer l'interface 3D (Streamlit)")
            print(" 3. Quitter le programme")
            print("="*50)

            choix = input("Choisissez une option (1, 2 ou 3) : ")

            # Gestion de l'erreur ValueError si l'utilisateur rentre une lettre au lieu d'un chiffre
            try:
                choix_int = int(choix)
            except ValueError:
                print("\nERREUR : Valeur invalide. Veuillez entrer uniquement un chiffre (1, 2 ou 3).")
                continue

            # Routage selon l'option choisie
            if choix_int == 1:
                self.gerer_donnees()
            elif choix_int == 2:
                self.lancer_interface()
            elif choix_int == 3:
                print("Fermeture du programme. À bientôt !")
                sys.exit(0)
            else:
                print("ERREUR : Option inconnue. Veuillez choisir 1, 2 ou 3.")


if __name__ == "__main__":
    Application().menu_principal()
