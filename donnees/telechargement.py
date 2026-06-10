"""
Telechargement des donnees orbitales BRUTES depuis CelesTrak (Etape 1, P1).

Ce module fait UNIQUEMENT le telechargement du fichier TLE brut et sa mise en
cache locale. Il ne fait aucun calcul.

L'interpretation des donnees (lecture du TLE, calcul des positions XYZ) est le
travail de P2 et se trouve dans le module 'orbites/'.

    CelesTrak (web)  --requests-->  fichier TLE local (.txt)
"""

import os
import requests

# Dossier ou on sauvegarde les fichiers TLE telecharges
DOSSIER = os.path.dirname(os.path.abspath(__file__))


def telecharger_tle(groupe, fichier):
    """Telecharge le TLE d'un groupe CelesTrak et le sauvegarde en local.

    :param groupe: nom du groupe CelesTrak, ex. "starlink" ou "cosmos-2251-debris"
    :param fichier: chemin du fichier .txt ou sauvegarder le TLE
    :return: le chemin du fichier sauvegarde
    """
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={groupe}&FORMAT=tle"
    print(f"Telechargement de {groupe} ...")
    reponse = requests.get(url, timeout=30)
    reponse.raise_for_status()          # erreur claire si le serveur repond mal

    # CelesTrak repond parfois "data not updated..." (code 200) au lieu du TLE.
    # On verifie que c'est bien du TLE avant de sauvegarder, sinon on cree un
    # fichier casse. Un vrai TLE a des lignes commencant par "1 " et "2 ".
    texte = reponse.text
    if not ("\n1 " in texte and "\n2 " in texte):
        raise RuntimeError(
            f"CelesTrak n'a pas renvoye de TLE pour '{groupe}'. Reponse recue :\n"
            f"{texte[:200]}\n"
            "Reessayez plus tard (CelesTrak limite les telechargements repetes)."
        )

    with open(fichier, "w") as f:
        f.write(texte)
    print(f"  -> sauvegarde dans {fichier}")
    return fichier


def obtenir_fichier_tle(groupe):
    """Renvoie le chemin du fichier TLE local, en le telechargeant s'il manque.

    C'est la fonction a utiliser par les autres modules : elle garantit que le
    fichier brut existe en local (telecharge une seule fois), puis renvoie son
    chemin. Aucun re-telechargement si le fichier est deja present.

    :param groupe: nom du groupe CelesTrak (ex. "starlink")
    :return: chemin du fichier TLE local
    """
    fichier = os.path.join(DOSSIER, f"{groupe}.txt")
    if not os.path.exists(fichier):
        telecharger_tle(groupe, fichier)
    return fichier


if __name__ == "__main__":
    # Demonstration : on s'assure d'avoir le fichier brut Starlink en local.
    chemin = obtenir_fichier_tle("starlink")
    print("Fichier TLE pret :", chemin)
