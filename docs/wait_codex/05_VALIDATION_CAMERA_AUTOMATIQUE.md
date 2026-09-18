---
labels: [wait_codex]
status: waiting
priority: P1
---

# Validation automatique de la caméra omnisciente

## Constat

Une trajectoire continue avec des raccords à 0 m peut malgré tout être cinématographiquement mauvaise. Les notes actuelles montrent encore des vitesses très élevées et des occultations.

## Checks à ajouter

Pour chaque image ou échantillon régulier :

- vitesse caméra ;
- accélération ;
- jerk si utile ;
- hauteur au-dessus du Landscape hors grotte ;
- intersection avec murs / rochers / toit ;
- sujet principal dans le champ ;
- taille minimale/maximale du sujet à l'écran ;
- ligne de vue caméra → cible ;
- durée d'occultation ;
- distinction occultation volontaire / accidentelle ;
- vitesse angulaire / rotation excessive.

## Seuils

Ne pas inventer des seuils définitifs. Les rendre configurables et exporter les maxima dans le rapport.

## Sortie

Dans le rapport :
- max vitesse ;
- max accélération ;
- frames problématiques ;
- beat narratif concerné ;
- capture ou timestamp associé.

## Règle

Le validateur ne doit pas réécrire automatiquement la vérité physique pour faire passer la caméra.
