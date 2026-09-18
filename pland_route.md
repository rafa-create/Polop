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
- [ ] Projet Unreal bootstrapable depuis zéro — GitHub issue **#41**.
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

Issue : **#44** (`3d_codex`).

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

Issue : **#43** (`3d_codex`).

## PHASE 4 — Plan-séquence omniscient

Objectif : caméra continue, physique et lisible, sans révélation prématurée.

Automatiser les contrôles :
- vitesse ;
- accélération ;
- obstacles / relief / grotte ;
- visibilité du sujet ;
- occultations volontaires vs accidentelles ;
- rotations excessives.

Issue : **#45** (`3d_codex`).

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

Issue : **#46** (`3d_codex`).

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

1. **#41** — reproductibilité totale depuis Git / autre machine ;
2. **#44** — vérité physique fermeture / anneau / mousqueton / grotte ;
3. **#47** — séparation réelle Thomas inversé / Éva-Léa vers 17h58 et absence de révélation prématurée ;
4. **#43** — personnages reproductibles et coût Sequencer ;
5. **#45** — validation automatique caméra ;
6. **#42** — modularisation ;
7. **#46** — film virtuel complet / polish narratif et visuel.

Les issues #12, #14 et #21 sont des sous-tâches de #44 ; #13 et #29 sont des sous-tâches de #46 ; #32 est une règle transversale de validation 3D.
