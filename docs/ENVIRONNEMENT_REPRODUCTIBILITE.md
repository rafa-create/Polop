# Environnement reproductible — POLOP

## Référence et niveau de preuve (19 septembre 2026)

- **Un seul dépôt officiel :** `https://github.com/rafa-create/Polop.git`, branche `main`. Consulter en premier `AGENTS.md` à la racine pour les consignes de Codex.
- **Projet à ouvrir :** `polop.uproject` (respecter la casse réelle, minuscules). Association de moteur `5.8`, essai effectué dans **Unreal Engine 5.8.2 / Windows**.
- **Script actif unique :** `Unreal/previz_polop.py`, à exécuter depuis Unreal, pas depuis Python système.
- **Carte source :** `Content/Main.umap` (`/Game/Main`), téléchargée par Git LFS ; base Landscape 1009 × 1009 sommets, 63 quads/section, une section/composant, 16 × 16 composants. Le script duplique cette carte puis normalise la copie de travail.

**Preuve obtenue :** depuis `E:/perso/polop/Polop-git`, ouverture UE 5.8.2 et run `20260919_084218_028677` ; carte générée et séquence omnisciente inspectées dans l'éditeur ; rapport MASTER V10 `OVERALL: OK`, 35 OK, 0 WARN, 0 FAIL, 0 BLOCKER ; validation animation V05 OK. Un **clone local séparé** a récupéré sur GitHub le `.uproject` et la map `Main.umap` de 3,9 Mo par Git LFS avec `git status` propre. **Aucun deuxième run dans ce clone et aucun test sur un deuxième PC** ; ne pas les présenter comme réalisés. Le jalon pratique #41 a été accepté sur cette base.

## Reprise sur le futur ordinateur

1. Installer **Unreal Engine 5.8.2** et **Git + Git LFS**, puis `git lfs install`. Le matériel doit prendre en charge les fonctions de rendu dont vous avez besoin ; sur l'ancien PC, le GPU Intel Iris Xe bascule vers D3D11/SM5, sans empêcher le run technique.
2. Cloner `https://github.com/rafa-create/Polop.git` dans le dossier souhaité : `git clone https://github.com/rafa-create/Polop.git` ; se placer **dans ce clone** et vérifier `git status -sb` et `git lfs ls-files`.
3. Ouvrir **`polop.uproject` à la racine du clone** dans UE 5.8.2. Le projet versionné active `PythonScriptPlugin` et `SequencerScripting`.
4. Charger `/Game/Main` si elle n'est pas chargée, sans ajouter ni déplacer manuellement de Landscape. Lancer via **Outils / Tools > Execute Python Script** le fichier `Unreal/previz_polop.py` **du même clone**.
5. Attendre la fin du run ; relever le `run_id`, vérifier le rapport `Saved/POLOP/Runs/<run_id>/MASTER_V10/report_previz_v10.txt`, puis inspecter la carte `Previz_<run_id>` et `LS_POLOP_OMNISCIENT` du même run. Un rapport technique vert ne suffit pas à valider la fidélité cinématographique.
6. Si le moteur ne reconnaît pas l'association `5.8`, choisir la version installée **5.8.2** sur cette machine sans inscrire de GUID ou de chemin local dans le `.uproject` versionné. Toute correction de portabilité doit être répercutée sur GitHub.

## Quels dossiers garder sur l'ancien PC ?

- **Dossier de travail officiel à conserver et synchroniser :** `E:/perso/polop/Polop-git/`, connecté à GitHub. Après un push vérifié, son contenu **versionné** peut être récupéré par clone sur le nouveau PC.
- **À conserver séparément comme sauvegarde non migrée :** `E:/perso/polop/polop/`, ancien projet Unreal avec Git local `master` sans remote et des animations/séquences WIP propres à ce dossier. Ce travail **n'est pas garanti sur GitHub**. Avant de quitter l'ancien PC, sauvegarder/transférer le dossier ancien ou inventorier et transférer les assets irremplaçables ; ne pas `git reset`, `git clean`, écraser, supprimer ni copier tout ce dossier dans le dépôt officiel.
- `E:/perso/polop/Polop-test-clone/` ne servait qu'au contrôle de téléchargement : **facultatif après vérification de son absence de travail inédit**, il n'est ni le dossier à maintenir ni une sauvegarde des animations. Le ZIP `Polop-main/` n'est pas un dépôt Git officiel de travail et peut être archivé/supprimé seulement après vérification d'absence de fichier unique.
- `E:/perso/UE_5.8/` est une installation du **moteur Unreal**, pas un dépôt POLOP ; ne pas la déplacer/supprimer en pensant nettoyer des clones.

## Source contre résultat : ce que GitHub doit contenir

| À versionner (dans le clone officiel) | À laisser local et ne pas ajouter à Git |
| --- | --- |
| `Script_POLOP.md` et documents canoniques | `Saved/`, rapports de runs et logs locaux |
| `Unreal/previz_polop.py` et tests/scripts sources explicitement nécessaires | `Content/POLOP/Generated_*/` : cartes et séquences générées |
| `polop.uproject`, `Config/Default*.ini`, `Content/Main.umap` | `Intermediate/`, `DerivedDataCache/`, `Binaries/`, caches et captures non validées |
| Assets Unreal **sources** supplémentaires uniquement après sélection explicite | Anciens assets WIP non inventoriés, ne pas importer en masse |

Les `.umap` et `.uasset` sources ajoutés passent par Git LFS (`.gitattributes`). Les runs sont ignorés par `.gitignore` ; ne jamais employer `git add .` sans inspection. Le clone local a présenté un avertissement LFS connu sur une **ancienne capture JPG** déjà versionnée avant `.gitattributes`, sans affecter le téléchargement LFS de `Main.umap` ; traiter séparément si cela cause un problème.

## Personnages et limites à préserver

Les assets tutoriels d'Unreal (`/Engine/Tutorial/SubEditors/TutorialAssets/Character/` : `TutorialTPP`, `Tutorial_Walk_Fwd`, `Tutorial_Idle`) ne sont pas eux-mêmes dans le dépôt. Selon l'installation, leur disponibilité ou la nécessité d'un fallback proxy peut varier ; **ne pas affirmer que le cast articulé est portable sans l'avoir contrôlé sur la nouvelle machine**. Les animations sophistiquées WIP du projet Unreal historique restent à inventorier avant migration ; éviter toute suppression ou substitution par un probe de débogage.

La prévisualisation actuelle est un blockout technique, non le film virtuel final. La fermeture de #41 acte le **jalon de bootstrap local accepté**, pas l'achèvement des autres issues ni une garantie universelle de rendu/compatibilité.
