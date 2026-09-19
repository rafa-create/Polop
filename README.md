# LA BOUCLE / POLOP

## Source canonique

La bible narrative absolue est **`Script_POLOP.md`**. Les anciennes versions dans `archive/` sont historiques uniquement.

## Projet de référence — un seul dépôt

**Dépôt officiel :** `https://github.com/rafa-create/Polop.git`, branche `main`. Sur l'ancien PC, le dossier actif est `E:/perso/polop/Polop-git/` ; sur le nouveau PC, utiliser la racine du clone officiel, quel que soit son emplacement.

**Lire d'abord [AGENTS.md](AGENTS.md)** : règles opérationnelles pour Codex (sources à modifier, lancement Unreal, Git/Git LFS, protection des animations historiques et résultats générés).

- Projet Unreal à ouvrir : **`polop.uproject`** (à la racine), avec UE **5.8.2** (version testée).
- Carte de démarrage versionnée : `Content/Main.umap` = `/Game/Main`, via Git LFS.
- **Seul générateur actif à modifier et à lancer : `Unreal/previz_polop.py`**, via Unreal > Tools / Outils > Execute Python Script.
- Configuration portable à maintenir sur Git : `polop.uproject`, `Config/Default*.ini`, `.gitignore`, `.gitattributes`.
- Les runs locaux `Content/POLOP/Generated_*/` et `Saved/POLOP/Runs/` ne sont **pas** des sources à commiter.

## État de reproductibilité — 19 septembre 2026

Bootstrap publié sur `main` : ouverture UE 5.8.2 et génération complètes vérifiées dans `Polop-git` (run `20260919_084218_028677`, rapport MASTER V10 : **35 OK, 0 WARN, 0 FAIL, 0 BLOCKER**). Un clone local séparé a téléchargé `polop.uproject` et `Main.umap` via LFS. **Le générateur n'a pas été relancé dans ce clone et aucun essai sur un deuxième PC n'a été effectué.** Ne pas présenter la portabilité intermachines comme démontrée.

L'ancien dossier `E:/perso/polop/polop/` reste une **sauvegarde du WIP Unreal local non synchronisé**, notamment les animations articulées ; ne pas le supprimer avant inventaire et migration sélective. Voir [l'environnement et la reprise sur un autre PC](docs/ENVIRONNEMENT_REPRODUCTIBILITE.md).

## Documentation et travaux

- `Unreal/README_PREVIZ.md` : fonctionnement du générateur, rapports, limites narratives ;
- `docs/ENVIRONNEMENT_REPRODUCTIBILITE.md` : prérequis, dossiers, installation, Git LFS ;
- `pland_route.md` : ordre des prochains chantiers ;
- GitHub Issues : travaux nécessitant Codex/Unreal, après clôture du jalon bootstrap #41.

Toujours séparer la **vérité physique du monde** de la **mise en scène** : une caméra peut cacher une information narrative, jamais un bug physique.
