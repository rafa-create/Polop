# POLOP — Unreal Previz

> **Bootstrap Git versionné depuis le 19/09/2026 :** le projet de référence se trouve à la racine du clone officiel, dans `polop.uproject` (minuscules). `Content/Main.umap` est fourni par Git LFS ; ne pas recréer manuellement le Landscape. Ouvrir **le projet et le script du même clone** (`Unreal/previz_polop.py`). Lire `AGENTS.md` et `docs/ENVIRONNEMENT_REPRODUCTIBILITE.md` pour la procédure Codex et la migration vers un autre ordinateur. UE 5.8.2 + run MASTER V10 OK (35/0/0/0) vérifiés localement ; aucun run dans le second clone ni essai sur un autre PC. La préviz reste un blockout et non le film final.

## Source de vérité

### Révision du rythme — 18 septembre 2026

Le plan-séquence de blocage passe de 693 à 266 secondes (4 min 26).
Les changements ordinaires de cadrage durent au plus trois secondes ; les
vues larges A5 et finale durent huit secondes. La caméra reste près du chemin
pour regarder le pont, au lieu d'effectuer un aller-retour jusqu'à lui.

### Retouche ciblée A9 — 19 septembre 2026

Sur le **seul plan A9_PONT** (pont vu de loin), la caméra se décale légèrement
sur le côté et s'élève depuis le chemin actuel, vise le milieu des deux
extrémités existantes et effectue un bref resserrement optique de sa focale
jusqu'à 72 mm. Elle retrouve ensuite sa focale initiale pendant le raccord
vers A10. Durée A9 inchangée : 4 secondes, caméra toujours continue, pas de
vol rapide vers le pont. Le relief, les chemins, la position du pont, la
première traversée de Léa et le plan B5_PONT restent inchangés.

Modification publiée dans `Unreal/previz_polop.py` ; contrôles statiques des
blocs modifiés et de leur présence sur GitHub effectués. **Aucun nouveau run
Unreal ni contrôle visuel du cadrage n'a été exécuté ici** : vérifier sur le
run du clone synchronisé que le tablier, les deux extrémités et le sentier du
flanc sont effectivement lisibles, et que le raccord vers A10 reste fluide.
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

1. Installer Git LFS, puis **cloner le dépôt officiel** `https://github.com/rafa-create/Polop.git` sur `main` ; ne pas télécharger un script isolé.
2. Utiliser Unreal Engine **5.8.2** (version validée localement). Ouvrir **`polop.uproject` à la racine du clone** ; Python Editor Script Plugin et Sequencer Scripting y sont activés.
3. Charger la carte source `/Game/Main` fournie sous `Content/Main.umap` via Git LFS : son Landscape 1009 × 1009 sommets, 63 quads par section, 1 section par composant, 16 × 16 composants est déjà enregistré. Ne pas le reconstruire manuellement et ne pas y enregistrer les modifications d'un run.
4. Exécuter le **`Unreal/previz_polop.py` de ce clone** dans l'éditeur Unreal, via Outils / Tools > Execute Python Script. Python système ne fournit pas le module `unreal`.
5. Attendre l'événement `complete` dans `Saved/POLOP/Runs/<run_id>/keylog.jsonl` ; en cas de `failed`, examiner le journal du même run.
6. Vérifier le rapport du même `run_id`, puis la carte générée et sa séquence omnisciente. Ne pas commiter `Content/POLOP/Generated_*/` ni `Saved/`.

**Limite :** le script ne crée pas un Landscape à partir d'un projet Unreal vide ; **ce n'est plus une préparation manuelle nécessaire** lorsque l'on ouvre le `polop.uproject` du clone officiel, car le dépôt inclut `Content/Main.umap`. Le test local validé ne démontre pas encore la portabilité du cast sur un autre PC.

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

