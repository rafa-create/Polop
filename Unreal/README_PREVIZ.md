# POLOP — Unreal Previz

## Scripts actifs

Pour éviter toute ambiguïté, seuls ces scripts à la racine de `Unreal/` sont considérés comme actifs :

- `previz_polop_complet_v11.py` — géographie / Landscape de référence.
- `previz_polop_validation_v11.py` — validation de la géographie V11.
- `previz_polop_animation_v05.py` — animation, POV et validation visuelle actuelle.

Les anciennes versions sont archivées dans `Unreal/old/`. Elles servent uniquement d'historique et ne doivent plus être exécutées sauf besoin de comparaison.

## V05 — objectif immédiat

V05 reprend la simulation précédente sans modifier la logique A/B/pont/flanc déjà validée. Elle concentre les corrections sur la lisibilité de la caverne finale :

- corridor de contrôle dégagé dans la cavité ;
- POV Thomas normal / inversé décalés pour éviter d'entrer dans les proxies ;
- caméras `FINAL_CAVE_MASTER`, `CAVE_BACKLIGHT_REVIEW` et `CAVE_TOP_DEBUG` ;
- plage Sequencer cadrée sur 0–65 s ;
- 62 s = 18h00 narratif ; 62–65 s = queue technique de vérification uniquement ;
- validation automatique intégrée au script.

### Contrôle recommandé

Après exécution de `previz_polop_animation_v05.py`, vérifier prioritairement :

- 60 s et 61 s : coexistence lisible dans la cavité ;
- 62 s : contact / convergence ;
- 62–65 s : POV Thomas normal sans collision caméra ;
- `PZ_ANIM_CAM_CAVE_BACKLIGHT_REVIEW` : lecture vers l'entrée ;
- `PZ_ANIM_CAM_CAVE_TOP_DEBUG` : diagnostic si une paroi bloque encore une vue.

## Exécution

Dans Unreal, utiliser la console Python / Output Log et lancer la copie locale du script voulu, par exemple :

`py "CHEMIN_COMPLET/previz_polop_animation_v05.py"`

La préviz reste un outil de validation spatiale et narrative, pas une proposition de décor final.
