# POLOP — Unreal Previz

## Source de vérité

### Révision du rythme — 18 septembre 2026

Le plan-séquence de blocage passe de 693 à 266 secondes (4 min 26).
Les changements ordinaires de cadrage durent au plus trois secondes ; les
vues larges A5 et finale durent huit secondes. La caméra reste près du chemin
pour regarder le pont, au lieu d'effectuer un aller-retour jusqu'à lui.
La traversée B6 dispose de six secondes distinctes, suivies de huit secondes
pour B7/B8. B9 suit désormais Thomas normal, comme demandé par le scénario.

Le passage de Thomas inversé sur le pont est canonique : B6 indique B vers A,
après le geste sur le mousqueton vers 17 h 01. Léa revient par le FLANC.
Le rapprochement des deux Thomas se termine vers 17 h 00 (minute objective 2).
Ne pas supprimer cette traversée pour corriger une ambiguïté de cadrage.

La version resserrée a été générée dans Unreal dans le run
`20260918_212116_518810`, séquence `LS_POLOP_OMNISCIENT_222405_944014`, puis
examinée pendant sa lecture dans le viewport. Ce contrôle n'est pas un export
vidéo final. Ses raccords de position mesurés sont inférieurs à 1e-12 m.
La vitesse maximale atteint 68,06 m/s : la compression des longues marches
reste très visible. La grotte demeure trop sombre. L'anneau, le geste du
mousqueton et la fermeture masquée par le relief ne sont pas validés.
La correction du regard vers le pont a été ajoutée après cette première lecture.
Elle a ensuite été générée dans `LS_POLOP_OMNISCIENT_222856_861056`.
Une relecture ciblée à partir de 3 min 46 a confirmé le trajet B vers A,
mais révélé une superposition exposée des deux Thomas vers 3 min 59.
Un relief de premier plan a donc été ajouté à côté de la voie, sans changer
les trajectoires. La lecture montre désormais le masquage puis le retour à
Thomas normal et à la famille. Ce volume est encore un bloc massif : sa forme
naturelle, son encombrement dans le cadre, la lisibilité du contact et l'anneau
restent à travailler. Cette correction ne vaut pas validation finale de B8.

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

## Objectif de livraison

Le rendu final doit être une **caméra omnisciente**, avec une simulation esthétique
et compréhensible qui respecte les révélations de `Script_POLOP.md`. Les quatre
POV sont des outils de vérification. La caméra doit notamment rester avec Éva et
Léa pendant l'entrée de Thomas, puis révéler la grotte en A15, et respecter la
lecture normale → inversée → retour final. Un rapport technique vert ne valide
pas, à lui seul, cette mise en scène.

L'objectif de réalisation est désormais explicitement un **plan-séquence**.
Les étapes A/B servent de repères narratifs dans une seule trajectoire caméra.
La dernière révision remplace les sauts entre cadrages par une interpolation
continue de la position et du point regardé, avec départs et arrivées amortis.
Les grands déplacements allongent automatiquement la durée ; 276 secondes était
la durée de la version précédente à cadrages séparés, plus celle de cette version.
L'heure objective est également continue aux raccords A1/A2 et A17/B1.

Les contrôles hors Unreal vérifient les raccords exacts, la progression de
l'interpolation et la continuité des bornes temporelles. Le manifeste exporte
les écarts aux raccords et la vitesse maximale mesurée de la caméra. Cette nouvelle
trajectoire n'a pas encore été validée visuellement dans Unreal : les collisions,
les occultations et l'absence de révélations prématurées restent à contrôler.
Une interpolation continue ne garantit pas à elle seule un plan-séquence réussi.

La première génération continue a été exécutée dans Unreal : 693 secondes, une
seule section caméra, 19 raccords à 0 m d'écart et 20 captures produites. Leur
inspection a révélé des sujets perdus pendant les transitions et des passages
derrière le relief. La correction suivante (`9b995ad`) suit les positions
actuelles des sujets des deux côtés de la transition, et relève la caméra au-dessus
du Landscape hors grotte. Elle reprend aussi les positions de caméra intérieures.
Les rochers et le toit de la grotte ne sont pas couverts par ce contrôle de hauteur.

