# F01 — Présenter la famille et garder l'arc émotionnel

**Statut : CADRAGE INITIAL À REPRENDRE ; B9 À TESTER DANS UNREAL — NON VALIDÉE.** Type : mise en scène incomplète / éléments de scénario non encore animés.

## Observation dans la vidéo

Au début (environ 0–11 s de l'enregistrement), la caméra présente surtout un personnage isolé et un environnement très dépouillé; les trois membres de la famille ne forment pas immédiatement une unité identifiable. On reconnaît mieux le trio vers 38–41 s. À la fin (99–104 s), le retour à la famille et l'éloignement se succèdent rapidement dans l'extrait, sans geste intime lisible.

## Référence canonique

`Script_POLOP.md` A0 (l. 17–51) : la rivière, l'anneau puis vallée, montagne, trois silhouettes, **sans coupe**. A1–A4 (l. 55–225) : jeux ordinaires, Éva photographie, Thomas en retrait, humour autour de la montre et de Strava. B9 (l. 753–845) : reprise d'A2, petite **boîte destinée à Éva** touchée dans la poche, regard vers Éva/Léa, hésitation, départ ensemble, dézoom final.

## Risque pour quelqu'un qui découvre l'histoire

Sans scène familiale initiale suffisamment claire, la disparition et le retour de Thomas perdent leur poids affectif. Sans le geste de la boîte et la reprise nuancée de la randonnée, la boucle ressemble à une simple répétition de parcours.

## Pistes pour une fiche de réalisation ultérieure

Distinguer deux étapes : (1) garantir un plan lisible des trois personnages avant l'écart de Léa, conserver A0 comme scène à construire; (2) prévoir les gestes et les répliques minimales du retour B9. Le matériau n'est pas assez avancé pour juger le jeu des acteurs ou la musique.

## Critères de validation

À la lecture sans annotation, un spectateur peut identifier Thomas, Éva et Léa avant le détour. Le retour reprend le même moment de manière reconnaissable, avec l'hésitation et la boîte distinctes de la version initiale. L'ouverture A0 et la fin canonique sont soit visibles, soit **signalées comme encore à construire**, jamais présentées comme déjà validées.


## Première passe approuvée : cadrage seul (19/09/2026)

**Commit du script :** `ee92cc8e2166e59467d58350f2bc6c312a210dd0`. **Rendu non encore testé** et **fiche non validée**.

- **PAUSE_INTRO et ouverture A1** : un cadrage panoramique dynamique prend en compte les positions réelles de Thomas, Éva et Léa afin de les inclure ensemble; la caméra revient graduellement vers Léa lorsqu'elle approche du pont. **Limite de la base existante :** au temps objectif initial, Léa se trouve déjà sensiblement devant Thomas et Éva. Ce changement de caméra ne les rapproche PAS physiquement; on teste un plan d'ensemble, pas un portrait familial rapproché. Si l'unité du trio demeure illisible, il faudra discuter d'une modification distincte du blocking avant toute intervention sur les trajectoires validées.
- **B9 et PAUSE_ISSUE** : cadrage qui donne plus de place à Thomas, sans changer la seconde lecture de 17 h 00–17 h 01 ni la demande de Léa de revenir par le pont.
- **B9_ELOIGNEMENT** : dézoom progressif autour du centre réel des trois personnages; la caméra suit leur déplacement tout en révélant progressivement le paysage existant. Aucun geste de boîte, nouvelle réplique, scène A0 de rivière ni effet naturel de conclusion n'a été créé dans cette première passe.

**Invariants du code contrôlés avant publication :** la fonction des mannequins articulés, toutes les trajectoires ANIM, l'ordre, les durées et les temps objectifs des plans, la construction F03 (mise en pause), la variante sous-titres UMG et la caméra/séquence omniscientes sont inchangés. Ces contrôles statiques ne valent pas test de cadrage ou de collision dans Unreal.

**Validation à demander :** vérifier avec le nouveau run et la seule caméra `PZ_ANIM_CAM_OMNISCIENT` : (1) intro/A1 montrent-ils bien trois silhouettes identifiables sans en cacher une ? (2) le raccord vers la traversée de Léa est-il fluide ? (3) B9 concentre-t-il plus justement le regard sur Thomas sans effacer Éva et Léa ? (4) le dézoom final retrouve-t-il le trio en mouvement, puis la géographie sans saccades ni passage dans le terrain ? Les gestes, la petite boîte, l'ouverture A0 et l'émotion musicale restent à faire dans des passes ultérieures **après accord**. F03 reste ouverte et gelée.

## Deuxième ajustement de cadrage B9 — 19/09/2026

**Script publié, non testé dans Unreal :** `899772b37fc86b442b1395d6f99dac2e835eef80`.

Suite au visionnage du retour B9 et du dézoom, le cadrage sur Thomas se rapproche progressivement en fin de B9 (temps objectif 7,45–8), puis reste auprès de lui pendant la pause. Le dézoom suivant retarde son éloignement d'environ 2,4 secondes de temps écran avant de suivre le centre mobile des trois personnages pour retrouver le paysage. La chronologie, les 17 pauses, les déplacements du casting, la première version du cadrage d'ouverture et la géométrie F03 n'ont pas été modifiés. Le geste de la boîte n'est pas encore créé. Vérifier dans Unreal le raccord B9 → pause → dézoom et l'absence d'obstruction du terrain; F01 n'est pas validée. Demander séparément l'extrait complet du début jusqu'au pont avant toute correction supplémentaire de l'ouverture. F03 demeure en pause.

## Revue de la capture du 19/09/2026 à 17 h 28 — ouverture confirmée

L'utilisateur confirme explicitement que le plan très éloigné aperçu au **début de l'enregistrement** est bien le début de la préviz, et non un extrait d'une autre séquence. Le précédent doute sur l'identification du plan est donc levé : **la première passe F01 ne présente pas encore les trois personnages à une taille suffisante pour lire la famille**. Les trois silhouettes deviennent plus faciles à distinguer lors du détour près du pont (environ 36–52 s dans l'enregistrement), mais cet instant arrive trop tard pour remplacer l'installation familiale d'A1. La caméra suit toujours des positions de départ très espacées; aucun changement de trajectoire n'est autorisé par cette seule observation.

**Action à discuter en F01 :** recadrer plus près le début sans couper Thomas ou Éva, et contrôler le raccord vers Léa; si le blocking actuel rend un plan familial rapproché impossible, soumettre un changement limité des positions initiales à validation explicite, au lieu de le faire silencieusement. La véritable ouverture A0 (rivière → montagne, sans coupe) demeure non réalisée. Le retour B9 et son dézoom révisés ne sont pas visibles en entier dans ce dernier extrait; conserver leur statut « à tester ».

**Sous-titre initial — signalement confirmé par l'utilisateur :** le premier carton reste à l'image trop longtemps. Le code l'affichait pendant la totalité de la pause introductive de 6 s. Correction publiée dans le script : texte introductif raccourci à deux lignes et plage de la section UMG **ainsi que durée du cue** réduites à **3 s**, sans modifier la pause introductive, les 17 pauses ou la durée du film. **À vérifier sur un nouveau run complet, avec `FAST_CAMERA_ONLY=False` : le mode rapide ne régénère pas les sous-titres.** Ne pas considérer cette correction comme validée tant que le texte ne disparaît pas réellement avant la reprise de la randonnée. F03 reste en pause.
