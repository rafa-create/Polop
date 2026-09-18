---
labels: [wait_codex]
status: waiting
priority: P0
---

# Bootstrap Unreal totalement reproductible

## But

Permettre :

`git clone → ouvrir projet → lancer previz_polop.py`

sur un ordinateur neuf, sans ancienne copie locale de POLOP.

## Travail attendu

- créer/versionner `Polop.uproject` ;
- activer explicitement Python Editor Script Plugin et Sequencer Scripting ;
- versionner les `Config/Default*.ini` nécessaires ;
- choisir une stratégie pour `/Game/Main` :
  - **option A privilégiée** : petite `Main.umap` minimale versionnée avec la coquille Landscape 1009×1009 ;
  - option B : création fiable de la coquille Landscape par Python depuis un projet vide ;
- faire échouer proprement le générateur si le bootstrap est incomplet ;
- documenter la version UE testée.

## Contraintes

- `/Game/Main` doit rester source et ne pas être modifiée par un run ;
- les maps/runs générés ne doivent pas être versionnés ;
- si `.umap` / `.uasset` sont ajoutés, utiliser Git LFS ;
- aucune dépendance à un chemin absolu local.

## Validation

Sur une deuxième machine :

1. clone frais ;
2. aucune copie d'un ancien projet POLOP ;
3. ouverture du projet ;
4. run complet ;
5. rapport sans blocage de bootstrap ;
6. map `Previz_<run_id>` et séquence omnisciente présentes.

## Preuve à conserver

Ajouter au repo un compte rendu avec :
- commit testé ;
- UE version ;
- OS ;
- run_id ;
- résultat ;
- problèmes éventuels.
