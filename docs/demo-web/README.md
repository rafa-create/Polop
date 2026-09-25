# POLOP V4 — film 3D interactif de 5 minutes

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

L'horloge narrative (16 h 58 → 18 h 00 → 17 h 00) et la durée de lecture de 5 minutes sont **deux échelles différentes** : cette adaptation pratique des ellipses. La même trajectoire normale des personnages est réévaluée en temps objectif pendant le parcours inversé ; un second Thomas visible utilise un objet 3D distinct, sans détruire ni cacher artificiellement l'occurrence normale. Les deux lectures de la collision se déroulent à la même zone du décor. Les détails d'appui des corps, les collisions physiques, l'entropie exacte du mousqueton, le trajet de l'anneau et les raccords géographiques ne sont **pas encore vérifiés dans Unreal**. Les ouvertures de la grotte et le sentier final sont des **blockouts provisoires** et ne doivent pas servir de preuve de cohérence causale du film. Le final dévoile seulement alors la continuité du sentier et les deux ouvertures.

## Lire et explorer

Lecture/pause, reprise, chronologie `00:00–05:00` dans les deux sens, neuf chapitres de navigation, vitesse ×0,5 / ×1 / ×1,5, caméra libre (glisser/pincer), plein écran, ambiance eau/vent synthétique et optionnelle. Les textes incrustés résument les passages : il n'y a **ni dialogues enregistrés ni mixage sonore final**. Tous les éléments animés sont pilotés par le temps de lecture : retour arrière et recherche aléatoire retrouvent le même état.

Sur ordinateur ou téléphone, ouvrir `https://rafa-create.github.io/Polop/demo-web/`. Les fichiers restent dans `docs/demo-web/`, publié par GitHub Pages depuis `main` et `/docs`. La scène requiert WebGL, un navigateur moderne et un accès au CDN jsDelivr pour Three.js. Pour un essai local : `python -m http.server 8000 --directory docs`, puis `http://localhost:8000/demo-web/`.

## Architecture / tests / limites

- `index.html`, `style.css` : interface de lecture et textes de scène.
- `storyboard.js` : minutage, chapitres, textes et découpage vérifiables sans WebGL.
- `app.js` : décor 3D de V3 conservé, nouvelle mise en scène, deux occurrences de Thomas, cavité, animation du pont et mouvements inversés.
- `tests/demo-web-smoke.mjs` et `tests/demo-web-story.mjs` : respectivement tests réels Chromium/WebGL et contrôle de la chronologie narrative.
- `Unreal/previz_polop.py`, `Script_POLOP.md` et `docs/BIBLE_EXPLICATIVE_POLOP.md` sont inchangés.

L'application génère encore des silhouettes procédurales : aucun modèle final GLB/GLTF/VRM n'était versionné lors de l'intégration. Le remplacement facultatif GLB/GLTF déjà amorcé dans V2 reste à adapter aux modèles fournis ; VRM demande un rig/moteur dédié. Cette version **couvre l'arc scénaristique**, mais ne contient pas tous les plans, dialogues, personnages articulés et effets validés scène par scène. La continuité parfaite du plan-séquence et la justesse du déterminisme nécessitent des validations visuelles et physiques supplémentaires avec les assets du film. Le workflow GitHub Pages et les tests automatisés ne valident pas à eux seuls la qualité artistique ni les contraintes du projet Unreal.
