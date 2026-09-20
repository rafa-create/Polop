# Grotte : audit géographique avant reprise caméra — 20/09/2026

Référence du code : `9fe0c06b4a51945343d250c3b2ccc4661a17682b`.
Autorité narrative : `Script_POLOP.md`, A10–A17 et B1.
Terrain et routes : exports du run local `20260920_085219_299235`, lancé avec
UE 5.8.2 depuis le clone officiel. Le SHA-256 annoncé au lancement correspond
à cette version du générateur. La génération est encore en cours selon
l’utilisateur ; elle n’est pas déclarée terminée ou validée dans cette fiche.

## Méthode et limites

Évaluation hors Unreal des fonctions de trajectoire du générateur, avec le
heightmap 1009 × 1009 et les routes exportés par ce run. Les positions utilisent
la conversion du Landscape du projet (pas un sol plat). Lecture des volumes
de galerie et des fonctions de caméra. Aucune modification de scène, de
terrain, d’animation, de sous-titre, d’ombre ou du contact à 18 h.

L’accès à la fenêtre Unreal a dépassé son délai pendant la génération.
Les constats ci-dessous sont des mesures du modèle et une comparaison à la
Bible, **pas une inspection du nouveau rendu ni un test de collision moteur**.

## Constats

| Élément | Mesure ou comportement actuel | Conséquence à vérifier/corriger |
| --- | --- | --- |
| Zone d’attente | Les femmes restent sur A, environ 8 m avant la jonction haute. Leurs recherches rejoignent la petite poche, côté ouest de l’éperon. | Conserver dans le même cadre les femmes, l’accès surveillé et la poche ; Thomas doit disparaître derrière le relief, sans révélation de l’entrée. |
| Détour extérieur de Thomas | Environ 24 m de parcours entre la jonction et l’entrée, avec un crochet côté précipice. | La Bible décrit quelques mètres et un petit espace. Cette ampleur de blockout mérite d’être évaluée avant de rallonger le mouvement caméra. Aucun redimensionnement décidé ici. |
| Repère du précipice | Plateforme à Z ≈158 m ; `PRECIPICE_EDGE_POINT` à Z ≈130,37 m, soit 27,63 m plus bas. | Le repère est déjà dans la pente, pas sur la lèvre haute. Le mélange utilisé comme cible caméra tire le regard vers le bas. Le petit volume `SEARCH_LEDGE_LIP` utilise également ce point bas. |
| Recherche A12–A14 | La cible finale mélange 40 % du repère bas du précipice et 60 % de `CAVE_ZONE_POINT`, sans inclure les positions des femmes. | Cela concorde avec leur perte de présence signalée par l’utilisateur. Construire un plan de situation incluant les femmes, puis le vide, au lieu de viser la pente seule. |
| Première cavité et galerie B | Entrée → contact ≈10 m ; parcours total jusqu’à B ≈60,17 m en 3D. Le contact est à Z ≈160,14 m, le coude à ≈149,60 m, le second faisceau à ≈158,14 m. | Le premier tronçon descend de 10,54 m pour 8 m horizontaux, puis remonte. Ce profil explique un risque de déplacement fastidieux et de caméra plongeante ; la Bible décrit une progression à pied dans une cavité, pas cet accident de terrain. |
| Construction de la galerie | Murs et plafonds sont des boîtes horizontales placées à la hauteur moyenne des extrémités de chaque segment. | Sur le premier segment, la face inférieure du plafond est à environ Z 157,95 m, sous le niveau des pieds au contact (160,14 m). Les volumes ne suivent donc pas les hauteurs du trajet. Vérifier aussi les raccords aux coudes avant de régler la caméra. |
| Silhouette dans B1 | B1 couvre les minutes objectives 62 → 60,2. Thomas normal recule du contact vers l’entrée mais reste au minimum à 2,37 m de celle-ci. Il n’atteint l’entrée qu’à la minute 54. | La silhouette sortant par A, exigée en B1, n’est pas produite dans cette fenêtre. Ce n’est pas réparable par un simple panoramique. Ne pas inventer une deuxième trajectoire ou déplacer un double pour simuler la sortie. |
| Raccord extérieur B | La sortie passe par un point de dégagement puis rejoint une station intérieure du chemin B, distincte de sa station 0 au sommet. | Préserver ce raccord. L’utilisateur juge déjà cette partie plus lisible ; éviter une refonte de la sortie extérieure sans preuve supplémentaire. |

## Ordre de correction proposé

1. **Géographie verticale** : définir une vraie lèvre haute comme repère de
   recherche et une galerie praticable dont sol, murs et plafond suivent le
   même profil. Préserver la séparation visuelle des ouvertures A/B et les
   coordonnées/instant du contact à 18 h. Ne pas déplacer seulement le
   personnage au-dessus du terrain ou cacher l’écart avec la caméra.
2. **Chronologie de la silhouette** : réconcilier les trajectoires objectives
   avec la sortie par A en B1. Toute solution doit être cohérente dans les
   deux lectures et préserver un seul contact à 18 h. La fiche ne choisit pas
   encore un nouveau timing : ce point exige un examen de la continuité de
   l’ensemble A15–B2, pas un déplacement isolé de Thomas normal.
3. **Cadrage de situation** : attente avec l’unique retour visible, recherche
   avec les deux femmes dans la poche, regard vers le chemin puis le vide.
   Le resserrement des dialogues doit rester assez modéré ici pour conserver
   ces repères pendant les questions courtes.
4. **Révélation A15** : suivre brièvement le départ des femmes, puis adopter
   l’angle inédit autour de l’éperon, retrouver Thomas à quelques pas de
   l’entrée. Régler le trajet après validation des volumes, sans traverser
   un rocher ni montrer trop tôt la seconde ouverture.

## Preuves à obtenir après génération

Revoir attente/recherche avec les femmes visibles et sans carton explicatif ;
revoir A15 en mouvement, puis B1 avec les deux occurrences de Thomas et les
deux accès. Vérifier à hauteur humaine les murs, plafonds et appuis dans le
coude. Un spectateur doit comprendre la disparition, la zone fouillée et le
changement d’accès sans qu’on lui explique l’origine du phénomène.

La présence d’un run terminé et de contrôles verts ne suffira pas à fermer
cette revue. Aucun nouveau dialogue explicatif n’est proposé.
