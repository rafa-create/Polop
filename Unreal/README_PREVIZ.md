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
