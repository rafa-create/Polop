# POLOP — Unreal Previz

## V01 — Blockout géographique

Le script `previz_blockout_v01.py` construit dans le niveau actuellement ouvert :

- chemin A — montée normale de Thomas, Éva et Léa ;
- chemin B — descente de Thomas inversé ;
- pont A ↔ B ;
- chemin du flanc A ↔ B ;
- zone de la grotte ;
- relief séparant A et B ;
- point de convergence de 17h00 ;
- quatre proxies de personnages ;
- une Cine Camera d'ensemble ;
- une Level Sequence vide de 10 secondes à 24 fps.

### Sécurité

Le script ne supprime que les Actors dont le label commence par `PZ_`.
Il peut donc être relancé après chaque modification topologique.

### Exécution dans Unreal Engine 5.8

1. Ouvrir le projet `polop`.
2. Ouvrir le niveau dans lequel créer la préviz.
3. Ouvrir **Window > Output Log**.
4. Dans la barre de commande de l'Output Log, choisir le mode **Python** si nécessaire.
5. Exécuter le fichier depuis une copie locale avec :
   `py "CHEMIN_COMPLET/previz_blockout_v01.py"`
6. Vérifier dans le World Outliner le dossier `POLOP_PREVIZ`.
7. Sélectionner `PZ_CAM_OVERVIEW_GEOGRAPHIE` et utiliser **Pilot** pour voir la maquette depuis la caméra.

La géométrie V01 est un schéma spatial, pas une proposition de décor final. Les dimensions, pentes et distances sont des hypothèses de prévisualisation à corriger après lecture dans Unreal.
