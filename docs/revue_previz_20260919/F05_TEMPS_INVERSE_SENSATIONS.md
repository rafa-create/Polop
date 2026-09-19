# F05 — Donner une réalité sensible au temps inversé

**Statut actuel : EFFETS MATÉRIELS ET JEU À CRÉER ; CONTRÔLES TEMPORELS DU BLOCKOUT À TESTER — NON VALIDÉE.** Type : développement visuel et sonore encore absent du blockout.

## Observation dans la vidéo

Vers 75–90 s, Thomas bleu descend longuement un chemin presque nu, avec un mouvement de marche provisoire. Les éléments du terrain et le décor ne donnent pratiquement aucun indice de **sens inversé**; le carton « Le paysage remonte le temps » fournit l'information à la place de l'image. La progression de Thomas de l'étonnement au plaisir n'est pas perceptible dans ce rendu.

## Référence canonique

`Script_POLOP.md` B2–B4 (l. 535–674) : Éva/Léa à rebours, pierre remontant vers sa place, feuilles, eau inversée, pied qui anticipe un gravier, caillou reçu dans la main, plaisir croissant et chorégraphie sensorielle. Les fragments d'anneau (l. 627–655, 739–751) montrent une descente à rebours du paysage, avec eau qui remonte / anneau qui descend, puis blocage et libération physique notamment par le passage du chevreuil.

## Risque

Sans un ou deux exemples concrets, un spectateur peut confondre « Thomas inversé » avec un autre Thomas se déplaçant normalement. La séquence B4 perd son contraste émotionnel avec l'arrivée au pont, où le jeu s'arrête.

## Pistes (une première passe, pas encore de simulation totale)

Commencer par deux événements lisibles dans le **même cadre que Thomas** (pierre qui remonte, eau qui se rassemble) et une micro-réaction de lui; préserver la cohérence des trajectoires objectives. Réserver la chorégraphie et les fragments d'anneau pour une passe dédiée, sans allonger arbitrairement tout le montage. Un faux rewind global de l'image n'est pas équivalent à la physique du récit.

## Critères de validation

Un spectateur distingue le changement de temps même sans carton; il voit Thomas découvrir puis anticiper au moins un événement naturel inversé. Les effets restent matériels, sans pouvoirs ni effets lumineux explicatifs. Le sentiment change avant le retour au pont.

## État de suivi au 19/09/2026 — nouvelle préviz non encore revue

**Déjà préparé :** les trajectoires de Thomas inversé et des autres personnages s'évaluent suivant le même temps objectif dans le script Unreal ; les sous-titres orientent le spectateur après la révélation. **Encore absent visuellement :** vraie inversion de l'eau, des feuilles et de la poussière, caillou qui remonte, micro-réactions de Thomas, sa montée du plaisir puis sa retenue avant le pont, ainsi que les fragments matériels du trajet de l'anneau avec blocages et libération. Un libellé « le paysage remonte le temps » n'est pas un effet effectivement rendu.

**Prochaine passe dédiée, après validation des séquences en cours :** réaliser et examiner deux actions naturelles visibles auprès de Thomas (par exemple caillou et eau), puis un geste anticipateur et sa réaction. Contrôler l'inversion de leurs instants objectifs dans les deux lectures, sans rewind global d'image. Réserver la trajectoire longue de l'anneau, le chevreuil et le travail sonore/émotionnel à une passe distincte. Montrer B2–B4 et l'approche de B5 dans le prochain extrait ; ne pas annoncer F05 résolue parce qu'un texte la décrit.

## Revue vidéo du 19/09/2026 à 18 h 56 — principal gisement de dynamisme, NON VALIDÉE

**Observé (temps vidéo) :** vers 04:00–04:42, Thomas inversé marche seul sur un sentier presque uniforme, sous des cadrages voisins et avec un cycle de bras répété ; aucune remontée de pierre ou d'eau n'est identifiable dans cette portion de la capture. Le sens inverse est énoncé par les cartons, mais le passage de la découverte au plaisir n'est pas encore incarné. L'approche 04:42–05:06 réutilise largement le même motif de marche.

**Passe proposée :** garder une descente réellement continue sur B, mais la ponctuer de **trois temps contrastés** : (1) une pierre remonte et Thomas s'arrête surpris ; (2) un second événement matériel (eau/feuille) qu'il anticipe et teste, avec jeu de bras moins automatique ; (3) le plaisir cesse à l'approche de sa famille et du pont. Montrer chacun dans le même cadre que Thomas, avec un changement d'échelle motivé par l'événement ; revisiter ensuite la durée écran de B3_B4 (25 s), B6 (16 s) et des pauses environnantes. Réserver la grande chute de l'anneau et le chevreuil à une autre passe. Pas de rewind global ni de modification des positions objectives pour fabriquer le rythme.


## Décision de montage — 19 septembre 2026 (passe courte)

