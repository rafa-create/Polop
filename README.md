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

`docs/wait_codex/01_BOOTSTRAP_UNREAL_REPRODUCTIBLE.md`

## Travaux en attente de Codex / Unreal

Toutes les tâches qui demandent du code Unreal ou une exécution réelle sont regroupées sous :

`docs/wait_codex/`

Chaque fiche porte le label **wait_codex**.

## Règle de travail

Séparer toujours :

- **vérité du monde** : géographie, temps objectif, causalité, états physiques ;
- **mise en scène** : caméra, rythme, focale, occultation, lumière, son.

La caméra peut cacher une information narrative, jamais un bug physique.
