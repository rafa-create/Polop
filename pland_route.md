# Feuille de route actuelle — LA BOUCLE / POLOP

> Source narrative canonique : `Script_POLOP.md`
>
> Workflow : **script → vérité physique → prévisualisation Unreal → validation → tournage réel**.

Cette feuille remplace les anciennes étapes V8 devenues historiques. Le projet dispose déjà d'un terrain procédural, de trajectoires A/B, d'une timeline objective, de POV de contrôle, d'un montage omniscient de travail et de rapports automatiques.

## PHASE 1 — Reproductibilité

Objectif : repartir du Git sur un autre ordinateur sans dépendre d'un ancien projet local.

- [x] Bible narrative unique : `Script_POLOP.md`.
- [x] Script Unreal actif unique : `Unreal/previz_polop.py`.
- [x] Runs générés isolés par `RUN_ID`.
- [x] `.gitignore` Unreal.
- [x] `.gitattributes` préparé pour Git LFS.
- [x] Documentation de l'environnement reproductible.
- [ ] Projet Unreal bootstrapable depuis zéro — `docs/wait_codex/01_BOOTSTRAP_UNREAL_REPRODUCTIBLE.md`.
- [ ] Smoke test sur une deuxième machine.

**Critère de sortie :** `git clone → ouvrir projet → lancer previz_polop.py → obtenir un run + rapport`, sans préparation manuelle cachée.

## PHASE 2 — Vérité physique

Avant davantage de polish caméra, verrouiller :

- terrain / pont / flanc / routes A et B ;
- entrée et volume de la grotte ;
- worldline Thomas normal / inversé ;
- anneau ;
- mousqueton ;
- fermeture à 17h00 ;
- état physique unique du monde pour chaque heure objective ;
- interactions inversées indispensables.

Fiche : `docs/wait_codex/04_VERITE_PHYSIQUE_ANNEAU_MOUSQUETON.md`.

**Critère de sortie :** les causalités fonctionnent même si toutes les caméras sont masquées.

## PHASE 3 — Personnages et performance

Déjà acquis :
- poses dérivées du temps objectif ;
- personnages articulés de prévisualisation ;
- lecture normale/inversée dérivée du même état monde.

À fiabiliser :
- dépendance aux assets tutoriels Unreal ;
- fallback vers proxies ;
- coût du sampling image par image.

Fiche : `docs/wait_codex/03_PERSONNAGES_ASSETS_ET_FALLBACK.md`.

## PHASE 4 — Plan-séquence omniscient

Objectif : caméra continue, physique et lisible, sans révélation prématurée.

Automatiser les contrôles :
- vitesse ;
- accélération ;
- obstacles / relief / grotte ;
- visibilité du sujet ;
- occultations volontaires vs accidentelles ;
- rotations excessives.

Fiche : `docs/wait_codex/05_VALIDATION_CAMERA_AUTOMATIQUE.md`.

**Règle :** un raccord à 0 m ne suffit pas à valider une caméra de cinéma.

## PHASE 5 — Film virtuel complet

Ajouter :
- A0 rivière → vallée → montagne → famille ;
- anneau complet ;
- geste du mousqueton ;
- événements naturels réversibles ;
- lumière de travail ;
- musique / son temporaire ;
- jeu minimum ;
- transitions temporelles.

Fiche : `docs/wait_codex/06_FILM_VIRTUEL_COMPLET.md`.

## PHASE 6 — Validation spectateur

Trois lectures obligatoires :
1. spectateur naïf ;
2. spectateur puzzle ;
3. audit causal/physique.

Puis correction → nouvelle simulation → lock Unreal.

## PHASE 7 — Tournage réel

À partir de la prévisualisation verrouillée :
- plan de tournage ;
- storyboard / shot list ;
- découpage technique ;
- repérage réel ;
- VFX ;
- sécurité / cascade ;
- accessoires / continuité ;
- répétitions ;
- tournage.

---

## Architecture à préserver

### COUCHE VÉRITÉ

géographie, temps objectif, positions, causalité, anneau, mousqueton, états physiques.

### COUCHE MISE EN SCÈNE

caméra, focale, rythme, occultation, lumière, son, jeu.

Quand quelque chose ne marche pas à l'image, identifier d'abord **la couche responsable**. Une correction de mise en scène ne doit jamais masquer un défaut de vérité physique.

## Priorité immédiate

1. reproductibilité complète depuis Git ;
2. vérité physique anneau / mousqueton / fermeture / grotte ;
3. seulement ensuite polish caméra.