Le plaisir de l'inversion doit être **bref et rythmé**, pas une accumulation d'effets. Le scénario décrit un réservoir de possibilités, pas une obligation de toutes les illustrer. Première passe ciblée : (1) une pierre remonte et Thomas la suit du regard ; (2) une seule manifestation d'eau qui se rassemble ou remonte, avec une réaction brève ; (3) Thomas anticipe un petit mouvement, sourit, puis retrouve le pont et cherche sa famille. Les feuilles, la poussière, la branche, le caillou dans la main et les fragments de l'anneau restent des options, non des prérequis de cette passe.

**Rythme :** privilégier des ellipses et une progression nette surprise → curiosité → plaisir → inquiétude au pont. Accélérer les marches sans action ; ne pas allonger une scène pour remplir le budget existant. B3_B4 occupe actuellement 25 secondes d'écran et PAUSE_RETOUR 6 secondes : ce sont des durées de la version actuelle, non des objectifs artistiques. Préparer une proposition de coupe après un premier visionnage, puis faire approuver séparément tout changement des 17 pauses, des durées du film ou des instants objectifs. Une accélération de montage ne doit pas modifier la trajectoire physique des personnages ni inventer un deuxième événement temporel.

**Statut :** cadrage créatif décidé ; animations et coupes non validées visuellement. Le correctif F07 en cours reste hors périmètre ; F03 demeure en pause. Vérifier dans Unreal que les événements sont visibles dans le plan, que le regard de Thomas les accompagne et que la transition vers le pont est lisible sans carton supplémentaire.


## Investigation GitHub du 19/09/2026 — préparation technique, pas de validation Unreal

La source actuelle `Unreal/previz_polop.py` contient un montage omniscient à durée fixe : `B3_B4` = 25 s, `PAUSE_RETOUR` = 6 s, puis `B5_PONT` = 4 s. Chaque image du film possède un temps objectif `t`, décroissant sur B3/B4 ; `character_performance()` et `add_human_performances()` évaluent les poses à ce même `t`. C'est le point d'insertion des effets et réactions, sans modifier les trajectoires `ANIM`, les instants 17 h/18 h, les 17 pauses, F03 ou F07.

**Préparation d'animation en trois événements distincts (fenêtres indicatives à caler dans Unreal, non validées) :**

- B3, première pierre : un petit volume naturel doit remonter d'un rebord vers son point d'origine dans la lecture B ; son mouvement doit être défini une seule fois en temps objectif et relu dans les deux sens. Selon le scénario, la pierre précise de B3 est délogée par le pied de Thomas normal : une pierre arbitrairement apparue à côté de Thomas inversé ne suffit PAS à réaliser ce raccord A7/B3. Faire apparaître le geste de Thomas normal dans le même mouvement de caméra avant de déclarer B3 narrativement réalisé.
- B4, mince ruissellement : quelques gouttes et une éclaboussure se rassemblent sur une roche, puis rejoignent un filet d'eau en remontant. Les volumes blockout peuvent aider à caler l'action mais une bille bleue en mouvement n'est pas une eau physiquement crédible.
- B4, petit gravier distinct : trajectoire réversible près de la chaussure. Thomas observe, anticipe le passage et adapte son pas ; prévoir un geste de tête/pied réellement animé, pas seulement un carton explicatif ni une rotation rigide du mannequin.

La transition vers B5 est une progression dramatique : dès que Thomas reconnaît le creux et voit le pont, il cesse de jouer, regarde sa montre puis le pont, et cherche sa famille. **Attention : le montage actuel B5/PONT arrive encore loin de la famille ; aucune ligne de vue ne doit être inventée.** Les regards ne doivent viser Éva/Léa que si leur position et la visibilité depuis B le permettent physiquement.

**Implémentation envisagée :** placer les propriétés des effets dans une fonction pure `f05_event_pose(event, objective_t)` ; créer des acteurs environnementaux distincts sous `POLOP/F05_Environment` uniquement pendant une régénération complète, puis baker leurs Transform et leur visibilité dans le film avec les mêmes échantillons `performance_samples` que le casting. Utiliser des clés déterministes selon `objective_t`, jamais une simulation libre ou un compteur de temps écran. Enrichir `character_performance` sur les seuls intervalles B3/B4, sans retoucher les branches à 17 h et 18 h. Ne pas utiliser `FAST_CAMERA_ONLY=True` : ce mode ne rebake ni les acteurs ni le casting.

**Statut d'exécution :** étude du générateur et conception établies. Une tentative d'écriture du grand fichier Python via le connecteur a été bloquée par les contrôles de sécurité ; après relecture, le fichier source reste à son SHA précédent `d5a3d292d39b89369c42ef334aed55bee29ff4df`. Aucun nouveau rendu Unreal n'a été exécuté, aucune trajectoire matérielle ou réaction n'est déclarée implémentée ou validée. Le test demandé reste : run complet avec `FAST_CAMERA_ONLY=False`, capture continue B2 → B3_B4 → B5, revue des effets visibles dans le même cadre que Thomas et de l'absence de régression autour de F07.
