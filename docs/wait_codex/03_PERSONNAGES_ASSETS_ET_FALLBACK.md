---
labels: [wait_codex]
status: waiting
priority: P1
---

# Personnages — assets et fallback reproductible

## Problème

Les personnages articulés récents chargent des assets tutoriels internes Unreal :

`/Engine/Tutorial/SubEditors/TutorialAssets/Character/`

Ils peuvent ne pas être disponibles dans une autre installation.

## Travail attendu

- détecter explicitement la présence de `TutorialTPP`, `Tutorial_Walk_Fwd`, `Tutorial_Idle` ;
- si présents : utiliser le cast articulé ;
- si absents : fallback automatique vers les proxies simples validés ;
- rapporter dans le manifest quel mode est utilisé ;
- ne jamais interrompre la validation spatiale uniquement parce que les assets de jeu manquent ;
- si on décide d'utiliser des assets propres au projet, les versionner correctement/LFS.

## Performance

Mesurer aussi :
- nombre de sections d'animation ;
- temps de génération ;
- taille de la Level Sequence ;
- coût du sampling image par image.

## Validation

Deux tests :
1. installation avec assets tutoriels ;
2. installation où ils sont volontairement indisponibles.

Les deux doivent produire un run exploitable.