Le **seul script de génération à modifier et exécuter** est
`Unreal/previz_polop.py`. Il contient la géographie, l'animation, le montage et les
outils de contrôle ; il ne charge pas les scripts `old/` ou `reference/`.
**Le projet Unreal à cloner inclut toutefois aussi** `polop.uproject`,
`Config/Default*.ini` et `Content/Main.umap` via Git LFS : ne pas se limiter
au téléchargement isolé du fichier Python. `README_PREVIZ.md` décrit les
prérequis et limites sans être une dépendance du code.


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

## Reprise du 19 septembre — cast articulé et film courant

La clarification canonique lève le blocage du checkpoint précédent : avant
17 h, une occurrence ; à 17 h, raccord local ; pour chaque instant strictement
entre 17 h et 18 h, **deux occurrences présentes**. B9 suit Thomas normal sans
supprimer Thomas inversé. Les issues #44, #12 et #21 portent déjà cette règle.

Le WIP articulé est conservé. Les deux branches atteignent une même orientation,
un même clip et une même phase à 17 h. Le demi-tour de B7 se termine avant le
rapprochement final ; le cycle du recul est inversé. La cadence de marche dépend
désormais de la distance objective parcourue, avec une calibration provisoire
du mannequin adulte à 1,2 m/s, et non du temps écoulé à l'écran. Aucun morphing
ni changement d'échelle ne réalise le raccord. La visibilité exprime seulement
le domaine temporel de la branche ; le point exactement commun est dessiné une
seule fois. Les os continuent d'être évalués hors champ.

Les fonctions de contrôle sont intégrées au seul Python actif :
- `audit_cast_closure()` : raccord et coexistence sur 5 999 instants intérieurs ;
- `build_cast_closure_probe()` : nouveau test, sans écraser `LS_CAST_PROBE`,
  de 16:59:57 à 17:00:21, puis retour et relecture des mêmes instants ;
- `validate_cast_closure_evaluation()` : contrôle asynchrone dans Unreal des
  racines, de la visibilité et des 68 os, sur 21 échantillons.

Run contrôlé : `20260918_212116_518810`, UE 5.8.2, Windows.
Test : `LS_CAST_CLOSURE_20260919_073346_364121`.
Rapports locaux : `cast_closure_report.json` et `cast_closure_evaluated.json`.
Avec la marche par distance : erreur maximale des racines 0,003904 cm ;
écart des os au raccord inférieur à 0,000001 cm ; écart de relecture inférieur
à 0,000001 cm ; visibilité conforme sur les échantillons.
**Cela valide le raccord du cast et sa relecture, pas toute la physique de #44.**
L'appui de la main sur la roche, l'anneau, le mousqueton, les collisions détaillées
et le raccord articulé de 18 h restent à terminer. La marche reste provisoire.

### Une entrée de lancement, une caméra active

Le générateur désigne maintenant dans chaque map produite :
- `POLOP_FILM_CURRENT` : acteur Level Sequence pointant vers le film courant ;
- `PZ_ANIM_CAM_OMNISCIENT_CURRENT` : sa caméra ;
- `POLOP/Cameras/Archives` : anciennes caméras conservées pour les essais.

Un doublon technique a été corrigé : Sequencer créait une coupe caméra
automatiquement, puis le script en ajoutait une seconde. La piste est désormais
créée avec **une seule coupe couvrant toute la plage de lecture**.

Après génération, le film courant s'ouvre dans Sequencer à la frame zéro.
Utiliser la lecture de Sequencer pour le regarder. L'acteur
`POLOP_FILM_CURRENT` est aussi configuré pour lancer ce film avec Play (PIE)
dans la map générée ; ce chemin doit être contrôlé dans Unreal.
La fonction `play_omniscient_film()` revient au début et lance la lecture ;
`play_omniscient_film(play=False)` l'ouvre simplement au début.
Il ne faut pas choisir une caméra au hasard dans la liste des essais.

