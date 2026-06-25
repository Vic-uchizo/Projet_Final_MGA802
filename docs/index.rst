Documentation de ``debris_orbites``
===================================

Projet final **MGA802** — Visualisation 3D et détection de collisions entre
satellites et débris en orbite basse (LEO).

Le package ``debris_orbites`` regroupe toute la logique métier du projet :

- le **moteur de calculs orbitaux** (chargement des TLE, positions, trajectoires
  et détection de collisions) ;
- le calcul des **manœuvres d'évitement** ;
- le **téléchargement** des données brutes depuis CelesTrak.

Installation
------------

.. code-block:: bash

   pip install -e .          # le package
   pip install -e ".[docs]"  # + les outils de documentation

Lancement
---------

.. code-block:: bash

   python main.py            # menu : 1) télécharger les données  2) lancer l'interface 3D

Référence de l'API
------------------

.. toctree::
   :maxdepth: 2
   :caption: Package debris_orbites

   api/orbit
   api/maneuver
   api/donnees

.. toctree::
   :maxdepth: 2
   :caption: Scripts d'entrée

   api/main
   api/visualisation

Index
-----

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