La seconde passe (`OMNISCIENT/220418` du même run) a également produit 20 captures
inspectées. Les raccords restent inférieurs à 1e-12 m ; le suivi de Léa et du groupe
est amélioré. La durée est de 693 s (11 min 33), et la vitesse maximale mesurée
reste de 36,27 m/s : le calcul de durée n'est pas une limitation stricte à 20 m/s.
Les vues géographiques, l'approche A15 et B1 restent insuffisantes ; la caméra perd
encore certains centres d'intérêt pendant les grands trajets. Il faut remplacer
ces transitions génériques par des points de passage choisis dans le décor et
contrôler la visibilité image par image. Statut : continuité technique vérifiée,
mise en scène et fidélité au scénario non validées.

## Reprise du 18 septembre — déplacements et exécution différée

- Correction de `NameError: __file__ is not defined` : Unreal retire cette variable
  après l'exécution du fichier, avant les callbacks Slate. Le chemin source est
  maintenant conservé dans `SOURCE_SCRIPT_PATH` dès le chargement.
- Raccords continus entre l'accès, la zone rocheuse et l'intérieur de la grotte.
- Positions distinctes pour Éva et Léa ; suppression du saut vers leur attente.
- Regard de Thomas inversé orienté selon son temps vécu ; disparition du trajet
  artificiel depuis le sous-sol avant 17h00.
- Échantillonnage des déplacements et des POV à 30 images/seconde.
- Les marqueurs sphériques de diagnostic sont masqués dans la scène.

Le run `20260918_212116_518810` a terminé avec un rapport **OK** dans UE 5.8.2.
Les nouveaux contrôles portent sur la continuité des trajectoires, la séparation
Éva/Léa, la présence de Thomas dans la grotte avant la recherche et le regard
inversé. Il ne s'agit pas encore d'une validation visuelle des quatre parcours.

### Lecture automatisée des POV

L'option de lancement Unreal `-POLOPReview` déclenche la lecture après génération.
Les captures attendues sont dans `Saved/POLOP/Runs/<run_id>/POV/` et chaque demande
est inscrite dans le keylog. Une demande de capture ne prouve pas que le PNG existe
ou que son contenu est correct. La lecture limite l'avancement par tick pour
éviter qu'une compilation de shaders saute un parcours ; un verrou évite les
callbacks imbriqués pendant les opérations de l'éditeur.

### Montage omniscient en préparation

`build_omniscient_edit()` construit une séquence distincte
`LS_POLOP_OMNISCIENT`, en rééchantillonnant tous les personnages sur la même heure
objective, d'abord croissante puis décroissante. Le découpage est exporté dans
`omniscient_edit.json`. Ce montage de travail est désormais généré par défaut
après les contrôles techniques. Son exécution a été testée dans Unreal ; sa
fidélité narrative et ses cadrages ne sont pas encore validés.
L'ouverture A0, l'anneau, le mousqueton animé, les effets inversés, le jeu et le son
restent à produire. Ne pas présenter ce montage de travail comme le film final.

## Validation omnisciente — 18 septembre 2026

Le montage de 276 secondes a été exécuté, puis ses 20 plans ont été capturés et
inspectés dans le run `20260918_212116_518810`.

Un défaut majeur a été corrigé : `LevelSequenceEditorSubsystem.add_actors()`
crée déjà une piste Transform. Ajouter une seconde piste mélangeait les positions
et plaçait notamment la caméra à mi-distance de sa destination. Le générateur
supprime désormais la piste automatique avant de créer la piste animée, pour les
corps, têtes, POV et la caméra omnisciente. Les séquences locales ont été corrigées
et les positions réellement évaluées vérifiées sur neuf instants : aucun écart
supérieur à 2 cm pour les quatre corps. Les anciens rapports fondés uniquement sur
le modèle numérique ne détectaient pas ce défaut.

