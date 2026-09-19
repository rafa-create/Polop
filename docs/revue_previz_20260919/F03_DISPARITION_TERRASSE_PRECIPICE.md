# F03 — Disparition : terrasse, paroi, précipice, chemin gardé

**Statut courant : RÉOUVERTE pour la correction ciblée du trajet caméra A15 — correctif GitHub publié, rendu Unreal NON VALIDÉ.** (Les mentions « en pause » plus bas documentent les décisions antérieures.) Type : enjeu causal majeur / géographie et mise en scène.

## Observation dans la vidéo

Vers 54–65 s, les personnages évoluent sur une zone qui paraît assez ouverte; les plans montrent un grand espace lisse, puis un précipice ou un bord dans le premier plan à distance, sans établir de façon continue la **petite surface fermée entre paroi et vide**. Le spectateur ne peut pas encore vérifier par l'image qu'Éva et Léa contrôlent l'unique sortie et que Thomas n'a pas simplement contourné le relief. Le rocher d'occultation ressemble à un volume massif; un photogramme ne suffit pas à prouver que l'ouverture de la grotte est réellement hors de leur vue.

## Référence canonique

`Script_POLOP.md` A10–A15 (l. 301–457) : quelques dizaines de m², paroi, rochers, précipice, entrée de caverne masquée par un décrochement **depuis la trajectoire des femmes**, unique sortie naturellement dans leur champ, courte recherche effective, regard vers le chemin puis le vide, descente chercher de l'aide. Thomas n'est **pas vu entrant** dans la caverne.

## Risque

Si l'espace semble vaste ou qu'une seconde sortie paraît plausible, la peur d'une chute devient une déduction forcée par la narration. Si la grotte est visible, l'absence n'est plus mystérieuse; si seul le cadrage cache Thomas, le problème physique demeure.

## Contrôles à mener avant correction

Tracer depuis leurs yeux les lignes de vue vers : retour sur A, terrasse entière, entrée réelle de la grotte, bord du précipice. Vérifier que leur recherche passe derrière les rochers accessibles et que Thomas peut atteindre l'ouverture sans croiser cette ligne de vue. Inspecter le Landscape et l'écart réel terrasse–rebord avec une capture latérale à hauteur humaine, pas seulement la caméra omnisciente.

## Critères de validation

Une unique vue (ou un mouvement très court) situe paroi, quelques m² praticables et vide; le parcours filmé de la recherche exclut une autre sortie visible. Les femmes ne voient ni l'entrée ni Thomas y pénétrer; la caméra ne révèle la cavité **qu'en A15**. Aucun déplacement ou occultation n'est uniquement un tour de caméra.

## Première implémentation approuvée (19/09/2026)

**Commit script :** `8d1ae58383753e39598ec30710bc4576e1b5b37a`.

- Thomas quitte le chemin A et entre dans **la même poche près du précipice** que fouilleront ensuite Éva et Léa : motif banal, pause toilettes. Il contourne physiquement le gros bloc situé à l'extrémité apparente de la paroi, passe derrière lui, puis entre dans une **ouverture sombre réelle** à l'abri de leurs regards. La grotte V05 est rapprochée de cette extrémité; ses points internes et les deux parcours de Thomas sont raccordés à cette nouvelle bouche, sans changer le casting articulé.
- Deux volumes de roche constituent le masque physique : l'un depuis le chemin A, l'autre depuis les positions de recherche. Les femmes vont vers la poche mais ne contournent pas l'extrémité qui leur paraît bouchée. Un filet d'ombre à l'intérieur suggère une roche continue jusqu'au changement de point de vue A15; ne pas afficher la bouche avant.
- Le Landscape conserve sa rupture de terrain à proximité immédiate de la petite zone. Le gros bloc vertical de 21 m ajouté devant la falaise a été supprimé pour ne pas cacher le précipice réel.
- A11 reste cadré du côté d'Éva et Léa; A12 accompagne leur déplacement avant de décaler la caméra du côté du vide. A14 garde ce point de vue pendant leur départ. A15 reste seul détenteur de la révélation.
- Une vérification **2D indicative** des segments de trajet des deux Thomas et des angles de vue des femmes par rapport aux volumes des deux rochers est intégrée au script. Elle ne remplace pas la vérification 3D des hauteurs, collisions, ombres et silhouettes dans Unreal.

