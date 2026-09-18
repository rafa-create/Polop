# POLOP — Unreal Previz

## Script actif unique

À partir de maintenant, un seul script doit être lancé :

- `Unreal/previz_polop.py`

Tous les anciens scripts de construction, validation et animation sont archivés dans `Unreal/old/`. Le script master embarque actuellement la géographie V11 et l'animation V05 validées comme base de travail.

## Compatibilité avec un ancien setup

Le master est prévu pour être relancé sur le niveau actuel sans nettoyage manuel :

- suppression des anciens Actors `PZ_*` ;
- détection de la coquille Landscape existante ;
- suppression des Landscapes supplémentaires d'anciens essais ;
- remise du Landscape à `Location X=100800 Y=0 Z=0` ;
- remise à `Scale X=200 Y=200 Z=100` ;
- génération du heightmap V11 ;
- réinjection automatique du heightmap dans le Landscape ;
- reconstruction de la géographie puis de l'animation, des POV et du Sequencer.

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