`validate_sequencer_evaluation()` ajoute désormais ces contrôles au générateur.
`start_omniscient_review()` produit une capture par plan et vérifie la présence des
PNG avant de journaliser la fin, avec protection contre les callbacks imbriqués.
Les images sont conservées localement sous `OMNISCIENT/<heure>/` dans le run.

**Verdict visuel : non validé comme adaptation finale.** Léa est trop basse dans
le tablier du pont ; la grotte reste trop sombre et certains cadrages y sont trop
serrés ; les silhouettes sont encore de simples proxies ; le relief en damier et
les sentiers demandent une finition. Le plan géographique et la distance de la
caméra de grotte ont été repris pour une seconde passe de captures. Les gestes,
objets et phénomènes canoniques listés ci-dessus restent absents. La visibilité
des deux Thomas et leur occultation nécessitent une reprise de mise en scène.

## Fichier nécessaire sur GitHub

Le **seul fichier de code à télécharger et exécuter** est
`Unreal/previz_polop.py`. Il contient la géographie, l'animation, le montage et les
outils de contrôle ; il ne charge pas les scripts `old/` ou `reference/`.
`README_PREVIZ.md` fournit les prérequis et limites, sans être une dépendance du
code. Cela ne signifie pas qu'un PC vide peut exécuter le fichier seul : Unreal,
les deux plugins et le Landscape source décrits plus haut restent nécessaires.


## Checkpoint du cast avant validation physique de #44 — 19 septembre 2026

Source préservée au commit `af7adc856dea20cfd7f4ae412025d42c1fa2ad4a`.
Le WIP conserve `character_performance`, `prepare_human_cast` et
`add_human_performances` : positions, orientations et poses squelettiques sont
échantillonnées depuis le temps objectif partagé. Le film complet avec ce cast
n'a pas encore été généré ni validé. Ne pas remplacer ce travail par la vue debug.

Le dépôt Git local Unreal n'a qu'un commit initial (`71e13ff`), pas de remote,
240 assets déjà indexés et 14 fichiers suivis modifiés. Les sources `Unreal/`
y sont non suivies. Le checkpoint GitHub a donc utilisé le connecteur sans
embarquer ni réinitialiser cet index. Les assets générés restent locaux.

Préservation locale du code, des deux scripts de reprise, du test sauvegardé et
de leurs SHA-256 : `Saved/POLOP/Checkpoints/20260919_cast_wip/`.
Le test modifié en mémoire a été dupliqué sans écraser l'original dans
`/Game/POLOP/Generated_V10/Runs/20260918_212116_518810/Sequences/LS_CAST_WIP_CHECKPOINT_20260919_012120`.
Le `LS_CAST_PROBE` original contient quatre bindings articulés. Sa version
sauvegardée initiale couvrait les frames 0 à 59 ; la version en mémoire termine
à 61 (borne exclusive), à 30 fps. Ce test va donc jusqu'à 17 h 00 environ,
pas jusqu'à 17 h 01 : il ne prouve pas encore la convergence.

Audit numérique exécuté dans la session Unreal, sans changement de trajectoire :
`Saved/POLOP/Runs/20260918_212116_518810/closure_wip_audit.json`.
À la minute objective 2, les racines des deux Thomas sont à distance zéro, mais
leurs orientations diffèrent de 180 degrés et leurs phases squelettiques sont
différentes. À 2,01 min, la séparation des racines n'est encore que de 0,2499 m.
L'occultation ne valide donc pas l'absence d'interpénétration. Le masquage par
réduction d'échelle avant 17 h n'est pas une résolution physique de la fermeture.
L'anneau et un événement explicite de raccord des branches restent absents.

**Statut : WIP conservé, vérité physique non validée.** Avant une refonte,
clarifier si DEUX → UN désigne la continuité suivie après la bascule alors que
les deux occurrences subsistent aux mêmes temps objectifs, ou une réduction
réelle à un seul corps, incompatible en l'état avec la coexistence après 17 h.
Aucune issue n'est fermée ; aucune sophistication supplémentaire n'a été ajoutée
pendant cet audit. #41 demeure le prochain chantier global après résolution de
cette sous-passe immédiate de #44.
