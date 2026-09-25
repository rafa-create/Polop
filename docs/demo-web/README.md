# POLOP V4.2 — film 3D interactif de 5 minutes

Cette version **prolonge l'application web existante à la même URL** avec une lecture de **300 secondes (05:00)**. Elle n'est plus limitée aux 15 secondes de l'ouverture : `storyboard.js` adapte en **21 séquences condensées** les événements de `Script_POLOP.md` de **A0 à A17, puis B1 à B9**. Les textes affichés proviennent des situations et de courts dialogues du manuscrit. C'est une **prévisualisation 3D narrative**, pas un MP4 téléchargeable, un doublage des dialogues, ni le film achevé.

## Déroulé

| Temps de lecture | Extraits du film-manuscrit | Intention à l'écran |
| --- | --- | --- |
| 00:00–00:36 | A0 | Anneau sous l'eau ; caméra hors de la rivière, vallée et montagne. |
| 00:36–01:46 | A1–A9 | Marche en famille, Léa traverse le pont, détour, collision cachée par le rocher, montée. |
| 01:46–02:16 | A10–A14 | Thomas s'éloigne ; Éva et Léa le cherchent puis partent demander de l'aide. |
| 02:16–02:46 | A15–A16 | Découverte différée de la petite entrée ; anneau remontant dans la fissure. |
| 02:46–02:59 | A17 | Contact de Thomas et de l'anneau, inversion sans flash. |
| 02:59–04:19 | B1–B4 | Seconde ouverture, parcours inversé, famille à rebours, eau/graviers qui remontent. |
| 04:19–04:42 | B5–B6 | Pont décroché ; Thomas raccroche le mousqueton et traverse. |
| 04:42–04:55 | B7–B9 | Rencontre des deux occurrences, contacts simultanés, retour au même instant. |
| 04:55–05:00 | B9 | Dézoom final de la boucle, puis noir. |

L'horloge narrative (16 h 58 → 18 h 00 → 17 h 00) et la durée de lecture de 5 minutes sont **deux échelles différentes** : cette adaptation pratique des ellipses. Les personnages partagent désormais des trajectoires et des animations réellement communes entre A et B ; le second Thomas utilise un objet 3D distinct évalué au même instant objectif, sans supprimer artificiellement l'occurrence normale. Les deux lectures de la collision se déroulent à la même zone du décor. Les détails d'appui des corps, les collisions physiques, l'entropie exacte du mousqueton, le trajet de l'anneau et les raccords géographiques ne sont **pas encore vérifiés dans Unreal**. Les ouvertures de la grotte et le sentier final sont des **blockouts provisoires** et ne doivent pas servir de preuve de cohérence causale du film. Le final dévoile seulement alors la continuité du sentier et les deux ouvertures.

## Correction du pont et du détour (V4.1)

La première version de cinq minutes utilisait la hauteur **du fond du creux** pour positionner les pieds de Léa et de Thomas inversé : les personnages paraissaient tomber et la caméra du pont visait elle aussi sous le tablier. Désormais `bridge-geometry.js` définit une source commune pour le relief local, le dessus des planches, les deux paliers et le chemin de contournement. Léa traverse sur le tablier à 00:57–01:12, reprend le **détour distinct** ensuite, et Thomas inversé rejoint la rive éloignée, rattache le mousqueton **avant** de traverser le pont à rebours de 04:36 à 04:42. Éva et Thomas normal ne traversent pas pendant le premier passage de Léa. Les cadrages 00:57–01:12 et 04:19–04:42 regardent désormais le tablier, pas le fond de la gorge.

Les appuis sont calculés explicitement à partir de la surface empruntée et non par « aimantation » au pont lorsqu'un personnage circule sur le flanc ; un essai de placer quelqu'un hors du tablier lève une erreur. `tests/demo-web-bridge.mjs` échantillonne les deux parcours et `tests/demo-web-smoke.mjs` vérifie les appuis pendant les traversées dans Chromium/WebGL. Le décor reste une prévisualisation procédurale : cette correction ne certifie pas encore la géographie et la physique finale du film Unreal.

## Chronologie objective commune (V4.2)

`objective-timeline.js` devient l'unique source des positions, orientations et phases de marche de **Thomas normal, Éva, Léa et Thomas inversé**. Son temps objectif est **condensé pour la prévisualisation** : les nombres 81, 86 et 179 y représentent respectivement les événements vers 17 h 00 (collision), 17 h 01 (mousqueton) et 18 h 00 (contact dans la grotte). Ces nombres **ne représentent pas les secondes réelles de l'heure vécue**.

