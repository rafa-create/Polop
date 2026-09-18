# POLOP — Unreal Previz

## Source de vérité

La **bible narrative absolue** du projet est `Script_POLOP.md`.

Les anciennes versions de scénario conservées dans `archive/` sont historiques uniquement. Elles ne peuvent pas corriger silencieusement `Script_POLOP.md`.

## Script Unreal actif unique

Lancer uniquement :

`Unreal/previz_polop.py`

Tous les anciens scripts individuels restent dans `Unreal/old/` pour historique et diagnostic. Ils ne font plus partie du workflow normal.

## Master V10

V10 conserve les corrections de terrain introduites par Codex et ajoute une isolation complète des runs.

Le script :

- exige que le niveau source `/Game/Main` soit enregistré avant exécution ;
- duplique `/Game/Main` dans une nouvelle map de travail ;
- ne modifie pas directement la map source ;
- génère le relief V11 et vérifie le transport du heightmap 16 bits avant import ;
- mesure l'origine réelle du Landscape au lieu de supposer arbitrairement son pivot ;
- attend que les couches/collisions Landscape soient réellement disponibles ;
- exécute le WORLD GATE avant l'animation ;
- génère ensuite l'animation objective de préviz, les POV et les validations ;
- journalise les étapes et les positions narratives importantes.

## Isolation d'un run

Chaque lancement reçoit un `RUN_ID` unique.

### Content Browser

- `/Game/POLOP/Generated_V10/Maps/Previz_<run_id>`
- `/Game/POLOP/Generated_V10/Runs/<run_id>/...`

### Saved

- `Saved/POLOP/Runs/<run_id>/keylog.jsonl`
- `Saved/POLOP/Runs/<run_id>/V11/polop_v11_heightmap_1009.png`
- `Saved/POLOP/Runs/<run_id>/V11/route_model_v11.json`
- `Saved/POLOP/Runs/<run_id>/ANIMATION_V05/...`
- `Saved/POLOP/Runs/<run_id>/MASTER_V10/report_previz_v10.html`
- `Saved/POLOP/Runs/<run_id>/MASTER_V10/report_previz_v10.txt`
- `Saved/POLOP/Runs/<run_id>/MASTER_V10/report_previz_v10.json`

Un run ne doit donc plus écraser le heightmap, la validation ou le rapport d'un autre run.

Le nettoyage automatique est désactivé par défaut (`CLEANUP_OLD_RUNS = False`) pour conserver les essais et leurs preuves. Son activation explicite conserve les **12 derniers runs Saved** et les **8 derniers runs Content V10**. Il ne vise pas `/Game/Main` ni les sources.

## Rapport de cohérence

Le rapport HTML est la lecture la plus rapide.

Le WORLD GATE contrôle notamment :

- Landscape présent et transform cohérent ;
- composants Landscape présents ;
- emprise XY et relief vertical plausibles ;
- routes A/B/HAUT/GROTTE/FLANC à l'intérieur du terrain ;
- zone grotte dans l'emprise montagne ;
- hauteurs réelles du Landscape sur plusieurs points narratifs ;
- validation Animation V05 ;
- autorité unique des caméras `PZ_ANIM_*`.

Si le rapport contient un `FAIL` bloquant, ne pas perdre de temps à valider les POV visuellement.

## Statut narratif de la préviz

La préviz actuelle reste un **blockout technique de la boucle montagne + timeline objective compressée**.

Le nouveau plan canonique d'ouverture **rivière → vallée → montagne → famille** présent dans `Script_POLOP.md` est accepté narrativement mais n'est pas encore construit dans la préviz de 65 secondes. L'anneau complet, certains effets environnementaux inversés et le montage cinématographique final restent également des étapes ultérieures.

## Exécution

Dans Unreal Engine 5.8 :

1. enregistrer `/Game/Main` ;
2. `Tools > Execute Python Script` ;
3. choisir `Unreal/previz_polop.py` ;
4. attendre la fin de la reconstruction Landscape ;
5. ouvrir le rapport HTML du `RUN_ID` courant ;
6. seulement si le rapport est cohérent, inspecter la map `Previz_<run_id>` et les POV.



## Corrections vérifiées le 18 septembre 2026

- Le canal R du RenderTarget transporte des valeurs entières 0–65535, comme l'exige l'import UE 5.8, et non des valeurs normalisées 0–1. Quatre pixels sont relus avant import et comparés au PNG 16 bits.
- L'origine du terrain est mesurée à partir de ses composants ; elle n'est pas supposée au centre.
- Les résultats des traces Python se lisent avec `HitResult.to_tuple()` ; `GameplayStatics.break_hit_result` n'est pas exposé dans l'installation testée.
- La couche d'édition cible est rendue visible et son poids réglé à 1 dans la copie de travail. Une couche masquée acceptait l'import sans produire de relief visible.
- Le premier événement du journal contient le SHA-256 du fichier exécuté. Comparer ce hash en cas de résultat différent entre machines.

Ces quatre corrections ont permis au run local V09 du 18 septembre de terminer sans échec technique. Elles ont été fusionnées dans la V10 distante (commit `48d2675`). Cela ne constitue pas encore une validation complète du scénario ou des quatre POV.

## Reprise sur un autre ordinateur — prérequis actuels

1. Récupérer **la version courante** de `Unreal/previz_polop.py` sur `main`, plutôt qu'une ancienne copie téléchargée.
2. Utiliser Unreal Engine **5.8** (essai local : 5.8.2), avec **Python Editor Script Plugin** et **Sequencer Scripting** activés ; redémarrer l'éditeur après activation.
3. Ouvrir un projet Unreal et disposer actuellement d'une carte **/Game/Main** avec un seul Landscape **1009 × 1009 sommets** : 63 quads par section, 1 section par composant, 16 × 16 composants. Enregistrer cette carte. Le générateur normalise ensuite son échelle et son emplacement.
4. Exécuter le fichier **dans l'éditeur Unreal**, via Outils / Tools > Execute Python Script. Un interpréteur Python en ligne ou GitHub seul ne fournit pas le module `unreal`.
5. Attendre l'événement `complete` dans `Saved/POLOP/Runs/<run_id>/keylog.jsonl`. En cas de `failed`, lire ce journal et le rapport du même run.
6. Ouvrir la carte générée et sa séquence dans le dossier Content correspondant au même `run_id`.

**Limite actuelle : le .py ne crée pas encore la coquille Landscape à partir d'un projet vide.** La préparation de la carte décrite ci-dessus reste nécessaire.

## Ordre de contrôle demandé

Thomas normal → Léa → Éva → Thomas inversé. Contrôler A1/A2 (pont et détour), A10–A15 (attente, recherche, grotte), A17 (18h00), puis B1–B9 dans le sens 18h00 → 17h00. Une lecture objective de 16h58 → 18h00 ne suffit pas à valider le parcours vécu par Thomas inversé.
