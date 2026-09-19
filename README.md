# LA BOUCLE / POLOP

## Source canonique

La bible narrative absolue est **`Script_POLOP.md`**.

Les anciennes versions dans `archive/` sont historiques uniquement.

## Prévisualisation Unreal

Point d'entrée unique :

`Unreal/previz_polop.py`

Documentation :

- `Unreal/README_PREVIZ.md`
- `docs/ENVIRONNEMENT_REPRODUCTIBILITE.md`
- `pland_route.md`

## État de reproductibilité

Le dépôt contient le générateur et la logique de simulation, mais il manque encore le bootstrap Unreal complet (`.uproject` + `/Game/Main` minimal ou création automatique du Landscape). Voir :

GitHub issue **#41** (`3d_codex`)

## Travaux en attente de Codex / Unreal

Toutes les tâches qui demandent du code Unreal ou une exécution réelle sont suivies dans les **GitHub Issues** avec le label **`3d_codex`**. Les issues principales ouvertes sont #41, #42, #44, #45, #46 et #47. #43 est fusionnée dans #41.

## Règle de travail

Séparer toujours :

- **vérité du monde** : géographie, temps objectif, causalité, états physiques ;
- **mise en scène** : caméra, rythme, focale, occultation, lumière, son.

La caméra peut cacher une information narrative, jamais un bug physique.
