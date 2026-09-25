# POLOP V3 — plan-séquence web interactif (15 s)

La V3 conserve **le même dossier, la même URL** et le décor Three.js de la V1. Référence : `Script_POLOP.md`, A0 puis début A1. Elle suit l'anneau dans la rivière, remonte à la surface, découvre la vallée et la montagne, puis rejoint Thomas, Éva et Léa. Le portail et un personnage nommé « Polop » ne figurant pas dans cette ouverture, ils ne sont pas ajoutés.

| Temps | Cadrage du plan continu |
|---|---|
| 0–3 s | Sous l'eau, anneau et sortie de la rivière. |
| 3–7,5 s | Vue de la vallée et montagne. |
| 7,5–11 s | Approche du relief et du sentier. |
| 11–15 s | Caméra sur la famille en marche et rapprochement. |

La caméra utilise une interpolation cubique à vitesse continue aux repères, évitant les micro-arrêts de la V2. La transition sous l’eau/air agit sur la brume, la lumière et l’exposition, tandis que particules et surface de rivière bougent réellement en 3D. Les trois silhouettes provisoires marchent et bougent la tête ; Éva ralentit à la fin devant le paysage tandis que Thomas et Léa poursuivent leur marche. Toutes leurs positions sont recalculées à partir du temps absolu pour garder le même état au retour arrière. Ce rendu web ne remplace pas `Unreal/previz_polop.py` et ne valide ni la géographie ni la physique finales.

## Commandes

Lire/pause, recommencer, vitesse, chronologie dans les deux sens, vue libre, plein écran et son d’ambiance activable. L’ambiance est synthétisée localement via Web Audio (eau et vent), sans utiliser de pistes musicales externes ; elle est désactivée par défaut et se coupe à la pause. En vue libre : souris ou doigt pour tourner, pincement ou molette pour zoomer. Raccourcis hors champs : Espace, R, V, F. La préférence système de réduction du mouvement démarre la lecture en pause.

## Modèles optionnels

Aucun GLB, GLTF ou VRM n'est présent dans le dépôt. La carte `CHARACTER_ASSETS` de `app.js` peut recevoir `Thomas: { url: "./assets/thomas.glb", scale: 1 }` après ajout du fichier sous `docs/demo-web/assets/`. Le GLTFLoader n'est chargé qu'en présence d'un modèle configuré ; le personnage procédural reste visible si le téléchargement échoue. Les clips contenant « walk »/« marche » et « idle »/« rest »/« repos » sont reconnus. Adapter l'échelle, l'orientation et le rig selon le modèle. **VRM nécessite un adaptateur spécifique et n'est pas encore pris en charge.**

## Déploiement et limites

La source GitHub Pages reste `main` + `/docs`, URL : `https://rafa-create.github.io/Polop/demo-web/`. Le workflow Actions existant sert uniquement à synchroniser le script vers Drive, pas à déployer Pages. Il faut un navigateur WebGL et un accès Internet au CDN jsDelivr pour Three.js. Test local via `python -m http.server 8000 --directory docs`, puis `http://localhost:8000/demo-web/`. Les tests réellement exécutés et les limites de vérification doivent être distingués de l'inspection statique. Le rendu et le mixage ne remplacent pas une revue artistique et sonore en conditions de projection.
