import math
from sgp4.propagation import false

from .orbit import charger_donnees_tle, detecter_collisions
from skyfield.api import load
from datetime import timedelta


class Manoeuvre:
    # Gravitational constant
    GM = 3.986004418e14
    def __init__(self,satellite_name,df_collision,altitude_evasion_km=10.0, inclinaison_rad=0.0, eleve_orbit=True):
        """Initialise la classe Manoeuvre avec les paramètres de la simulation de collision.

        :param satellite_name: Nom du satellite cible à protéger
        :type satellite_name: str
        :param df_collision: Tableau contenant les données sur les collisions détectées
        :type df_collision: pandas.DataFrame
        :param altitude_evasion_km: Distance de sécurité pour l'évitement en kilomètres, defaults to 10.0
        :type altitude_evasion_km: float, optional
        :param inclinaison_rad: Changement d'inclinaison orbitale souhaité en radians, defaults to 0.0
        :type inclinaison_rad: float, optional
        :param eleve_orbit: Détermine s'il faut rehausser (True) ou abaisser (False) l'orbite, defaults to True
        :type eleve_orbit: bool, optional
        :return: None
        :rtype: None
        """
        self.satellite_name=satellite_name
        self.df_collision=df_collision
        self.altitude_evasion=altitude_evasion_km
        self.inclinaison=inclinaison_rad
        self.eleve_orbit=eleve_orbit

    def orbital_radius(self,cible):
        """Calcule le rayon orbital moyen actuel (demi-grand axe) du satellite à partir de ses données TLE.

        :param cible: Objet satellite Skyfield/SGP4 contenant les éléments orbitaux
        :type cible: skyfield.sgp4lib.EarthSatellite
        :return: Le rayon orbital calculé en mètres
        :rtype: float
        """
        rev_par_jour = cible.model.no_kozai / (2* math.pi) * 1440
        rad_par_sec = (rev_par_jour * 2 * math.pi) / 86400
        demi_major_axis = (self.GM / rad_par_sec**2) ** (1/3)
        return demi_major_axis
        
    def orbit_transfer(self,r1, r2):
        """
        Calcule un transfert de Hohmann entre deux orbites circulaires r1 (orbite actuelle)
       :param r1: Rayon de l'orbite initiale en mètres
        :type r1: float
        :param r2: Rayon de l'orbite cible finale en mètres
        :type r2: float
        :return: Un dictionnaire contenant les composants du transfert :
            - 'dv1_m_s': Premier delta-V (m/s)
            - 'dv2_m_s': Second delta-V avec inclinaison potentielle (m/s)
            - 'total_dv_m_s': Delta-V total cumulé (m/s)
            - 'transfer_time_s': Durée totale du transfert en secondes
        :rtype: dict
        """

        v1 = math.sqrt(self.GM / r1)
        v2 = math.sqrt(self.GM / r2)

        # Demi-grand axe de l'ellipse de transfert
        a_t = (r1 + r2) / 2.0

        # Vitesse au périgée et à l'apogée de l'ellipse de transfert
        v_pg = math.sqrt(self.GM * (2 / r1 - 1 / a_t))
        v_ag = math.sqrt(self.GM * (2 / r2 - 1 / a_t))

        dv1 = abs(v_pg - v1)

        if self.inclinaison != 0.0:
            dv2 = math.sqrt(v_ag**2 + v2**2 - 2 * v_ag * v2 * math.cos(self.inclinaison))
        else:
            dv2 = abs(v2 - v_ag)

        # Temps de transfert = la moitié de la période de l'ellipse
        transfer_time = math.pi * math.sqrt(a_t ** 3 / self.GM)

        return {
            'Poussee d évitemment (m/s)': dv1,
            'Pousse de re-circularisation (m/s)': dv2,
            'total delta de vitesse (m/s)': dv1 + dv2,
            'Temps de transfert (s)': transfer_time,
        }

    def evasive_maneuvre(self):
        """
        Calcule la manœuvre d'évitement (delta-v + temps de transfert) nécessaire pour déplacer
        «satellite» de altitude_evasion_km, en se basant sur le DataFrame d'alerte produit
        par detecter_collisions().
        :return: Une liste de dictionnaires, où chaque élément associe les données de la collision (débris, heure, distance) aux paramètres physiques de la manœuvre calculée.
        :rtype: list[dict]
        """
        if self.df_collision.empty:
            print("Aucune collision prévue, maintien de l'orbite")
            return []
        
        satellites_starlink = charger_donnees_tle('donnees_tle/starlink.txt')
        cible = next((s for s in satellites_starlink if s.name == self.satellite_name), None)

        r1 = self.orbital_radius(cible)

        delta_r = self.altitude_evasion * 1000.0  # km -> m
        r2 = r1 + delta_r if self.eleve_orbit else r1 - delta_r

        transfer = self.orbit_transfer(r1, r2)

        manoeuvres = []
        for _, row in self.df_collision.iterrows():
            manoeuvres.append({
                'Débris': row['Débris'],
                "Heure d'impact": row["Heure d'impact"],
                'Distance Min (km)': row['Distance Min (km)'],
                'rayon inital (km)': float(f"{(r1/1000):.3f}"),
                'rayon final (km)': float(f"{(r2/1000):.3f}"),
                **transfer,
            })

        return manoeuvres