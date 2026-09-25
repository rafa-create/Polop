# Démo animatique A0 — La rivière

Prototype autonome, **non canonique**, de l'ouverture A0 du film décrite dans `Script_POLOP.md`.

## Voir la démo

1. Depuis cette branche, récupérer `Video_demo/demo_A0_riviere.html`.
2. Ouvrir le fichier avec un navigateur récent. Aucune installation, connexion réseau ni ressource externe n'est nécessaire.
3. Utiliser **Pause / Lire**, **Revoir** ou la barre de progression (30 secondes). La touche Espace fonctionne hors des boutons.

## Ce que montre le prototype

- 0–9 s : travelling illustratif sous l'eau, fond de rivière et anneau qui bouge brièvement contre la pierre, sans insert dramatique.
- 9–13 s : passage graphique de l'eau à la lumière extérieure.
- 13–21 s : révélation de la vallée et de la montagne.
- 21–30 s : approche du sentier et des trois silhouettes (Thomas, Éva, Léa).

L'objectif est de discuter de l'ambiance et du rythme **avant** de toucher à l'animation 3D.

## Limites et périmètre

- Animatique **2D stylisée et silencieuse**, pas un export vidéo ni une séquence Unreal. Les silhouettes sont schématiques ; aucun asset de personnages WIP n'a été déplacé ou remplacé.
- La sortie de l'eau utilise un fondu graphique. Ce n'est **pas** la continuité physique d'un vrai plan-séquence, exigée par le scénario. La géographie et les déplacements ne sont pas validés.
- Le prototype n'utilise pas `Unreal/previz_polop.py`, ne modifie pas `Content/Main.umap`, `polop.uproject` ni aucun dossier de run généré.
- Vérification effectuée ici : présence de la structure et des éléments narratifs dans le fichier source ; **aucune lecture visuelle dans un navigateur, aucun test Unreal et aucun rendu vidéo n'ont été effectués**.

Pour une prévisualisation 3D conforme au workflow du dépôt, partir du clone officiel synchronisé, ouvrir UE 5.8.2 et utiliser exclusivement `Unreal/previz_polop.py` selon `AGENTS.md` et `Unreal/README_PREVIZ.md`.
