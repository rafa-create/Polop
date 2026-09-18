# Environnement reproductible — POLOP

## État actuel

Le dépôt contient la bible narrative, les documents, le générateur Unreal et ses validations. Il **ne contient pas encore un projet Unreal complet bootstrapable depuis zéro**.

Aujourd'hui, un autre ordinateur doit disposer au minimum de :

- Unreal Engine **5.8.x** ; le test local documenté a été fait avec 5.8.2 ;
- Python Editor Script Plugin activé ;
- Sequencer Scripting activé ;
- une carte `/Game/Main` enregistrée ;
- un Landscape source 1009 × 1009 sommets, 63 quads/section, 1 section/composant, 16 × 16 composants.

Le générateur normalise ensuite le terrain et crée les runs de travail.

## Ce qui est déjà versionné

- `Script_POLOP.md` : bible narrative absolue ;
- `Unreal/previz_polop.py` : point d'entrée unique ;
- `Unreal/README_PREVIZ.md` : exécution / limites ;
- roadmap et documents narratifs ;
- anciens scripts dans `Unreal/old/` pour historique.

## Ce qui manque encore pour « clone and run »

- un `.uproject` versionné ;
- les `Config/Default*.ini` nécessaires ;
- un bootstrap de `/Game/Main` ;
- soit une petite map `Main.umap` versionnée avec la coquille Landscape,
  soit une création fiable de cette coquille par script ;
- une vérification automatique des plugins au démarrage.

Ces éléments sont décrits dans `docs/wait_codex/01_BOOTSTRAP_UNREAL_REPRODUCTIBLE.md`.

## Assets Engine utilisés

Le code récent peut utiliser les assets tutoriels Unreal :

`/Engine/Tutorial/SubEditors/TutorialAssets/Character/`

- `TutorialTPP`
- `Tutorial_Walk_Fwd`
- `Tutorial_Idle`

Ce ne sont pas des fichiers du dépôt. Le pipeline doit donc soit garantir leur présence, soit avoir un fallback. Voir `docs/wait_codex/03_PERSONNAGES_ASSETS_ET_FALLBACK.md`.

## Fichiers générés

Chaque run écrit localement dans :

`Saved/POLOP/Runs/<run_id>/...`

et crée des assets de travail sous :

`/Game/POLOP/Generated_V10/...`

Le dossier `Saved/` ne doit pas être commité.

## Git LFS

Le fichier `.gitattributes` prépare Git LFS pour les formats binaires Unreal et médias. Si un `.umap` ou `.uasset` est ajouté, Git LFS doit être installé sur les machines qui clonent le dépôt.

## Test de reproductibilité attendu

Quand le bootstrap sera terminé :

1. cloner le dépôt ;
2. installer/ouvrir UE 5.8.x ;
3. ouvrir `Polop.uproject` ;
4. lancer `Unreal/previz_polop.py` ;
5. attendre l'événement `complete` ;
6. ouvrir le rapport du `RUN_ID` ;
7. ouvrir la map générée et la séquence omnisciente.

Aucune étape de placement manuel ne devrait être nécessaire.