Le fichier local `Saved/POLOP/Runs/<run_id>/current_film.json` indique la map,
la séquence exacte, la caméra, la durée et le SHA-256 du Python publié.
La version courante de cette passe est `LS_POLOP_OMNISCIENT_073733_588799`,
7980 frames à 30 fps, soit **4 min 26**, de A1 à B9.
**Lecture intégrale de cette prévisualisation ne signifie pas adaptation
complète du scénario** : A0 rivière, les contacts/gestes, les effets inversés,
le jeu et le son ne sont pas tous réalisés. Ne pas fermer #44 ni #46 sur la
seule base de ces tests.

Le Python et ses outils de contrôle sont sur GitHub ; les scripts de reprise
sous Saved ne sont pas des dépendances. Le bootstrap d'un ordinateur neuf reste
le chantier #41 : une installation Unreal et la coquille Landscape source sont
encore nécessaires.


### Passe #49 — placement familial, 19 septembre 2026 (validation visuelle en attente)

La référence active est #48, avec #49 comme correction macro prioritaire ; les
anciens numéros cités dans les sections historiques ci-dessus ne sont pas des
chantiers séparés. Bible lue au commit `4747d5a`.

Sans changer la géographie, les premiers mètres du flanc représentent désormais
la descente de Léa depuis B (interprétation autorisée par l'utilisateur). Elle
quitte le pont à 16h59:30, ralentit à 17h01:30–17h01:39 pour regarder Thomas normal,
puis poursuit le même flanc ; arrivée inchangée à 17h06. Éva s'écarte de quatre
mètres du centre du chemin, douze mètres avant la jonction sur A, pour regarder
le paysage pendant le passage de l'inversé. Le décalage latéral préexistant de
son corps reste appliqué. Thomas normal rejoint cette zone d'attente. Le modèle
rejoint les anciennes trajectoires à 17h02 pour les adultes, à 17h06 pour Léa.
La branche inversée, les chemins, les rochers, la grotte et les clips articulés
ne sont pas modifiés. Les horaires intermédiaires sont des choix de blockout.

Contrôles statiques réalisés sur les fonctions sources et les routes V11 du run
`20260919_093417_388979` : syntaxe du maître et des deux sources embarquées,
raccord de pose à 17h00, domaine de coexistence des deux Thomas, égalité des
poses aux mêmes instants interrogés dans les deux sens et conservation des
trajectoires après les fenêtres modifiées. Échantillonnage horizontal toutes
les 0,06 secondes objectives de 17h00 à 17h06 : distance minimale à l'inversé
3,35 m pour Éva et 8,54 m pour Léa ; angle minimal entre orientation corporelle
et direction de l'inversé respectivement 51,52° et 61,69°. Ces mesures ne sont
**pas une preuve de non-perception** : ni champ périphérique, ni regard des yeux,
ni occultation, ni animation évaluée dans Unreal n'ont été contrôlés. Le test
statique utilise un Z plat ; il ne valide pas les appuis sur le Landscape.

Le prochain lancement produira `bridge_family_blocking.json` et l'événement
`bridge_family_blocking_measured` dans les résultats locaux du même run. Ce
rapport mesure les positions/orientations ; il laisse explicitement la
validation visuelle en attente et ne ferme pas #49.

Vérification nouvelle nécessaire : depuis `/Game/Main` du clone officiel,
exécuter `Unreal/previz_polop.py` une fois, attendre `complete`, puis examiner le
nouveau résultat entre 16h59 et 17h02 dans les deux sens, notamment 17h00:17,
17h01:07 et la pause de Léa à 17h01:30. Vérifier les appuis d'Éva hors du sentier,
les regards, la continuité des arrêts et le rejeu A2/B9. Ne pas sauvegarder le
résultat dans `Content/Main.umap`. Aucun nouveau run Unreal n'a encore été fait
pour cette passe. Le mousqueton reste un proxy statique et l'anneau n'est pas
animé : la causalité complète demandée par #49 reste donc à traiter et valider.
