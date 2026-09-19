# F04 — Révélation de la grotte, perceptions, contact de 18 h

**Statut actuel : PASSAGES CANONIQUES ENCORE PARTIELLEMENT ABSENTS DU BLOCKOUT — NON VALIDÉE ; F03 GELÉE.** Type : scène fondatrice absente ou illisible dans le blockout.

## Observation dans la vidéo

Environ 65–70 s : la transition vers la cavité est très noire et une partie d'un lettrage/carton reste seule visible dans le noir. Vers 71–74 s, deux mannequins bleus occupent nettement la même cavité; leurs silhouettes et positions sont difficiles à attribuer à une **perception** particulière. Aucun anneau, approche dans la fissure, geste de contact ou changement matériel concomitant n'est identifiable dans cette capture. Une partie de l'obscurité peut venir d'un obstacle/cadrage provisoire : ne pas conclure à une erreur de collision sans tester.

## Référence canonique

`Script_POLOP.md` A15–A17 (l. 439–501) : la caméra révèle l'ouverture seulement après avoir quitté Éva/Léa; Thomas est entré de quelques pas, écouteurs aux oreilles, l'anneau remonte par impacts mécaniques vers lui, contact **exactement à 18 h 00**, la trajectoire de l'anneau repart vers le bas et Thomas s'inverse. B1 (l. 511–531) : Thomas inversé, habitué au noir, distingue une **silhouette**, sans reconnaître son visage; Thomas normal, encore ébloui, ne perçoit pas son double. Aucun flash ni effet surnaturel.

## Risque

Un plan presque noir suivi de deux corps visiblement exposés peut faire lire une téléportation ou une rencontre consciente, contrairement au scénario. Un carton ne remplace pas les deux conséquences visuelles simultanées du contact.

## Approche à décider

Séparer **validation spatiale** (entrée, paroi, fissure, accès des deux occurrences) et **validation des regards** (plans de perception différents). Construire un repère simplifié de l'anneau et une animation matérielle minimale avant d'essayer les effets naturels complets. Vérifier la synchronisation temporelle au même instant objectif, sans apparition/disparition artificielle du double.

## Critères de validation

La révélation de l'ouverture survient en A15 seulement. Le contact annulaire de 18 h est visible, simultané au changement de direction de l'anneau. B1 fait comprendre que seul Thomas inversé **voit une silhouette**; l'autre ne la voit pas à cause de l'obscurité, pas parce que le double a disparu. Les trajectoires 3D restent cohérentes.

## État de suivi au 19/09/2026 — après revue du code et de la Bible

**Pas de nouvel essai validant A15–B1.** Les nouvelles passes de sous-titres donnent des repères au contact de 18 h et à la perception dans l'obscurité, mais elles ne créent ni l'anneau ni ses rebonds, ni le contact de la main, ni la divergence des perceptions par le jeu/la lumière. Les deux occurrences articulées existent comme proxies temporels ; cela ne prouve pas que leur visibilité à l'écran respecte les yeux de Thomas normal et inversé.

**Reste à faire lorsque le travail F03 sera explicitement repris :** vérifier d'abord que l'ouverture de la cavité est révélée depuis un trajet de caméra et une géométrie réellement dégagés. Puis animer un anneau matériel montant vers Thomas, son contact **exact à 18 h 00** et sa descente, sans flash ni explication magique ; rendre les deux regards distincts (silhouette perceptible seulement par Thomas inversé à cet instant) en contrôlant les lignes de vue, l'éclairage et les POV. Tester l'extrait A15–A17 puis B1 dans Unreal. **Ne toucher à aucune géométrie ni caméra de F03 tant que cette fiche reste en pause.**

## Revue vidéo du 19/09/2026 à 18 h 56 — obstacle visuel et contact manquant, NON VALIDÉE

**Observé (temps vidéo) :** autour de 03:00–03:36, l'image est très largement occupée par des surfaces de roche ; la révélation de l'entrée et l'approche de l'anneau ne se comprennent pas par l'image. Vers 03:39–03:45 apparaissent de très près des corps/volumes dans la cavité, suivis de plusieurs secondes de noir ; le carton de 18 h apporte l'explication temporelle à la place du contact visible. L'enregistrement n'a pas de piste audio, impossible d'évaluer un effet sonore ou le silence.

**À faire, sans réouvrir F03 indirectement :** préparer hors scène un **test isolé de l'anneau** (trajectoire matérielle, main et repère 18 h) et une étude de silhouettes/éclairage permettant de distinguer les perceptions. L'insertion dans A15–B1 et toute correction de paroi, d'entrée ou de caméra de grotte restent BLOQUÉES tant que F03 est gelée. Ne pas compenser 30 secondes d'image occultée par de nouveaux sous-titres ; la solution exige une reprise géométrique/caméra dédiée avec l'accord de l'utilisateur.


## Reprise de travail autorisée — passe grotte puis rythme (19/09/2026)

L'utilisateur reporte la validation F01/F02 et demande de poursuivre avec la grotte, puis les longueurs. **Cette autorisation ouvre la préparation et les essais ciblés F04 ; elle ne valide pas rétroactivement F03 ni le rendu précédent.** La géométrie de la poche, la caméra A15 et l'occultation encore signalée restent des prérequis physiques : ne pas déclarer la scène résolue par l'ajout d'un anneau ou par des sous-titres. F07 en validation distincte ne doit pas être retouchée.

### Ordre d'implémentation et critères de passage

1. **Diagnostic visuel A12–A15, avant toute retouche :** identifier dans le même run Unreal le mesh opaque responsable de l'image bouchée (nom de l'acteur et profondeur de caméra), tester depuis les yeux d'Éva et Léa l'occultation réelle de l'entrée, et depuis A15 le trajet complet caméra–cible. Si le blocage persiste, demander un extrait A12–A15 et le premier message d'erreur du run ; aucune modification géométrique à l'aveugle. Une éventuelle reprise F03 se fait en passe dédiée, pas via F04 ou F09.
2. **Contact A16–A17 dans un banc isolé :** un proxy d'anneau de taille lisible remonte mécaniquement depuis la fissure, rebondit contre la roche, ralentit à portée de Thomas, entre en contact avec sa main au seul instant objectif 18 h 00, puis repart vers le bas. La position et l'orientation de l'anneau sont définies par l'heure objective, jamais par le sens de lecture écran ; les deux lectures doivent donc être le même événement vu dans deux sens. Le contact ne doit pas dépendre d'une téléportation du proxy ni d'un flash.
3. **Perceptions B1 :** depuis Thomas inversé, silhouette non identifiable dans le noir ; depuis Thomas normal, pas de reconnaissance de son double. Tester deux POV distincts avec lumière et exposition mesurées, sans cacher artificiellement un personnage qui est physiquement présent. Vérifier que le spectateur comprend le contraste de perception sans carton supplémentaire.
4. **Intégration seulement après les tests :** conserver le temps objectif 18 h, les 17 pauses, la durée actuelle et le trajet de chacun ; insérer le proxy et les regards dans la séquence existante après preuve que la caméra et l'entrée sont dégagées. Puis contrôler A15 → A17 → B1 en lecture continue et sur les deux sens temporels.

**Statut de cette passe : spécification prête ; aucun nouveau rendu Unreal ni animation d'anneau n'est prétendu réalisé.** Les prochaines corrections géométriques dépendent d'une capture et d'un diagnostic du même run, pour ne pas défaire le masquage depuis les femmes.
