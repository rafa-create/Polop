---
labels: [wait_codex]
status: waiting
priority: P0
---

# Vérité physique — anneau, mousqueton, fermeture, grotte

## Principe

Le décor et la caméra peuvent **cacher une information narrative**, mais ne doivent jamais cacher un bug physique.

Avant davantage de polish caméra, rendre les événements suivants explicites dans la simulation :

- anneau ;
- trajet de l'anneau ;
- interaction au contact 18h00 ;
- mousqueton / geste canonique ;
- passage de Thomas inversé sur le pont ;
- fermeture vers 17h00 ;
- coexistence des deux occurrences de Thomas ;
- entrée/sortie réelle de la grotte ;
- occultation de la fermeture uniquement si la géométrie et les worldlines sont déjà cohérentes.

## Modèle

À une heure objective donnée, le monde possède un seul état physique.

Toute lecture normale/inversée doit dériver de ce même état.

## Rapport automatique attendu

Ajouter des checks :
- position anneau par temps clé ;
- état mousqueton par temps clé ;
- distance worldline Thomas normal/inversé ;
- contact exact à 18h00 ;
- passage B→A du Thomas inversé ;
- aucune collision personnage/rocher ajouté pour l'occultation ;
- grotte accessible physiquement dans les deux sens concernés.

## Validation

Masquer toutes les caméras et vérifier le monde seul.
Si la causalité fonctionne encore, la couche vérité est correcte.
