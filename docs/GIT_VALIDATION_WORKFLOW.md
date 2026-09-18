# Politique Git / validation Unreal

## Principe

Un commit de code n'est pas équivalent à une version validée dans Unreal.

Une version peut être considérée comme **vérifiée** seulement après :

1. exécution réelle dans Unreal ;
2. génération d'un `RUN_ID` ;
3. rapport technique lu ;
4. contrôle visuel demandé effectué ;
5. problèmes connus consignés.

## Manifest de run vérifié

Utiliser `Unreal/VERIFIED_RUN.template.json` comme modèle.

Créer/mettre à jour `Unreal/VERIFIED_RUN.json` uniquement lorsqu'un run a réellement été exécuté et revu.

Ne jamais remplir ce fichier à partir d'une simple inspection statique du code.

## Branches / expériences

Les expérimentations peuvent produire plusieurs commits.

Pour une étape importante, préférer :
- expérimentation ;
- run Unreal ;
- corrections ;
- nouveau run ;
- seulement ensuite déclaration de version vérifiée.

## Preuves locales

Les rapports et captures restent sous `Saved/POLOP/Runs/<run_id>/` et ne sont pas committés par défaut.

Le manifest Git conserve seulement les références nécessaires pour savoir **quel code a réellement été testé**.
