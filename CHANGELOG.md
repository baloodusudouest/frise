# Journal des versions


## 0.10.1 — 14 novembre 2026
- **Sillage passe en lavande crépuscule** (`#a98fd8`, le miel doré avant), icône comprise. L'or est gardé pour l'Anneau : carnet, Sillage et l'Anneau avaient trois ors voisins. Dans la frise de plusieurs invités, le quatrième invité prend l'ancien miel (sa lavande était trop proche des moments ensemble, qui suivent la couleur de Sillage).

## 0.10.0 — 13/11/2026

- **Noms d'étapes plus propres** (vus sur ta photothèque) : l'année en tête d'un album part (« 2007 - Soirée class » → « Soirée class »), comme pour les dossiers. Un lot de numérisation (« 1998 Numérisation … », « Scans … ») n'est plus pris pour un nom : ses scans datés au mois se réunissent par année.
- **Les vidéos se lisent** dans la photo ouverte en grand (propriétaire seulement), lues par morceaux dans Immich.
- **Les vignettes sont gardées sur le disque** de Sillage (`/data/vignettes`, 500 Mo au plus, réglable par `SILLAGE_CACHE_MO`, 0 pour couper) : une vignette déjà vue ne redemande plus Immich, même après un redémarrage. Les moins récemment servies partent en premier.
- **Tuile « À vérifier »** sur la liste : les personnes sans date de naissance dans Immich (leur chemin est rangé par année au lieu de l'âge), d'un toucher.
- Tests : 38 du serveur, 21 d'écran.

## 0.9.0 — 13/11/2026

- **Moins d'étapes, plus parlantes** (vu sur une vraie frise de 333 étapes, dont « Apéro » des dizaines de fois) :
  - les étapes du même nom à moins de deux mois d'écart n'en font qu'une, même si d'autres passent entre elles : « Apéro · 8 janvier – 5 mars 2021 · 3 fois » ;
  - les scans sans nom datés au 1er du mois se réunissent par année : « 1998 · 9 photos ».
- Partout : ton chemin et la page des invités. Nommer, masquer ou choisir la photo phare d'une étape réunie la touche toute entière.
- Tests : 34 du serveur, 18 d'écran.

## 0.8.0 — 13/11/2026

- **Page d'invité : la photo phare s'ouvre en grand** d'un clic ou d'un toucher, avec le nom et la date de l'étape ; fermeture par la croix, un clic à côté ou Échap. Seules les photos phares, comme avant : les autres photos de l'étape restent réservées au propriétaire.
- Côté Home Assistant (template `chambre_photo` v2.2) : un lien « Ouvrir en grand ↗ » sous la carte ouvre la page d'invité dans un nouvel onglet.

## 0.7.0 — 13/11/2026

- **Plusieurs invités : une seule frise en couleurs.** Les moments où ils sont ensemble (miel), et pour chacun, dans sa couleur, ses photos seul ou avec les hôtes de la maison. Une photo où il y a quelqu'un d'autre n'y entre pas. Par décennies du calendrier ; une légende (● Camille ● Hugo ● Ensemble) et le prénom sur chaque carte. Plus d'onglets « chacun son chemin ».
- **Hôtes de la maison**, réglés dans Sillage (Réglages, choisis parmi les personnes d'Immich). Sans hôte, chaque invité ne garde que ses photos seul.
- **Page d'invité sans titre** : une ligne (« Votre chemin ensemble »), la légende, la bascule, et la frise tout de suite dessous — pensé pour la carte de 300 px des chambres.
- Tests : 33 du serveur, 18 d'écran.

## 0.6.0 — 13/11/2026

- **Onglet « Chambres »** : les pages que Home Assistant a préparées pour les chambres d'amis, dès qu'un séjour y est programmé. Pour chaque chambre : les invités, les dates, les noms qu'Immich ne connaît pas, et l'aperçu de la page telle que la verra le tableau de bord de la chambre. Lecture seule : c'est Home Assistant qui crée et retire les pages.
- `POST /ha/sejour` accepte la date d'arrivée (`du`, facultative, AAAA-MM-JJ). La changer garde le même lien. Package HA `sillage_invites.yaml` v1.3.
- Tests : 33 du serveur, 18 d'écran.

## 0.5.0 — 13/11/2026

- **Vue des invités.** Une page sans mot de passe, `/invite/<jeton>`, faite pour le tableau de bord d'une chambre d'amis. Home Assistant la prépare au début du séjour : `POST /ha/sejour` (en-tête `Authorization: Bearer <SILLAGE_JETON_HA>`) avec la chambre, les noms des invités (quatre au plus) et le dernier jour. Sillage cherche chaque nom parmi les personnes nommées d'Immich (à l'identique, puis sans accents ; un homonyme n'est pas pris) et rend le chemin de la page. Le lien vaut jusqu'au lendemain du dernier jour, à midi ; un nouveau séjour dans la chambre donne un nouveau lien et efface l'ancien. Sans nom, la chambre est vidée.
- **Ce que voit l'invité** : son chemin, temps forts d'abord (bascule « Tout »), avec la photo phare de chaque étape. Ni Raconter, ni photos en grand, ni corrections, ni « Ouvrir dans Immich ». Seules les photos phares passent par le lien.
- **Plusieurs invités** : leur chemin commun (photos où ils sont ensemble), découpé par décennies (« Années 2010 »). Sans photo commune, le chemin de chacun, en onglets. Personne de trouvé, ou personne sans photo : un mot d'accueil.
- **Toujours sombre**, comme les autres applis, même sur un appareil réglé en clair.
- Tests : 32 du serveur, 16 d'écran.

## 0.4.3 — 13/11/2026

- **Un nom de dossier ne perd plus son nombre.** Sillage retirait tous les chiffres en tête du nom, pas seulement la date : « 2004-04-01 50 ans de mariage… » devenait « ans de mariage… ». Seule une vraie date est retirée maintenant (année, année-mois, année-mois-jour, jour-mois-année, ou une période de deux dates).

## 0.4.2 — 13/11/2026

- **La croix d'une photo ouverte en grand se ferme d'un clic au centre.** Le compteur (« 2 / 40 »), remonté en haut à la 0.3.0, passait par-dessus : seul le bas du bouton répondait.
- **« Ouvrir dans Immich »** devient un bouton, avec les autres gestes de la photo. Sans adresse réglée (`SILLAGE_IMMICH_ADRESSE`), le lien vise le même hôte que Sillage sur le port d'Immich (`SILLAGE_IMMICH_PORT`, en http). Ce lien est un geste du propriétaire : une future vue d'invité ne l'aura pas.

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