**À vérifier dans le prochain run :** 1) la génération complète réussit; 2) les deux femmes restent effectivement devant l'impasse apparente et ne voient ni Thomas entrer ni l'ouverture; 3) la terrasse paraît petite et fermée, le vide reste lisible; 4) le chemin réel de Thomas et celui de son occurrence inversée ne traversent pas les roches, les talus ou le bord; 5) la grotte ne se dévoile qu'en A15; 6) les mannequins articulés et les 17 pauses restent fonctionnels. La variante anglaise/UMG des sous-titres n'est **pas** considérée comme validée par cette fiche.

### Tester F03 sans avancer le chantier des sous-titres

Le script principal conserve par défaut le nouveau système de sous-titres anglais, **non validé à ce stade**. Pour isoler uniquement F03, saisir dans la console Python de l'éditeur Unreal AVANT « Execute Python Script » :

```python
import os; os.environ["POLOP_F03_GEOMETRY_ONLY"] = "1"
```

Exécuter ensuite le `previz_polop.py` mis à jour, depuis une carte sauvegardée, et vérifier les scènes A10 à A15. Dans CE run de test, les 17 pauses restent sur la timeline **sans texte**; aucun plugin UMG n'est nécessaire. Les animations et la caméra restent présentes. Après le test, vider la variable dans la même console Python :

```python
import os; os.environ.pop("POLOP_F03_GEOMETRY_ONLY", None)
```

Puis fermer et rouvrir Unreal plus tard pour tester les vrais sous-titres avec la configuration normale. Ne pas considérer l'absence de texte pendant le test F03 comme une régression.

Captures demandées pour la validation : A10 Thomas s'écarte; A11 ligne de vue des femmes vers l'unique sortie; A12–A13 (vue à hauteur humaine et caméra film) paroi + petite terrasse + bord du vide; A15 **première apparition** de l'entrée; vérifier également dans le journal l'absence d'erreur F03 et la fin de génération. Étiqueter les captures du même run.

**Important :** statut « À TESTER » ne signifie **pas** que la mise en scène est validée. Attendre la vidéo/captures et l'accord de l'utilisateur avant toute autre fiche.

## Correctif de régression du regard inversé (19/09/2026)

**Commit du script :** `1973734fd9d4f1c395ab49a1e3916b8f72a6e832`. Le dernier run F03 est resté **BLOCKED** sur `inverse_gaze_follows_personal_time` (produit scalaire à t=60,5 : `-0.2050496489`) et n'a donc pas construit la caméra `PZ_ANIM_CAM_OMNISCIENT`. Il ne s'agissait pas d'une suppression de la caméra : le master n'appelle sa création qu'après la validation narrative.

Le virage serré nouvellement introduit entre la poche rocheuse et la grotte est incompatible avec le regard interpolé sur ±0,35 s, qui coupe plusieurs segments du trajet. Dans `pov_direction`, uniquement pour Thomas inversé et `60.2 <= t < 60.6`, le regard suit désormais la direction locale du segment de marche **dans son temps personnel**. Le reste de la fonction, l'ensemble des trajets, les visibilités du casting, les 17 pauses et le contrôle narratif bloquant sont inchangés. Aucun contournement des validations n'a été ajouté.

**À tester dans Unreal :** vérifier d'abord `inverse_gaze_follows_personal_time : OK`, puis `complete` et la présence de `LS_POLOP_OMNISCIENT` / `PZ_ANIM_CAM_OMNISCIENT` dans le nouveau run. Si un autre contrôle bloque, conserver le journal du **même run**. La géographie et les regards réels de F03 restent à valider visuellement.

