# LA BOUCLE — revue de la prévisualisation du 19 septembre 2026

**Statut : registre de revue et correctifs successifs ; fiches non validées, F03 en pause.** Revue de la capture utilisateur `2026-09-19_15h33_22.mp4` (enregistrement écran de **105,6 secondes**, avec une lecture accélérée/consultation du montage : les temps ci-dessous repèrent **la vidéo envoyée**, non les heures du récit ni les secondes du film). Elle montre l'ancien rendu **avant** la modification de sous-titres en anglais/UMG, qui sera testée plus tard.

**Autorité narrative :** `Script_POLOP.md`. Le script Unreal reste un blockout : distinguer une contradiction à l'image d'un accessoire, dialogue, effet ou scène **pas encore réalisé**. Ne pas déclarer une erreur de trajectoire physique à partir d'une seule capture. Les figures et les annotations de préviz ne sont pas censées être dans le film final.

## Dernière revue : vidéo du 19/09/2026 à 18 h 56 — première version exploitable, rythme à améliorer

**Source nouvelle :** `2026-09-19_18h56_45.mp4`, capture vidéo de **375,63 s** du rendu dans Unreal (légèrement plus longue que les **372 s** de la séquence du script). Les minutages de revue ci-dessous correspondent à la **capture**, non aux heures 17 h/18 h de la fiction ; la capture se termine sur le retour de l'image d'introduction. **Aucune piste audio** dans le fichier, donc on ne peut pas juger les paroles réelles, le CLAC, les silences ou la musique. Les nouveaux constats complètent sans effacer les observations plus anciennes.

**Bilan visuel :** les trois personnages et leurs itinéraires deviennent globalement suivables, le mousqueton B bénéficie d'un rapprochement lisible et la seconde lecture revient bien à la famille. **Les longues marches avec mouvements identiques, les 17 pauses (106 s des 372 s), le gros volume de l'ancrage, la recherche/grotte occultée et surtout le rocher couvrant la collision freinent fortement le visionnage.** Un sous-titre de la partie inversée apparaît sur l'image initiale de la capture ; contrôler le démarrage/bouclage UMG. F03 demeure **en pause** malgré la persistance de l'occultation dans cette vidéo.

**Plan d'attaque recommandé :** (1) vérifier/corriger le plan **F07** de collision pour rendre l'accident visible depuis un angle latéral, sans toucher F03 ; (2) rendre la remise du mousqueton **F06** corporelle et claire avant la traversée ; (3) varier l'action et les regards sur la longue descente inversée **F05** ; (4) travailler le trio, la boîte et les émotions **F01**, ainsi que la lisibilité du pont **F02** ; (5) seulement ensuite proposer à l'utilisateur une **variante de rythme écran** qui traite les pauses redondantes et les marches répétées sans bouleverser les 17 repères ou les heures objectives, puis retester F08 sur un lancement froid. Le dossier **[F09 — Rythme et dynamisme](F09_RYTHME_DYNAMIQUE.md)** contient les repères vidéo détaillés et la méthode de remontage.

**Point à clarifier avec l'utilisateur :** « animation de vote » n'identifie pas de façon certaine un geste dans la vidéo ; ne pas supposer qu'il s'agit de la petite boîte, de la marche, ou d'une autre action tant que le terme n'a pas été confirmé.

**Statut de validation :** toutes les fiches restent ouvertes ; les retouches de rythme, d'acting et d'objets sont des **propositions**, non des modifications déjà réalisées dans Unreal. La Bible et `Unreal/previz_polop.py` n'ont pas été modifiés pendant cette revue. **F03 et sa fiche restent inchangées, gelées sur demande.**

## État courant — après les correctifs de caméra, convergence, mousqueton et sous-titres (19/09/2026)

**Nouveau run Unreal en cours de validation par l'utilisateur ; aucun des éléments ci-dessous n'est réputé validé à l'image.** Les repères vidéo datés plus bas proviennent des enregistrements *antérieurs* aux derniers changements et servent d'historique, pas de constat sur le rendu à venir. `Script_POLOP.md` reste la Bible narrative ; les numéros de lignes cités dans les anciennes fiches peuvent être décalés depuis sa mise à jour A2/B6–B9.

| Fiche | Déjà préparé / publié dans le code | Travail restant avant validation |
| --- | --- | --- |
| **F01** | Aller-retour continu de caméra famille ↔ Éva/Thomas ↔ Léa, dialogues A1/A2/B9, cadrage B9/dézoom | Tester le véritable début et la fin dans la nouvelle vidéo ; A0 rivière, geste de la boîte, acting et musique finale non construits. |
| **F02** | Trajets A/B/pont/flanc et passe de cadrage du pont ; B6_REPAIR sur la rive B avant la traversée | Vérifier rives, creux, culées, durée du flanc, et compréhension spatiale **sans** les cartons. |
| **F03** | Corrections anciennes de cavité/terrasse publiées | **EN PAUSE SUR DEMANDE** : aucune reprise du travail A12–A15 ni validation tant que l'utilisateur ne le décide pas. |
| **F04** | Repères textuels 18 h et perceptions ; proxies des deux occurrences | Créer/tester anneau et contact, éclairage/perceptions de la grotte ; ne pas modifier F03 en passant. |
| **F05** | Trajectoires en temps objectif ; repères de sous-titres | Créer de vrais effets naturels inversés, jeu et sons ; trajets matériels de l'anneau en passe dédiée. |
| **F06** | Attache côté B, état animé d'un proxy, halte et cadrage B6, révélation B seulement | Tester action/visibilité et raccord pont ; vraie main, cordage et CLAC encore à créer ; A reste discret. |
| **F07** | Une collision objective à 17 h, pause/regard de Thomas, trajectoire inverse sur A, caméra centrée Thomas | Tester occultation physique des yeux de Thomas inversé et dégagement caméra ; anneau/contact et boîte non animés. |
| **F08** | 17 cartons conservés, mode « spectateur » par défaut et revue technique optionnelle, nouveaux dialogues A1/A2/B9/A11–A14 et repères B6 | Tester durée UMG intro 3 s, calage, chevauchements, lisibilité et divulgation seulement au moment voulu. |

