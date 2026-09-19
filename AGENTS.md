# AGENTS.md — Règles obligatoires pour Codex / POLOP

## 0. Dépôt et dossier de travail : une seule autorité

- Dépôt officiel **unique** : `https://github.com/rafa-create/Polop.git` ; branche de livraison : `main`.
- Sur le PC de septembre 2026, dossier actif : `E:/perso/polop/Polop-git/`. Sur un autre PC, utiliser **la racine du clone officiel**, quel que soit son chemin ; ne jamais coder un chemin local absolu dans une source ou une configuration versionnée.
- Avant d'éditer, vérifier que la racine contient `.git/`, `polop.uproject`, `Script_POLOP.md`, `Unreal/previz_polop.py` et que `git remote -v` désigne le dépôt officiel. Vérifier branche, `git status -sb` et changements distants. **S'il existe plusieurs copies, ou si le travail local n'est pas synchronisé, demander laquelle utiliser ; ne jamais deviner.**
- **Ne pas travailler dans** `E:/perso/polop/polop/` : ancien projet Unreal avec dépôt Git `master` local indépendant, sans remote, contenant des séquences/animations WIP potentiellement absentes de GitHub. Ne jamais le nettoyer, réinitialiser, écraser, migrer en masse ni le supprimer. Son contenu ne devient canonique qu'après inventaire et migration **sélective validée par l'utilisateur**.
- `Polop-test-clone/` est un clone temporaire de vérification, **pas** une deuxième source du projet. Les dossiers ZIP `Polop-main/` ne sont pas des clones Git.

## 1. Autorités des fichiers — lire avant toute modification

| Rôle | Fichier ou dossier versionné | Consigne |
| --- | --- | --- |
| Bible narrative absolue | `Script_POLOP.md` | Aucune ancienne version, capture, storyboard ou run ne la contredit. Ne pas modifier sans demande narrative explicite. |
| Projet Unreal à ouvrir | **`polop.uproject`** (minuscules, à la racine) | UE **5.8.2** est la version locale testée. `EngineAssociation: "5.8"` ; conserver PythonScriptPlugin et SequencerScripting actifs. |
| Carte source de démarrage | `Content/Main.umap` = `/Game/Main` | Carte versionnée via **Git LFS**, avec Landscape source 1009 × 1009, 16 × 16 composants. **Ne pas enregistrer un run sur cette carte**. Si une évolution du bootstrap doit modifier la carte source, faire une sauvegarde et demander validation spécifique. |
| Générateur actif unique | **`Unreal/previz_polop.py`** | C'est CE script qu'il faut modifier pour changer la préviz et lancer dans Unreal avec **Tools/Outils > Execute Python Script**. Les fichiers `Unreal/old/` et scripts copiés ailleurs sont historiques, jamais une entrée de production. |
| Configuration portable | `Config/Default*.ini`, `polop.uproject`, `.gitignore`, `.gitattributes` | Versionner toute modification nécessaire à une ouverture sur un autre PC. Éviter les chemins absolus, GUID propres au PC et options de plugins non disponibles par défaut. |
| Documents du workflow | `Unreal/README_PREVIZ.md`, `docs/ENVIRONNEMENT_REPRODUCTIBILITE.md`, `README.md` | Actualiser dès que l'installation, les prérequis ou la procédure changent. |

## 2. Exécution, validation et séparation source / résultat

1. Partir d'un clone officiel synchronisé et d'UE 5.8.2 avec Git LFS installé ; ouvrir **`polop.uproject` du même clone** et `/Game/Main`.
2. Lancer **`Unreal/previz_polop.py` depuis ce même clone**, jamais une copie dans un autre dossier ou un script historique. Il duplique la map source et produit un run isolé.
3. Résultats locaux : `Content/POLOP/Generated_*/` (cartes et séquences générées) et `Saved/POLOP/Runs/<run_id>/` (logs/rapports). Ils **ne sont pas des sources** ; ne pas les pousser à GitHub. Les dossiers `Saved/`, `Intermediate/`, `DerivedDataCache/`, `Binaries/` restent également locaux.
4. Valider avec le rapport du **même `run_id`** ; vérifier sa fin et les blocages, puis inspecter visuellement les séquences si l'évolution l'exige. Un rapport technique vert ne prouve pas la conformité du film entier. Ne pas refaire le même run sans modification ou besoin de preuve précis.
5. Référence de preuve locale au 19/09/2026 : depuis `Polop-git`, UE 5.8.2, run `20260919_084218_028677`, rapport MASTER V10 `OVERALL: OK`, **35 OK / 0 WARN / 0 FAIL / 0 BLOCKER**, animation V05 OK, résultat inspecté visuellement. Un clone frais séparé a récupéré `polop.uproject` et `Content/Main.umap` via LFS ; **aucun run n'a été fait dans ce clone, ni test sur un autre ordinateur**. Ne pas inventer ces validations.