## Deuxième passe F03 — terrasse et révélation (19/09/2026)

**Statut : correction publiée, à contrôler sur la nouvelle vidéo Unreal. Pas encore validée.**

**Commits du script :** `6c8cd7bf35f448318b7bd324b6415042f9c3acae` (caméra A15), puis `a1d5c3a98c7faf74a0cbbc8bcb48289a02f8b9b9` (terrasse et précipice).

**Problème observé dans la vidéo de 16 h 19 :** la recherche des femmes paraît se dérouler dans une grande zone ouverte; le passage A15 devient majoritairement gris/noir parce que la caméra traverse une masse rocheuse avant de découvrir Thomas, au lieu de dévoiler la petite entrée dissimulée. L'animation des mannequins et la caméra omnisciente fonctionnent : ne pas les reconstruire.

**Modifications ciblées :**

- Le plateau local artificiellement aplani est resserré autour des positions de recherche. Le **vrai** précipice dans le Landscape commence juste au sud de la poche et se prolonge un peu plus à l'est. Sa retouche reste strictement à l'écart du sentier `HAUT` et ne touche ni A/B, ni le pont, ni le flanc.
- Le contrechamp A12–A14 est rapproché de la terrasse pour lire ensemble les femmes, la paroi et la rupture de terrain, au lieu de révéler un vaste terrain non borné dans un plan aérien éloigné.
- **A15 seule** reçoit une trajectoire cinématographique en quatre étapes depuis la dernière pose A14 : face apparemment fermée, décalage latéral côté inaccessible aux femmes, dévoilement de la fente sombre, progression par l'ouverture vers Thomas. Le mouvement reste dans la même piste et la même caméra omnisciente; aucun montage additionnel ni téléportation.
- La position intérieure de la caméra de la grotte a été recentrée, car l'ancienne coordonnée latérale passait dans le volume géométrique du rocher droit. Un contrôle des enveloppes elliptiques des quatre rochers est appliqué aux images de la révélation. Il faut encore vérifier dans Unreal le dégagement réel en Z, les maillages, ombres, silhouettes et la lisibilité du cadre.

**Critères visuels de validation :** montrer A11 (sortie surveillée), A12–A14 (petite poche + paroi + bord du vide dans un même plan), A15 (paroi semblant fermée, puis fente révélée SANS obstruction prolongée ni caméra passant dans la roche), puis Thomas dans la cavité. Vérifier que les femmes n'ont jamais l'angle de A15, et que le trajet des deux Thomas reste dégagé. Vérifier aussi que le film omniscient est publié en fin de run et que les contrôles n'ont pas régressé.

**Tester sans mélanger avec le chantier des sous-titres anglais :** utiliser `POLOP_F03_GEOMETRY_ONLY=1` selon la procédure plus haut. Cela laisse les 17 pauses temporelles présentes **sans texte** pour ce run. Revenir ensuite au mode normal pour tester séparément le rendu UMG.

## Deuxième passe ciblée : petite terrasse et révélation A15 (19/09/2026)

**Commit du script :** `5f69fdb51ce050b105738752f4513e6eef155856` — **À TESTER dans Unreal, NON VALIDÉ**.