**Mode de contrôle courant :** régénérer complètement avec `FAST_CAMERA_ONLY=False` et `SUBTITLE_REVIEW_MODE=False` pour vérifier ensemble trajets, sous-titres et nouvel état du mousqueton. Le mode rapide ne reconstruit ni casting ni texte. En cas de régression, demander une capture ciblée et le premier message d'erreur du **même run** avant une nouvelle correction. Les sept fiches mises à jour décrivent le travail encore ouvert ; F03 demeure inchangée et gelée. La clôture d'une fiche exige une confirmation explicite de l'utilisateur après visionnage.

## Fiches à traiter séparément

| Fiche | Question à résoudre | Repère vidéo |
| --- | --- | --- |
| [F01](F01_DEPART_FAMILLE.md) | Ouvrir sur la famille, préserver l'ouverture rivière et la fin émotionnelle | 0–40 s, 99–104 s |
| [F02](F02_GEOGRAPHIE_PONT_FLANC.md) | Comprendre le pont, A, B et le flanc sans explication plaquée | 10–20 s, 47–54 s, 89–94 s |
| [F03](F03_DISPARITION_TERRASSE_PRECIPICE.md) | Rendre l'absence de Thomas physiquement convaincante | 54–65 s |
| [F04](F04_REVELATION_GROTTE_ANNEAU.md) | Montrer la grotte et le contact sans noir inexpliqué ni dévoiler le double trop tôt | 65–75 s |
| [F05](F05_TEMPS_INVERSE_SENSATIONS.md) | Faire exister le temps inversé à l'image, pas seulement dans les cartons | 75–90 s |
| [F06](F06_MOUSQUETON_PONT.md) | Retrouver le geste et le trajet du pont, préserver la révélation | 90–95 s et A1–A2 |
| [F07](F07_CONVERGENCE_ET_FIN.md) | Rendre la rencontre des deux Thomas et la boucle lisibles sans montrer de fusion | 95–104 s |
| [F08](F08_CARTONS_DIVULGATIONS.md) | Contrôler l'information narrative contenue dans les cartons (pas leur netteté) | 0–4, 34–36, 86–96 s |
| [F09](F09_RYTHME_DYNAMIQUE.md) | Rendre le plan continu dynamique, supprimer les répétitions sans déplacer les événements objectifs | Nouvelle vidéo 18 h 56 : 00:45–01:03, 02:00–02:36, 04:00–04:42, 05:27–05:42 |

## Méthode de validation

1. L'utilisateur **choisit une seule fiche** et approuve son objectif avant modification.
2. Établir, si nécessaire, une vérification objective de positions, visibilité réelle et continuité; ne pas camoufler un problème de géométrie par la caméra seule.
3. Modifier uniquement ce qui concerne la fiche, sans toucher au cast articulé, aux pistes de visibilité validées ni au scénario canonique sans demande explicite.
4. Générer un **nouveau run isolé** dans Unreal; examiner l'extrait correspondant et les rapports du même run. Évaluer les critères propres à la fiche.
5. Marquer **VALIDÉE** seulement après confirmation explicite de l'utilisateur, puis choisir la suivante.

**Aucune fiche de ce registre n'autorise à elle seule la modification du scénario ou de `previz_polop.py`.** La correction technique du texte UMG/anglais est une piste séparée déjà publiée, **non testée dans la capture analysée**.

## Mise à jour — enregistrement du 19/09/2026 à 17 h 28

La vidéo plus récente montre le **véritable début** de la prévisualisation (confirmation de l'utilisateur). F01 reste ouverte : la famille est trop éloignée dans les premières secondes malgré la passe de caméra publiée; les personnages se distinguent mieux vers 36–52 s près du pont, mais B9 et le dézoom révisés ne sont pas entièrement montrés. **F03 reste explicitement en pause et non validée** : une masse rocheuse continue à gêner un plan vers 72–76 s, sans nouveau diagnostic physique. F02 reste à discuter : présence du trio au pont ≠ lisibilité de toutes les routes.

Le premier **sous-titre UMG** dure trop longtemps selon l'utilisateur. Un correctif technique limité au cue `PAUSE_INTRO` est publié (3 s au lieu de 6 s, texte réduit); son rendu n'est pas encore validé. La correction exige **un run complet** : `FAST_CAMERA_ONLY=True` ne change que les clés de caméra et laisse tous les cues existants intacts. La question des spoilers et du contenu des cartons demeure distincte (F08). Les fiches F04–F07 et F06 gardent leurs statuts existants faute de nouveaux plans assez concluants dans cette capture; aucun critère de validation n'est présumé rempli.

**Méthode courante :** les anciennes observations et repères de la vidéo du 15 h 33 restent des archives, pas des descriptions exhaustives du rendu du 17 h 28. Aucun fichier de fiche ne valide un effet encore invisible, et chaque nouvelle correction doit être vérifiée dans son propre run.
