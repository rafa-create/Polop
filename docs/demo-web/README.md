# POLOP — Démo web 3D de l'ouverture

Cette **prévisualisation indépendante** propose une esquisse interactive de l'ouverture du manuscrit `Script_POLOP.md` (A0, puis début de A1) : anneau dans la rivière, sortie de l'eau, découverte du relief et arrivée auprès de Thomas, Éva et Léa. La scène 3D, les personnages, les mouvements et le pont sont **provisoires**. Les dimensions, la géographie et les animations ne valent pas validation de la continuité physique du film. Cette démo ne remplace pas le générateur Unreal `Unreal/previz_polop.py`.

## Fichiers

- `index.html` : interface et commandes ;
- `style.css` : mise en page adaptative ;
- `app.js` : décor et animations 3D en Three.js, sans asset Unreal/Blender à installer.

## Lancement

Ouvrir `index.html` via un petit serveur web local (les modules ES ne sont pas garantis en `file://`) :

```sh
python -m http.server 8000 --directory docs
```

Puis ouvrir `http://localhost:8000/demo-web/`. Une connexion Internet est nécessaire pour charger Three.js depuis jsDelivr ; un navigateur récent avec WebGL est requis.

Utiliser **Pause/Reprendre**, **Recommencer**, le curseur temporel, la vitesse de lecture et **Vue libre** (glisser pour tourner, molette pour zoomer). Raccourcis clavier hors contrôles : Espace, R, V. La préférence système « réduire les animations » démarre la démo en pause sur la randonnée.

## Publication GitHub Pages

Sur GitHub, ouvrir **Settings → Pages**, sélectionner **Deploy from a branch**, la branche `main` et le dossier `/docs`, puis enregistrer. L'adresse visée est :

`https://rafa-create.github.io/Polop/demo-web/`

**Important :** le dépôt Polop était privé au moment de l'intégration. Selon l'abonnement GitHub et la configuration Pages, la publication depuis un dépôt privé peut être indisponible, et un site Pages publié peut être publiquement accessible. Vérifier la visibilité et ne publier que les contenus destinés au public. La création des fichiers ne garantit pas à elle seule l'activation ni l'accessibilité du site Pages.
