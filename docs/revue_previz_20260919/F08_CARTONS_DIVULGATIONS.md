# F08 — Informations narratives dans les annotations de préviz

**Statut actuel : DEUX MODES DE SOUS-TITRES CODÉS ; DURÉES, CALAGE ET DIVULGATIONS À CONTRÔLER EN VIDÉO — NON VALIDÉE.** Type : pédagogie de prévisualisation vs surprise du film. **Hors sujet ici :** résolution, netteté, langue anglaise, taille ou placement du texte; ces points relèvent d'un autre correctif non testé dans cette vidéo.

## Observation dans la vidéo

Les cartons font parfois tout le travail explicatif (« le détour de Léa », « les trois passages », « absence impossible », « le paysage remonte le temps »). Vers 86–94 s, ils décrivent la situation du mousqueton et son geste sans qu'un objet animé permette de vérifier la causalité. Dans la première partie du scénario, une annotation au passage A9 signale explicitement le mousqueton décroché; la bible prévoit un indice discret, non une révélation écrite. Le spectateur comprend par la phrase, pas encore par le plan.

## Référence canonique

`Script_POLOP.md` A2 (l. 108–113), A9 (l. 291–297), B5–B6 (l. 677–703), B8 (l. 719–733) : le décrochage du mousqueton n'est **jamais montré**, le détail reste discret dans la première lecture; la cause exacte du retour normal demeure ouverte malgré les deux contacts simultanés. Les cartons ont été ajoutés uniquement pour lire une **préviz incomplète**, pas pour devenir narration définitive.

## Risque

Un premier spectateur peut croire que les explications sont la vérité révélée du film et que le scénario est conçu pour lui dire trop tôt sa propre solution. D'autres cartons rapportent des accessoires/effets **absents du rendu**, ce qui rend difficile une évaluation de l'image seule.

## Question de travail

Choisir explicitement deux modes d'évaluation : (A) **technique**, avec cartons signalant ce qui n'est pas encore animé; (B) **spectateur**, sans indices spoilants et avec les détails à découvrir par l'image. Ne pas retirer l'aide aux débutants sans leur donner une meilleure preuve visuelle. Ne pas changer le canon pour correspondre au texte provisoire.

## Critères de validation

Pour chaque carton, indiquer s'il s'agit d'un repère d'espace, d'une action encore non animée ou d'une information qui doit rester une révélation. Aucun carton du mode spectateur ne révèle prématurément le mousqueton ni n'affirme la cause définitive du retour. Le test de netteté/UMG en anglais est **reporté**, indépendant de cette fiche.

## Nouveau signalement distinct : durée du premier sous-titre (19/09/2026, capture de 17 h 28)

L'utilisateur indique que **le tout premier sous-titre reste affiché trop longtemps**. Il s'agit d'un **problème technique de durée UMG**, indépendant du fond narratif et des divulgations évaluées par F08. Le script initial assignait au cue `PAUSE_INTRO` une section et une durée de **6 s**. Correctif publié : texte intro raccourci, section native UMG et durée du cue ramenées à **3 s**; la pause de six secondes, les 16 autres sous-titres, les 17 pauses et la chronologie restent inchangés.

**À tester :** régénérer le film en mode complet (`FAST_CAMERA_ONLY=False` : son mode rapide ne retouche pas le texte), puis contrôler le début image par image : texte visible pendant la courte introduction, disparu au plus tard vers la troisième seconde de film, sans survivre sur A1. Les API UMG ou le widget peuvent conserver un état à vérifier : ce correctif statique ne prouve pas à lui seul la disparition effective. Si l'affichage persiste, demander un extrait avec le temps de Sequencer avant d'étendre la correction.

**Contenu des autres cartons :** la vidéo ne tranche pas les questions déjà soulevées sur les révélations prématurées, notamment le mousqueton décroché indiqué dans `PAUSE_ATTACHE`. Ne pas modifier ces annonces ni déclarer F08 validée à partir du problème de durée du premier sous-titre.

## Passe de sous-titres « œil neuf » publiée — 19/09/2026, nouveau rendu en cours de validation

