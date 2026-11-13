# Journal des versions

## 0.4.1 — 13/11/2026

- **Les noms des évènements sont écrits à la plume**, comme sur l'Anneau (même écriture, couleur miel), sur le chemin et en tête de l'étape ouverte. Une étape sans nom garde sa date en caractères droits.
- **Majuscule d'office** à la première lettre d'un nom, qu'il vienne d'un album, d'un dossier ou de toi ; le reste du nom n'est pas touché.

## 0.4.0 — 13/11/2026

- **Les personnes viennent de carnet.** Avec un jeton réglé (`SILLAGE_CARNET_JETON`, le même que `CARNET_JETON_SILLAGE` dans carnet 2.15), la liste d'ouverture est celle des fiches de carnet liées à une personne d'Immich, les proches d'abord, sous le nom de la fiche. Les autres personnes nommées d'Immich se trouvent par la recherche (« hors carnet »). Une fiche liée à une personne masquée dans Immich s'ouvre quand même. La date de naissance reste celle d'Immich ; une personne décédée n'affiche plus d'âge.
- **Immich en secours** : si carnet ne répond pas ou refuse le jeton, la liste est celle des personnes nommées d'Immich, et l'écran le dit.
- L'écran « Connexion » a une tuile carnet. Sillage n'écrit rien dans carnet.
- Tests : 27 du serveur, 12 d'écran.

## 0.3.0 — 13/11/2026

- **Corrections**, gardées dans Sillage (rien n'est écrit dans Immich). Sur une étape, par le crayon : la nommer, rendre le nom d'origine, la masquer. Sur une photo ouverte en grand : en faire la photo phare, la retirer du chemin, « ce n'est pas cette personne ». En bas du chemin, « Tes corrections » montre les étapes masquées et les photos mises de côté, avec « Remettre ». Les corrections sont rattachées à l'empreinte du fichier : elles survivent à la migration, qui change l'identifiant des photos.
- **Noms d'étapes.** Le nom vient de l'album le plus fréquent parmi trois photos de l'étape (la photo phare, la première, la dernière), et plus seulement de la photo phare ; une photo isolée cherche aussi son album. Un dossier qui ne dit rien (nom d'appareil, « DCIM », dossier fourre-tout) n'est plus pris pour un nom ; `SILLAGE_DOSSIERS_MUETS` allonge la liste. Une étape nommée à la main est un temps fort.
- **Raconter** : le récit du chemin, écrit par gabarit à partir des étapes visibles — une phrase par étape nommée (date, âge, nom), les autres comptées. Il se relit, se corrige, se garde et se copie ; « Repartir du chemin » le refait.
- **Le trait s'anime** : il se remplit à mesure qu'on descend, et les étapes apparaissent en entrant dans l'écran. Coupé si l'appareil demande moins d'animations.
- Les photos lues dans Immich sont gardées dix minutes : une correction recalcule le chemin sans rien relire.
- Tests : 25 du serveur, 12 d'écran.

## 0.2.0 — 13 novembre 2026
- **Connexion commune.** Connecté à l'Anneau, on n'a plus à se connecter ici : l'appli accepte le cookie « maison_session » que l'Anneau pose, quand elle est servie par la même adresse que lui. Le cookie est signé avec le mot de passe commun : une appli qui a un autre mot de passe continue de demander le sien. Il vaut trente jours, ou jusqu'au changement du mot de passe ; « Se déconnecter » le retire du navigateur.

## 0.1.0 — 13/11/2026

Première version. Liste des personnes nommées d'Immich, chemin d'une personne en étapes et chapitres d'âge, temps forts, étape ouverte avec galerie et photo en grand. Lecture seule d'Immich, images servies derrière le mot de passe.