- **Géographie physique :** le bord réel du précipice dans le Landscape est rapproché de la poche de recherche (début de la rupture à `y=-10.2 m` dans le repère du relief, contre `-11.1 m` auparavant); la route la plus proche de Thomas reste à `y=-8.2 m`. Deux volumes rocheux bas prolongent la paroi du côté montagne, pour que les femmes perçoivent une petite poche effectivement bornée et non une vaste plaine simplement recadrée.
- **Cause d'une obstruction concrète :** le rocher latéral droit de l'entrée occupait la trajectoire `CAVE_ZONE_POINT → CAVE_ENTRY_POINT` de Thomas et l'ancienne trajectoire de l'objectif. Il est déplacé vers le côté précipice et réduit; une vérification de dégagement du trajet réel de Thomas a été ajoutée pour ce volume, en plus des masques existants.
- **Caméra omnisciente A15 uniquement :** la trajectoire adopte plusieurs points du coude réellement praticable; la caméra regarde d'abord la paroi apparente, puis dévoile l'ouverture par déplacement latéral. Le code vérifie désormais **le rayon du regard caméra** après le contournement, pas seulement l'emplacement de l'objectif. Le montage demeure en **une seule caméra omnisciente**; aucune piste d'animation du casting, durée de plan, pause narrative ou système de sous-titres n'est modifié.

**Limites des contrôles automatiques :** les enveloppes de rochers sont testées en 2D (XY) et ne garantissent ni le rendu, ni les contacts réels des meshes, ni le masquage par le plafond, ni l'illusion de continuité créée par les ombres. Si un contrôle F03 bloque, relever le premier message d'erreur du **nouveau run**; la fiche ne peut être validée sur le seul succès de génération.

**Test ciblé à faire :** récupérer ce commit, utiliser au besoin `POLOP_F03_GEOMETRY_ONLY=1`, exécuter un nouveau run depuis une carte source sauvegardée. Vérifier d'abord `complete` et l'ouverture de `LS_POLOP_OMNISCIENT`; puis examiner A10 (entrée dans la poche), A11 (sortie surveillée), A12–A13 (paroi + petite surface + précipice dans le même espace), A14 (aucune bouche visible depuis les femmes) et A15 (découverte progressive de l'ouverture, sans rocher collé devant l'objectif). Contrôler séparément la vraie ligne de vue depuis les yeux d'Éva et Léa. Attendre la validation explicite de l'utilisateur avant de fermer F03.


## Troisième passe : enlever les occultations structurelles de l'entrée (19/09/2026)

**Commit script :** `7bee76e83d2186009b258788e09bedb79c4520a7` — **NON TESTÉ DANS UNREAL / F03 EN ATTENTE DE VALIDATION.**

Le rendu vidéo du run précédent montrait encore un grand bloc sombre/gris devant l'objectif pendant A15 et une portion de la grotte. Le diagnostic code a révélé un problème supplémentaire distinct des rochers latéraux : le plancher, le plafond et les parois de la grotte artificielle commençaient environ **1 m avant sa bouche**, donc une partie du volume opaque occupait exactement le passage qui devait être révélé. Les seuls contrôles d'écartement 2D des rochers ne pouvaient pas signaler ces trois pièces.

**Correction ciblée :** reculer ensemble les trois pièces opaques (sol artificiel, deux parois et toit) pour qu'elles commencent **3,2 m après l'entrée**. Conserver les vrais rochers de masquage vus depuis Éva/Léa, les petites bandes d'ombre latérales et le sol du Landscape devant la grotte. La trajectoire physique des deux Thomas et la caméra omnisciente ne sont pas remplacées; le passage doit maintenant être une **ouverture libre réelle**, non une boîte vue à travers un autre objet.

**Contrôle supplémentaire :** dans A15 après le contournement (progression ≥ 0,60), le code vérifie aussi que l'objectif est au moins 1,25 m au-dessus du Landscape réel; le test d'enveloppes 2D des rochers reste en place. Ce contrôle peut **bloquer** le run si le nouveau mouvement passe sous le terrain. Il ne constitue pas une garantie de visibilité intégrale des meshes, des ombres ou du rendu Unreal.