## 3. Versionnage et publication : responsabilité de Codex

- Avant de travailler : inspecter `git status -sb`, la branche et le remote ; récupérer les changements du distant et **ne pas écraser des changements concurrents ou locaux**. Si des modifications non comprises existent, s'arrêter et demander. Pour les modifications GitHub directes intervenues pendant une session locale, synchroniser le clone **avant** de modifier/pousser.
- Modifier **les sources suivies appropriées** (`Unreal/previz_polop.py` pour le générateur, `Config/Default*.ini` ou `polop.uproject` si prérequis modifié), puis la documentation concernée ; consigner l'objectif, la version UE, les tests réellement faits et leurs limites.
- Avant chaque commit, examiner `git diff`, `git diff --check`, `git status` et **lister exactement les chemins à indexer**. Utiliser `git add -- <fichiers_sources_précis>`, **jamais** `git add .`, `git add -A`, `git commit -a`, `git clean` ou `git reset --hard` pour « remettre au propre ». Ne pas publier un run généré, les logs, caches, assets de test ou données propres à un PC.
- Les seuls binaires Unreal à versionner sont les **assets sources explicitement justifiés** (dont `Content/Main.umap`) ; `.umap` et `.uasset` passent par Git LFS. Avant le push, vérifier `git lfs status` et que les pointeurs sont correctement enregistrés. Ne pas convertir/supprimer en masse les assets ni appliquer de migration LFS à tout l'historique sans accord.
- Après validation, créer un commit descriptif et **pousser sur `origin/main` si le remote et l'absence de conflit sont confirmés** et si l'utilisateur a autorisé le travail ; contrôler le SHA distant et `git status -sb`. Si un conflit, une protection de branche ou un blocage survient : ne pas forcer le push, demander une décision. Une branche de travail est possible si nécessaire, mais ne pas créer de dépôts Git séparés « juste pour Unreal ».
- Toute modification indispensable à l'installation doit exister **sur GitHub**, pas uniquement sur un PC. Ne pas annoncer « portable » parce qu'une installation locale fonctionne ; distinguer **ouverture sur le PC testé**, **clone frais local**, **validation sur un autre PC**.
- Une ancienne capture `Unreal/captures/previz_polop_complet_v03__capture_topview.jpg` a été ajoutée avant les règles LFS : `git clone` peut signaler « should have been a pointer ». Ne pas confondre avec `Content/Main.umap`, qui a été téléchargée via LFS. Documenter ou traiter ce cas séparément, sans réécriture globale de l'historique.

## 4. Protection des animations et vérité narrative

- Préserver le WIP des personnages articulés après 17h dans l'ancien projet tant que ses sources/assets n'ont pas été inventoriés, sauvegardés et migrés. **Ne jamais prétendre que GitHub contient déjà ces assets locaux**. Si un nouveau travail nécessite ces fichiers, demander l'accès/l'inventaire à l'utilisateur.
- Ne pas confondre vérité physique (temps objectif, positions et états du monde, causalité, objets) et mise en scène (caméra, occultation, montage). Ne pas masquer un bug physique par un cadrage ; ne pas éliminer un Thomas physiquement existant pour résoudre la scène.
- Si le travail est bloqué par une dépendance introuvable, une version UE différente ou un conflit entre le script et les ressources locales, **s'arrêter et poser une question précise** avant toute refonte ou suppression.

## 5. Prochaine machine

Installer UE 5.8.2 et Git LFS ; cloner `https://github.com/rafa-create/Polop.git` ; ouvrir le `polop.uproject` de ce clone ; exécuter son `Unreal/previz_polop.py`. Conserver/transférer **séparément** l'ancien dossier Unreal `polop/` si ses animations WIP doivent survivre au changement de PC : les fichiers restés uniquement dans cet ancien dossier **ne voyagent pas avec le clone GitHub**.
