# POLOP — Unreal Previz

## Script actif unique

À partir de maintenant, un seul script doit être lancé :

- `Unreal/previz_polop.py`

Tous les anciens scripts de construction, validation et animation sont archivés dans `Unreal/old/`. Le script master embarque actuellement la géographie V11 et l'animation V05 validées comme base de travail.


## Master V04 — collision Landscape différée

Le log V03 a confirmé que le nettoyage caméra fonctionne : V11 annonce `CAMERAS REVIEW : 0`. Le blocage suivant venait uniquement des raycasts de validation juste après l'import automatique du heightmap : UE 5.8 peut avoir mis à jour le rendu du Landscape avant que son heightfield Chaos/collision soit immédiatement requêtable.

V04 :

- conserve V11 sans aucune caméra de revue ;
- appelle `force_layers_full_update()` après l'import du heightmap ;
- force les Collision Mip Levels à 0 pour la préviz ;
- tente plusieurs chemins de reconstruction de collision quand ils sont exposés à Python ;
- utilise `TraceTypeQuery.ECC_VISIBILITY` au lieu de l'ancienne entrée dépréciée ;
- ne bloque plus le pipeline si **les trois raycasts sont tous indisponibles** juste après l'import, à condition que le Landscape ait toujours ses composants et le transform V11 correct ;
- continue alors vers Animation V05, qui reste l'unique autorité caméra ;
- continue de bloquer si un raycast existe mais révèle une hauteur incompatible avec V11.

Le log indique désormais `Mode validation terrain : STRONG`, `PARTIAL` ou `NO_COLLISION`. `NO_COLLISION` signifie que le rendu/import a été accepté mais que la collision n'était pas encore requêtable au moment exact du contrôle ; ce n'est plus traité comme une preuve que la montagne est absente.

## Master V05 — diagnostic automatique de la validation Animation V05

Le pipeline atteint maintenant complètement Animation V05 et confirme que toutes les caméras POLOP actives sont des `PZ_ANIM_*`. V05 historique peut toutefois écrire `AUTO-VALIDATION : FAIL` sans détailler les checks dans le Journal de sortie.

Master V05 lit donc automatiquement `Saved/POLOP/ANIMATION_V05/validation/validation_animation_v02.json`, imprime chaque check en échec sous la forme `VALIDATION FAIL : ...`, puis crée aussi des alias plus clairs :

- `validation_animation_v05.json`
- `validation_animation_v05.txt`

Cela évite d'avoir à chercher manuellement le fichier de validation après chaque exécution.

## Master V06 — POV Thomas inversé stabilisé

Le run V05 atteint maintenant correctement Animation V05 et confirme l'autorité caméra : **11 caméras POLOP actives, toutes `PZ_ANIM_*`**. Le seul échec restant était `pov_eye_offsets_reasonable`, avec Thomas inversé à 15,63 cm minimum du centre des yeux pendant l'approche de la caverne.

Master V06 corrige la cause au lieu d'abaisser le seuil :

- la direction 3D continue à piloter le regard de la caméra ;
- le décalage physique du POV (38 cm avant + 12 cm latéral) est désormais calculé dans le plan XY ;
- une forte pente ne peut donc plus écraser le décalage vers zéro autour de la tête ;
- la petite compensation verticale est limitée à ±8 cm ;
- les fichiers de validation portent enfin `validation_animation_v05.json/txt` au lieu de l'ancien nom V02.

La caméra de Thomas inversé à environ Z=-1000 m au tout début est volontaire : avant 17h00 objectif, son proxy est caché sous le niveau. À partir de 17h00/2 s Sequencer, sa piste POV prend les positions animées normales.

Après exécution, attendre `AUTO-VALIDATION : OK` et `VALIDATION ANIMATION V05 : OK | 0/19 check(s) en échec.`.

## Master V07 — POV anti-occlusion

Le run V06 est techniquement valide (`AUTO-VALIDATION : OK`, `0/19`) mais une capture vers 3,7 s montrait encore un proxy du groupe énorme sur le bord droit du POV Thomas normal.

V07 ne touche ni au Landscape, ni aux trajectoires, ni au timing. Il corrige uniquement la lecture subjective :

- le POV conserve son avance XY stable issue de V06 ;
- lorsqu'un autre personnage passe à moins d'environ 1,35 m de la caméra, le script teste plusieurs positions d'épaule à gauche et à droite ;
- il choisit automatiquement la position qui maximise la distance au proxy le plus proche, avec une pénalité pour éviter des écarts excessifs ;
- le décalage reste normalement de 14 cm et peut monter ponctuellement jusqu'à 78 cm uniquement quand le groupe est compact ;
- les quatre POV passent de 20 mm à **28 mm**, pour réduire l'effet grand-angle et les personnages géants en très proche avant-plan ;
- géographie, personnages et animation restent strictement identiques.

Contrôle visuel prioritaire après exécution : **3–4 s** pour le groupe, puis **60–61 s** pour Thomas inversé dans la caverne, et **62 s** pour le contact.

## Compatibilité avec un ancien setup

Le master est prévu pour être relancé sur le niveau actuel sans nettoyage manuel :

- suppression des anciens Actors `PZ_*` ;
- détection de la coquille Landscape existante ;
- suppression des Landscapes supplémentaires d'anciens essais ;
- remise du Landscape à `Location X=100800 Y=0 Z=0` ;
- remise à `Scale X=200 Y=200 Z=100` ;
- génération du heightmap V11 ;
- réinjection automatique du heightmap dans le Landscape ;
- V11 = géographie/blockout uniquement, sans caméra ;
- suppression de sécurité des anciennes caméras POLOP hors animation ;
- Animation V05 = seules caméras, POV et Sequencer.

### Prérequis unique

Il doit rester au moins **une coquille Landscape 1009x1009** dans le niveau. Unreal Python sait écraser le heightmap d'un Landscape existant mais la création fiable d'un Landscape complet depuis zéro n'est pas utilisée par ce pipeline.

Le setup actuel du projet possède déjà cette coquille : ne la supprime pas avant de lancer le master.

Si plusieurs Landscapes existent, le master conserve le candidat le plus proche du transform attendu et tente de supprimer les autres. Si la résolution détectée n'est pas 1009x1009, le script s'arrête au lieu de resampler silencieusement.

## Exécution

Dans le Journal de sortie / console Python Unreal :

`py "CHEMIN_COMPLET/previz_polop.py"`

Le script doit afficher des lignes commençant par `POLOP MASTER :`.

À la fin :

- ouvrir `LS_POLOP_ANIMATION_V05` ;
- contrôler les POV, notamment Thomas inversé ;
- contrôler la caverne vers 60–62 s ;
- enregistrer le niveau avec Ctrl+S si le résultat est validé.

## Historique

Les scripts précédents restent disponibles dans `Unreal/old/` uniquement pour comparaison et diagnostic. Ils ne doivent plus être exécutés dans le workflow normal.
