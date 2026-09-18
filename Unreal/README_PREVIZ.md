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

Après un run réussi, le master conserve automatiquement les **12 derniers runs Saved** et les **8 derniers runs Content V10**. Le nettoyage ne touche jamais `/Game/Main`, `Script_POLOP.md`, `archive/` ou les sources du projet.

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