**État du code, pas une confirmation du rendu :** `SUBTITLE_REVIEW_MODE=False` par défaut propose des cartons plus concis au spectateur ; `True` ajoute des indications techniques sur les effets/accessoires incomplets. Il reste **17 pauses** et une seule caméra. L'introduction UMG doit disparaître après trois secondes, alors que sa pause temporelle dure toujours six secondes. A1 reçoit cinq sous-titres raccourcis, avec la réponse d'Éva sur le chemin. Les **quatre répliques de Léa et Thomas** sont répétées à l'identique en A2 et en B9. Les dialogues de la pause de Thomas, de l'attente, de la recherche et de la décision de redescendre sont maintenant répartis dans A11, A12–A13 et A14. La réparation du mousqueton est explicitée **uniquement en B**, le décrochage restant discret en A. Les effets encore non animés ne sont signalés que dans le mode de revue technique ; la cause de la fermeture de 17 h 00 n'est pas tranchée par les cartons.

**Réserves et test :** le code de la préviz comprime des minutes de récit dans quelques secondes d'écran, sans jeu labial ; les phrases doivent être évaluées avec les actions réelles et non seulement par leurs indices de trame. Le spectateur ne doit pas recevoir des informations d'A9 ou B9 avant l'instant où elles deviennent pertinentes. Tester le départ, A1/A2, A10–A14, B5/B6 puis B9 avec le nouveau run, en particulier débuts/fins des sections UMG, chevauchements, rémanence du premier carton et rythme des échanges ; demander à une personne découvrant l'histoire de résumer les chemins, la disparition et la fonction du mousqueton **sans relire les cartons**.

**Procédure :** `FAST_CAMERA_ONLY=False` obligatoire pour reconstruire textes et séquences ; tester d'abord `SUBTITLE_REVIEW_MODE=False`, puis si nécessaire le mode technique sur un run complet distinct. Ne pas déclarer F08 ni le premier cue validés avant la vidéo et l'accord de l'utilisateur. Les commentaires historiques précédents décrivent la préviz *avant* cette passe et ne correspondent plus aux textes actuellement publiés.

## Revue vidéo du 19/09/2026 à 18 h 56 — lisibilité et persistance, NON VALIDÉE

**Observé (temps vidéo) :** les sous-titres anglais sont généralement visibles dans un bandeau inférieur et l'échange de Léa/Thomas apparaît bien dans A2 puis B9. **Anomalie à diagnostiquer :** au tout début de cette capture, la première image de montagne porte le texte « THOMAS MOVES INTO THE PAST », qui concerne une scène bien plus tardive ; vers 06:12, le lecteur revient à la montagne avec le titre d'introduction. Ce décalage peut être lié au redémarrage/bouclage et/ou à une persistance UMG : la capture ne suffit pas à attribuer une cause. Contrôler au frame 0 d'un nouveau lancement froid le début/fin des sections UMG et l'effacement à trois secondes, en particulier au raccord fin → début.

**Rythme observé :** des cartons de cinq à sept secondes demeurent sur des cadres presque figés (vers 01:12–01:21, 02:24–02:30, 03:15–03:33, 04:06–04:12, 05:12–05:18, 05:33–05:40). Des phrases annoncent encore une action qui n'est pas visible : réparation et collision, ainsi que le contact de l'anneau. Les 17 pauses totalisent 106 s dans le montage de 372 s, soit presque 29 % : elles peuvent constituer un outil de révision utile, mais la version spectateur doit être auditée pour éviter d'immobiliser l'image afin de faire lire le récit. Le script a reçu deux modes de sous-titres, pas un montage spectateur plus court.

**À faire :** valider l'absence de texte parasite au lancement et au bouclage, puis voir si chaque pause apporte une information nouvelle **au bon moment**. Revoir en priorité les redondances PAUSE_ATTACHE, PAUSE_ATTENTE, PAUSE_RETOUR, PAUSE_MOUSQUETON et PAUSE_BOUCLE. Ne pas effacer les 17 repères historiques ou modifier les 372 s par défaut : préparer une variante de durées/densité à arbitrer en F09. Pour un test « œil neuf », masquer aussi les messages rouges de debug et l'interface Sequencer ; pas de jugement sur le son, absent du fichier.