**Test avant de clore F03 :** récupérer le dernier script, lancer un nouveau run en mode `POLOP_F03_GEOMETRY_ONLY=1` si le test des sous-titres est reporté, vérifier `complete` et `LS_POLOP_OMNISCIENT`. Dans le film A12–A15, examiner (1) la petite surface bornée par la paroi/le vide, (2) l'impasse apparente depuis les femmes, (3) l'apparition progressive de l'ouverture après leur départ, (4) la caméra passant par une entrée dégagée puis montrant Thomas dans la cavité. Contrôler la vraie visibilité de l'entrée depuis les POV d'Éva et Léa. En cas d'échec, transmettre le **premier message d'erreur du même run** ou un extrait vidéo A15. Aucune nouvelle fiche ne doit être déclarée validée avant accord de l'utilisateur.

## Décision de suivi — 19/09/2026, capture de 17 h 28

**F03 EST EN PAUSE À LA DEMANDE DE L'UTILISATEUR, ET NON VALIDÉE.** Dans le nouvel extrait, vers **72–76 s**, une grande masse rocheuse masque encore le cadrage pendant la zone de recherche / révélation. Cette observation est compatible avec l'occultation déjà documentée mais ne permet pas d'identifier avec certitude le mesh responsable. Ne pas recommencer des corrections de la grotte, du précipice ou d'A15 à l'occasion du travail F01 / sous-titres. Reprendre ultérieurement la recherche de l'obstacle précis dans Unreal et les critères physiques déjà consignés.


## Réouverture ciblée A15 — caméra lisible (19/09/2026)

À la demande explicite de l'utilisateur, le périmètre F03 est réouvert **pour le trajet de caméra de la grotte**, pas pour changer le relief, les trajets de la famille ni le rocher de convergence F07. Commits du générateur : `8d6d148` (nouvelle progression de caméra autour de la lèvre extérieure, puis dans l'axe réel de l'ouverture), `c2e2df9` (contrôles 3D de dégagement), `24a9349` (retrait du test de rayon purement XY qui bloquait aussi une caméra passant au-dessus d'un rocher). Les deux masses d'occultation depuis les femmes et la géométrie de la cavité sont conservées : il ne faut PAS supprimer un masque physique pour obtenir un plan clair.

**Correction éditoriale :** A15 utilise désormais des jalons lisibles de caméra — vue extérieure, contournement du relief, arrivée à la bouche, entrée au centre du couloir, découverte de Thomas — au lieu de conserver un objectif dirigé vers l'intérieur d'un rocher lors du virage. Le mouvement est continu sur la même piste, sans nouvelle coupe, sans changement du temps objectif 18 h, de la durée du master (372 s) ou des 17 pauses.

**Diagnostics ajoutés :** en fin d'approche, le script vérifie un rayon réel depuis l'objectif dans le monde Unreal et une enveloppe conservatrice des meshes statiques de la grotte, y compris si leur collision est désactivée. Le journal nomme l'acteur devant l'objectif lorsqu'un contrôle échoue. Les anciens tests 2D de position de la caméra restent présents ; l'ancien rayon de regard **entièrement 2D** ne sert plus de preuve d'occultation. Ces contrôles ne sont pas une certification de l'image : l'effet d'une masse rocheuse dans le champ complet, la lumière et l'angle depuis les yeux d'Éva et Léa demandent encore une inspection du rendu.

**Test à effectuer sur le nouveau run complet :** partir d'une carte sauvegardée, exécuter `Unreal/previz_polop.py` avec `FAST_CAMERA_ONLY=False`. Pour tester **simultanément caméra ET sous-titres**, veiller à ne PAS avoir `POLOP_F03_GEOMETRY_ONLY=1` dans la console/processus Unreal. Vérifier `complete`, puis regarder un extrait **continu** A12–A15–A17–B1, pas uniquement des captures isolées : la caméra doit conserver du paysage lisible dans son contour et ne pas traverser une roche, tout en laissant l'entrée masquée aux femmes jusqu'à A15. En cas de blocage de génération, relever le premier message `F03 A15 ...` du même run, qui identifie désormais l'obstacle candidat. **F03 non validée avant visionnage et accord de l'utilisateur.**
