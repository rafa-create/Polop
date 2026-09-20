# Synchronisation de la Bible POLOP vers Google Drive

- Source canonique : `Script_POLOP.md` (branche `main`).
- Dossier : https://drive.google.com/drive/folders/1A5LpnJh_c7cPe0xprY_r9jDFowu48tLc
- Google Doc existant : https://docs.google.com/document/d/1-3JmmVB0da-eE-ewTSjAVzANDJA6udn_lmNIEe995z4/edit
- PDF : `Script_POLOP.pdf`, créé puis actualisé sur place dans ce dossier.
- Workflow : `.github/workflows/sync-script-drive.yml`.
- Conversion : `scripts/sync_script_drive.py`; le PDF est exporté depuis le Google Doc.

## Étape manuelle indispensable : autorisation OAuth

La connexion Google Drive dans ChatGPT ne se transmet **pas** à GitHub Actions. Pour utiliser **ton propre compte Google**, créer dans Google Cloud un projet OAuth, activer les APIs **Google Drive** et **Google Docs**, configurer l'écran de consentement et créer un identifiant OAuth de type **Application Web**. Pour obtenir un jeton de renouvellement via Google OAuth 2.0 Playground, ajouter `https://developers.google.com/oauthplayground` aux URI de redirection autorisées du client OAuth, puis dans les paramètres du Playground activer « Use your own OAuth credentials » et saisir les identifiants de ce client. Autoriser le scope `https://www.googleapis.com/auth/drive` depuis le compte qui peut modifier le dossier et le document, puis échanger le code d'autorisation contre un `refresh_token` (accès hors ligne).

Dans le dépôt GitHub, ouvrir **Settings → Secrets and variables → Actions → New repository secret** et ajouter séparément :

- `GOOGLE_CLIENT_ID` : identifiant client OAuth ;
- `GOOGLE_CLIENT_SECRET` : secret client OAuth ;
- `GOOGLE_REFRESH_TOKEN` : jeton de renouvellement du compte Google autorisé.

**Ne jamais** placer les trois valeurs dans le code, dans une issue GitHub, un journal Actions ou une conversation. Les identifiants OAuth Playground doivent être ceux de ton propre projet Google, non ceux du Playground.

Si l'application OAuth externe reste en mode **Testing**, les jetons de renouvellement avec scope Drive peuvent expirer après 7 jours : configurer correctement son mode de publication et ses utilisateurs autorisés avant de compter sur une synchronisation durable. L'accès accordé au scope Drive permet d'accéder à bien plus que ce dossier ; protéger soigneusement les secrets, restreindre les personnes pouvant modifier la branche principale et révoquer les jetons si besoin.

## Première exécution et contrôle

1. Dans **Actions → Synchroniser la Bible vers Google Drive → Run workflow**, lancer une publication initiale.
2. Vérifier que l'exécution est verte, que le Google Doc « Script » reflète le script canonique et qu'un seul `Script_POLOP.pdf` se trouve dans le dossier.
3. Modifier ensuite uniquement `Script_POLOP.md` sur `main` : un nouveau commit doit mettre à jour les mêmes deux fichiers. Les commits ne modifiant pas ce script ne déclenchent pas la synchronisation automatique.

Si un secret manque, l'Action échoue explicitement **avant d'écrire sur Drive**. Si le Google Doc n'appartient plus au dossier configuré, le script refuse aussi de publier. Les changements effectués directement dans Google Docs seront remplacés au prochain passage ; modifier la Bible dans GitHub uniquement.

### Limites

Le document convertit le texte et les titres Markdown simples ; la typographie Markdown complexe n'est pas entièrement reproduite. Le PDF est exporté du document Google Docs. Les commentaires ou modifications manuelles dans le corps de ce document ne sont pas considérés comme source canonique.