De 00:00 à 02:59 de lecture, l'horloge objective avance ; de 02:59 à 04:48, elle **recule strictement** ; de 04:48 à 05:00, le film réobserve la même collision puis les instants déjà vécus, et avance à nouveau. La famille n'a **aucune trajectoire ni animation spécialement inventée pour la partie B** : le moteur recalcule exactement ses poses normales au même instant objectif, mais dans l'ordre inverse. Les orientations restent celles des gestes normaux : en B, leurs pas, bras et positions sont donc réellement lus à reculons. Thomas inversé possède sa propre trajectoire indexée sur ce même temps objectif, présente aussi pendant la partie A dès qu'il existe physiquement ; il est orienté dans son propre sens de marche.

Le passage groupé après les retrouvailles (01:30–01:46 de lecture) emprunte maintenant le détour dessiné **pour les trois personnages** plutôt que de couper au travers du creux. La géométrie du creux a été légèrement resserrée et les appuis sont testés sur toute cette progression. À la convergence, les deux occurrences de Thomas occupent le même point au **même instant objectif** dans A2 et B8. Le mousqueton change d'état une seule fois au temps objectif 86 : dans la partie B, Thomas le raccroche vers 04:36–04:38 **avant** de traverser sur le tablier vers 04:38–04:42. Une caméra de B1/B2 se tourne brièvement vers la famille sur l'autre versant pour rendre son déplacement inverse visible.

Les tests unitaires vérifient l'ordre de l'horloge, les poses identiques A/B, la marche arrière, la collision, l'attache et la géométrie sur plusieurs centaines d'échantillons ; le test Chromium/WebGL compare aussi les **rotations des membres** pour des instants objectifs identiques. Ces garanties sont celles du modèle web condensé : il faudra toujours vérifier avec le script les horaires réels, toutes les occultations, la cavité traversante, les contacts et l'entropie des objets dans une prévisualisation de production avant de conclure à la parfaite cohérence physique du film.

## Lire et explorer

Lecture/pause, reprise, chronologie `00:00–05:00` dans les deux sens, neuf chapitres de navigation, vitesse ×0,5 / ×1 / ×1,5, caméra libre (glisser/pincer), plein écran, ambiance eau/vent synthétique et optionnelle. Les textes incrustés résument les passages : il n'y a **ni dialogues enregistrés ni mixage sonore final**. Tous les éléments animés sont pilotés par le temps de lecture : retour arrière et recherche aléatoire retrouvent le même état.

Sur ordinateur ou téléphone, ouvrir `https://rafa-create.github.io/Polop/demo-web/`. Les fichiers restent dans `docs/demo-web/`, publié par GitHub Pages depuis `main` et `/docs`. La scène requiert WebGL, un navigateur moderne et un accès au CDN jsDelivr pour Three.js. Pour un essai local : `python -m http.server 8000 --directory docs`, puis `http://localhost:8000/demo-web/`.

## Architecture / tests / limites

- `index.html`, `style.css` : interface de lecture et textes de scène.
- `storyboard.js` : minutage, chapitres, textes et découpage vérifiables sans WebGL.
- `objective-timeline.js` : horloge objective unique, trajectoires des quatre occurrences et état de l'attache.
- `app.js` : décor 3D de V3 conservé, nouvelle mise en scène, deux occurrences de Thomas, cavité, animation du pont et mouvements inversés.
- `tests/demo-web-smoke.mjs`, `tests/demo-web-story.mjs`, `tests/demo-web-bridge.mjs` et `tests/demo-web-objective.mjs` : tests Chromium/WebGL, minutage, appuis physiques et identité objective entre A/B.
- `Unreal/previz_polop.py`, `Script_POLOP.md` et `docs/BIBLE_EXPLICATIVE_POLOP.md` sont inchangés.

L'application génère encore des silhouettes procédurales : aucun modèle final GLB/GLTF/VRM n'était versionné lors de l'intégration. Le remplacement facultatif GLB/GLTF déjà amorcé dans V2 reste à adapter aux modèles fournis ; VRM demande un rig/moteur dédié. Cette version **couvre l'arc scénaristique**, mais ne contient pas tous les plans, dialogues, personnages articulés et effets validés scène par scène. La continuité parfaite du plan-séquence et la justesse du déterminisme nécessitent des validations visuelles et physiques supplémentaires avec les assets du film. Le workflow GitHub Pages et les tests automatisés ne valident pas à eux seuls la qualité artistique ni les contraintes du projet Unreal.
