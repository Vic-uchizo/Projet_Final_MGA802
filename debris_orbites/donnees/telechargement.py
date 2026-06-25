"""
Telechargement des donnees orbitales BRUTES depuis CelesTrak (Etape 1, P1).

Ce module fait UNIQUEMENT le telechargement du fichier TLE brut et sa mise en
cache locale. Il ne fait aucun calcul.

L'interpretation des donnees (lecture du TLE, calcul des positions XYZ) est le
travail de P2 et se trouve dans le module 'orbit.py'.

    CelesTrak (web)  --requests-->  fichier TLE local (.txt)

La logique est encapsulee dans la classe :class:`TelechargeurTLE`. Des fonctions
de compatibilite (``obtenir_fichier_tle``, ``telecharger_tle``) sont conservees
pour le code existant qui les importe directement.
"""

import os
import requests

# Dossier ou on sauvegarde les fichiers TLE telecharges.
# Ce module vit dans debris_orbites/donnees/ ; les fichiers de donnees, eux,
# sont ranges a la RACINE du projet dans "donnees_tle/" (hors du package).
# On remonte donc de 3 niveaux pour retrouver la racine, peu importe le cwd.
_RACINE_PROJET = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(_RACINE_PROJET, "donnees_tle")

# Les groupes de donnees utilises par le projet (choix d'equipe) :
#   - "starlink"           : les satellites (LEO, ~10 500 objets)
#   - "cosmos-2251-debris" : les debris de la collision de 2009 (LEO, ~600 objets)
GROUPES = ["starlink", "cosmos-2251-debris"]


class TelechargeurTLE:
    """Telecharge et met en cache les fichiers TLE bruts depuis CelesTrak.

    L'objet encapsule le dossier de destination et la liste des groupes a
    recuperer. Il telecharge un groupe une seule fois : si le fichier local
    existe deja, il n'est pas re-telecharge.

    :param dossier: dossier local ou ranger les fichiers .txt, defaults to
        ``DOSSIER`` (``<racine>/donnees_tle``)
    :type dossier: str, optional
    :param groupes: liste des groupes CelesTrak geres par defaut,
        defaults to ``GROUPES``
    :type groupes: list[str], optional
    """

    #: Modele d'URL CelesTrak (format TLE) ; ``{groupe}`` est remplace a l'appel.
    URL_MODELE = "https://celestrak.org/NORAD/elements/gp.php?GROUP={groupe}&FORMAT=tle"

    def __init__(self, dossier=DOSSIER, groupes=None):
        self.dossier = dossier
        self.groupes = list(groupes) if groupes is not None else list(GROUPES)

    def chemin_fichier(self, groupe):
        """Retourne le chemin local du fichier .txt d'un groupe (sans le telecharger).

        :param groupe: nom du groupe CelesTrak (ex. "starlink")
        :type groupe: str
        :return: chemin du fichier TLE local
        :rtype: str
        """
        return os.path.join(self.dossier, f"{groupe}.txt")

    def telecharger(self, groupe, fichier):
        """Telecharge le TLE d'un groupe CelesTrak et le sauvegarde en local.

        :param groupe: nom du groupe CelesTrak, ex. "starlink" ou "cosmos-2251-debris"
        :type groupe: str
        :param fichier: chemin du fichier .txt ou sauvegarder le TLE
        :type fichier: str
        :return: le chemin du fichier sauvegarde
        :rtype: str
        :raises RuntimeError: si CelesTrak ne renvoie pas un vrai TLE.
        """
        url = self.URL_MODELE.format(groupe=groupe)
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

        os.makedirs(os.path.dirname(fichier), exist_ok=True)
        with open(fichier, "w") as f:
            f.write(texte)
        print(f"  -> sauvegarde dans {fichier}")
        return fichier

    def obtenir_fichier(self, groupe):
        """Renvoie le chemin du fichier TLE local, en le telechargeant s'il manque.

        C'est la methode a utiliser par les autres modules : elle garantit que le
        fichier brut existe en local (telecharge une seule fois), puis renvoie son
        chemin. Aucun re-telechargement si le fichier est deja present.

        :param groupe: nom du groupe CelesTrak (ex. "starlink")
        :type groupe: str
        :return: chemin du fichier TLE local
        :rtype: str
        """
        fichier = self.chemin_fichier(groupe)
        if not os.path.exists(fichier):
            self.telecharger(groupe, fichier)
        return fichier

    def obtenir_tous(self):
        """Garantit que TOUS les groupes configures sont presents en local.

        :return: liste des chemins des fichiers TLE locaux
        :rtype: list[str]
        """
        return [self.obtenir_fichier(groupe) for groupe in self.groupes]


# ---------------------------------------------------------------------------
# COMPATIBILITE ASCENDANTE
# Un telechargeur partage est instancie une fois ; les anciennes fonctions de
# module restent disponibles pour le code qui fait
# « from ...telechargement import obtenir_fichier_tle, GROUPES ».
# ---------------------------------------------------------------------------
_telechargeur_par_defaut = TelechargeurTLE()


def telecharger_tle(groupe, fichier):
    """Passerelle vers :meth:`TelechargeurTLE.telecharger`."""
    return _telechargeur_par_defaut.telecharger(groupe, fichier)


def obtenir_fichier_tle(groupe):
    """Passerelle vers :meth:`TelechargeurTLE.obtenir_fichier`."""
    return _telechargeur_par_defaut.obtenir_fichier(groupe)


if __name__ == "__main__":
    # On s'assure d'avoir TOUS les fichiers bruts du projet en local
    # (telecharges une seule fois chacun).
    for chemin in TelechargeurTLE().obtenir_tous():
        print("Fichier TLE pret :", chemin)
