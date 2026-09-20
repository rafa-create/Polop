# Feuille de route actuelle — LA BOUCLE / POLOP

> Source narrative canonique : `Script_POLOP.md`
>
> Workflow actuel : **affinage 3D → génération du film virtuel → revue spectateur → corrections → nouvelle génération**, en boucle jusqu'à validation explicite, puis verrouillage Unreal et tournage réel.

Cette feuille remplace les anciennes étapes V8 devenues historiques. Le projet dispose déjà d'un terrain procédural, de trajectoires A/B, d'une timeline objective, de POV de contrôle, d'un montage omniscient de travail et de rapports automatiques.

## PHASE 1 — Reproductibilité

Objectif : repartir du Git sur un autre ordinateur sans dépendre d'un ancien projet local.

- [x] Bible narrative unique : `Script_POLOP.md`.
- [x] Script Unreal actif unique : `Unreal/previz_polop.py`.
- [x] Runs générés isolés par `RUN_ID`.
- [x] `.gitignore` Unreal.
- [x] `.gitattributes` préparé pour Git LFS.
- [x] Documentation de l'environnement reproductible.
- [x] Projet Unreal de démarrage versionné (`polop.uproject`, `Config/Default*.ini`, `Content/Main.umap` via LFS), ouverture et run local réussis — issue **#41** clôturée sur ce **jalon pratique accepté** le 19/09/2026.
- [x] Nouveau clone local depuis GitHub : `.uproject` et `Main.umap` correctement récupérés via LFS.
- [ ] Run depuis ce clone isolé / essai sur un autre PC : **non effectués, non demandés pour ce jalon**. À revalider si une nouvelle machine révèle un problème.

**Preuve :** UE 5.8.2, run local `20260919_084218_028677`, rapport `OVERALL: OK` (35 OK / 0 WARN / 0 FAIL / 0 BLOCKER). La carte de travail et la séquence omnisciente ont été contrôlées visuellement. Le succès n'est pas une garantie de portabilité intermachines ni d'adaptation cinématographique finale. Lire `AGENTS.md` et `docs/ENVIRONNEMENT_REPRODUCTIBILITE.md`.

**Critère pratique accepté :** `git clone → ouvrir polop.uproject → lancer Unreal/previz_polop.py → obtenir un run + rapport`, sans préparation manuelle du Landscape.

## PHASE 2 — Vérité physique

Pendant les itérations d'affinage 3D et de revue spectateur, contrôler :

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

## PHASE 3 — Personnages et performance (intégrés au bootstrap #41)

Déjà acquis :
- poses dérivées du temps objectif ;
- personnages articulés de prévisualisation ;
- lecture normale/inversée dérivée du même état monde.

À fiabiliser :
- dépendance aux assets tutoriels Unreal ;
- fallback vers proxies ;
- coût du sampling image par image.

La disponibilité des assets, le fallback proxies et un relevé léger du coût Sequencer sont intégrés à **#41**. Ne pas lancer une optimisation lourde du bake sans problème mesuré.

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

Si la revue révèle un défaut : correction 3D / mise en scène → nouvelle génération complète → nouvelle revue spectateur. Répéter autant que nécessaire ; verrouiller Unreal seulement après validation explicite.

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

## État actuel — boucle d'affinage 3D et revue spectateur

**Étape active : affiner la prévisualisation 3D, la soumettre à une revue spectateur, corriger, puis recommencer jusqu'à validation explicite.** La connexion du plan-séquence a été validée par l'utilisateur ; cela ne vaut pas validation du film virtuel complet, de la géographie, de la causalité ni de la compréhension du spectateur. Le prochain rendu sert à contrôler la grotte et le précipice après le correctif géographique `fd15fd5` (issues #52 et #53).

**Boucle de travail obligatoire, sans passage automatique au tournage :**

1. **Affinage 3D / vérité physique et mise en scène** : corriger un défaut identifié, sans déplacer la causalité pour masquer un problème de caméra ou de décor. Préserver la Bible et le plan-séquence continu.
2. **Génération du film virtuel complet** : conserver l'identifiant du run et vérifier que les modifications se retrouvent dans le rendu, pas seulement dans le code ou les rapports.
3. **Revue spectateur** : confronter le rendu à trois lectures — naïve (compréhension sans explication), puzzle (relecture des indices) et causale/physique (temps objectif, trajectoires, géographie et contacts).
4. **Décision documentée** : relever les défauts observés et mettre à jour les issues concernées. Si un critère échoue ou demeure non vérifié, revenir à l'étape 1 et régénérer. Ne fermer une issue que lorsque **ses propres critères** sont validés ; une caméra continue n'établit pas la validité du pont, de la grotte ou de l'anneau.
5. **Verrouillage de la prévisualisation (« lock Unreal »)** : seulement après validation explicite du film virtuel et des trois lectures, avec les éventuels écarts résiduels acceptés et documentés. **Alors seulement préparer le tournage réel (phase 7).**

### Ordre de traitement dans la boucle actuelle

- **En cours :** revue du nouveau rendu grotte/précipice (#52, #53). Le correctif de géométrie publié ne constitue pas à lui seul une validation Unreal.
- **Ensuite :** lisibilité des rives, du pont et du flanc (#51), geste du mousqueton (#55), puis rencontre et occultations de 17 h (#49, #56, #62).
- **Puis :** trajectoire et topographie de l'anneau (#63), effets du temps inversé (#54), ouverture et décor (#60, #61), jeu familial (#50), cartons et rythme (#57, #58).
- **En parallèle, sans changer le canon :** piste d'évolution scénaristique du galet (#64). Les contacts précis de l'anneau à 17 h et 18 h restent différés par décision de l'utilisateur.

L'ordre peut évoluer selon les défauts révélés par chaque nouveau rendu. **La continuité caméra est déjà validée par l'utilisateur** ; ne pas rouvrir ce chantier sans nouvel élément. Les phases 2 à 6 ci-dessus sont désormais des axes de vérification **itératifs**, pas des portes successives à franchir une seule fois.

### Passage au tournage

Le tournage réel (phase 7) ne démarre pas au terme d'un nombre fixé d'itérations : il dépend du **feu vert explicite après la revue spectateur et le verrouillage de la prévisualisation**. La préparation technique du tournage peut être documentée en amont, sans considérer la simulation comme approuvée.
