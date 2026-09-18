---
labels: [wait_codex]
status: waiting
priority: P1
---

# Modulariser le générateur sans perdre le point d'entrée unique

## Problème

`Unreal/previz_polop.py` concentre terrain, animation, personnages, caméra, validation, review et captures. Le fichier est devenu difficile à modifier sans régression.

## Cible

Conserver :

`Unreal/previz_polop.py`

comme **seul script à lancer**, mais déplacer le code interne vers des modules source versionnés, par exemple :

- `Unreal/polop/geography.py`
- `Unreal/polop/timeline.py`
- `Unreal/polop/characters.py`
- `Unreal/polop/camera.py`
- `Unreal/polop/validation.py`
- `Unreal/polop/review.py`

## Contraintes

- même résultat déterministe ;
- même run_id ;
- mêmes rapports ;
- aucun retour à plusieurs scripts manuels ;
- ne pas casser le fonctionnement via Tools > Execute Python Script ;
- ajouter une version/schema du modèle partagé entre modules.

## Validation

Comparer avant/après sur le même scénario :
- positions clés ;
- trajectoires ;
- report checks ;
- nombre de caméras ;
- séquence omnisciente ;
- hashes/manifeste lorsque pertinent.
