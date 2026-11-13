# Reprise — Sillage (ancien nom : Frise)

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (13/11/2026)

- **0.10.0** : `chemin.nom_d_album` (année de tête retirée, lots de numérisation `_LOT` muets, aussi pour les dossiers) ; `app/cache.py` (vignettes sur disque, élagage aux 90 % de la limite tous les 50 écrits) ; `GET /api/video/{id}` en flux (`Immich.flux`, Range transmis) ; tuile « À vérifier » dans `Sillages.svelte`. Revue du 13/11 sur dix chemins de proches : 48 noms d'albums avec l'année en tête, des albums « AAAA Numérisation … » pris pour des noms, 15 % d'étapes sans nom, jusqu'à 6,5 s pour un chemin de 160 étapes. **À vérifier** : la clé d'API de Sillage peut-elle lire les vidéos (`/assets/{id}/video/playback`, droit `asset.view` ou `asset.download` selon la version d'Immich) ? Sinon la vidéo affiche une erreur et l'image reste la vignette.
- **0.9.0** : `chemin.regrouper` (après le nom proposé, avant les chapitres) : même nom proposé à moins de `MEME_NOM` (60 j) → une étape (`fois`) ; sans nom et toutes les photos au 1er du mois → une étape par année (`quand`). La clé de réunion est le nom **proposé** (album, dossier), jamais le nom donné à la main ni le masquage, qui ne sont posés que sur la photo phare. Sonde du 13/11 sur la vraie frise d'un couple (0.8.0) : 333 étapes, 1 139 photos, 37 temps forts ; le chemin commun commence en 2020 → **l'intersection `personIds` d'Immich est confirmée**.
- **0.8.0** : visionneuse de la photo phare dans `Invite.svelte` (état `grande`, dialogue `.grand`). Décision de l'utilisateur : la photo en grand est permise aux invités, la photo phare seulement.
- **0.7.0** : `_ensemble` dans `app/main.py` (commun par `photos_ensemble`, chacun par `photos_de` filtré sur les personnes de la photo ⊆ {invité} ∪ hôtes ; étapes marquées `qui`, clés préfixées). Table `reglages` (clé « hotes »), `GET/PUT /api/reglages`. Le filtre suppose que la recherche d'Immich rend **toutes** les personnes reconnues sur chaque photo (`withPeople`) : à vérifier, sinon des photos avec d'autres gens passeraient. Un visage reconnu mais sans nom compte comme « quelqu'un d'autre ».
- **0.6.0** : onglet « Chambres » (`pages/Chambres.svelte`, `GET /api/chambres`, `Base.invitations`), aperçu par `Invite.svelte` en mode `apercu`. Colonne `du` ajoutée à la table `invites` au démarrage (bases de la 0.5). La date d'arrivée vient de `sejour_debut` (package HA v1.3).
- **0.5.0** : vue des invités (`/invite/<jeton>`, `pages/Invite.svelte`), préparée par Home Assistant (`POST /ha/sejour`, jeton `SILLAGE_JETON_HA`, table `invites` dans `app/base.py`). Chemin commun par `immich.photos_ensemble` (plusieurs `personIds`) et `chemin.calculer(..., decennies=True)`. Package HA : `config/packages/chambres/sillage_invites.yaml` du master doc. Thème toujours sombre. **Rien de cela n'a tourné contre le vrai Immich ni le vrai HA.**
- **0.4.3** : vu sur la vraie photothèque, « ans de mariage … » : la date de tête était retirée par une règle trop large qui mangeait aussi « 50 ». `chemin.sans_date_en_tete` ne retire qu'une vraie date.
- **0.4.2** : croix de la photo en grand recouverte par le compteur (corrigé, test sur trois hauteurs du bouton) ; « Ouvrir dans Immich » en bouton, adresse déduite de l'hôte et de `SILLAGE_IMMICH_PORT`. **Décision : ce lien, comme les corrections, est réservé au propriétaire ; la vue des invités, quand elle existera, ne les montrera pas.**
- **0.4.1** : noms d'évènements à la plume (classe `.plume`, police Tangerine embarquée), majuscule d'office (`chemin.majuscule`). Lisibilité à vérifier sur un vrai iPhone.
- **0.4.0** : personnes de carnet (`_de_carnet`, `_personnes` dans `app/main.py` ; adresse `/sillage/personnes` de carnet 2.15, jeton partagé), Immich en secours. 27 tests du serveur, 12 d'écran. **Jamais essayé contre le vrai carnet.**
- **0.3.0** : corrections (`app/base.py`, table `marques` par empreinte ; `POST /api/chemin/{personne}/marque`), noms d'étapes (trois photos témoins, dossiers muets), « Raconter » (`app/recit.py`, `pages/Recit.svelte`), trait animé (`pages/Chemin.svelte`). 25 tests du serveur, 12 d'écran.
- **0.2.0** : connexion commune avec l'Anneau. **0.1.0** : personnes d'Immich, chemin, étape ouverte.
- Vue sur la vraie photothèque par l'utilisateur (0.2.0). Ses retours : **les noms d'étapes** et **la photo phare ou des photos fausses**, sans détail ni capture. La 0.3.0 y répond par les corrections à la main et par un meilleur choix du nom ; **rien de cela n'a été vérifié sur ses photos**.

## À vérifier sur la vraie installation

- Intersection `personIds` d'Immich : **confirmée** le 13/11/2026 (chemin commun d'un couple qui commence à leur rencontre).
- L'iframe de la chambre : un tableau de bord ouvert en https (Nabu Casa, Funnel) refusera une page Sillage en http. Ouvrir le tableau de bord en local, ou passer Sillage en https.
- Les noms : sortent-ils mieux ? Quels dossiers faut-il ajouter à `SILLAGE_DOSSIERS_MUETS` ?
- La photo phare : si Immich ne rend pas les visages dans la recherche (`withPeople`), c'est la première image du groupe. À regarder avant de retoucher le choix automatique.
- Le temps de lecture : jusqu'à trois lectures d'album par étape (huit de front, gardées dix minutes).
- Le trait animé sur un vrai iPhone.

## Pas encore fait

1. Scans datés « vers … », date de fin, tuile « À vérifier », cache des vignettes sur disque, lecture des vidéos.
2. Un récit plus vivant : refusé pour l'instant (gabarit choisi, rien d'inventé).

## Décisions à ne pas rouvrir sans raison

- Étape = groupe de photos de la personne proches en dates ; l'album la nomme.
- Lecture seule d'Immich ; réglages dans la base de Sillage, rattachés à l'empreinte des fichiers.
- Personnes : carnet d'abord, Immich en secours.
- « Raconter » dans la V1, sobre, avec relecture.
- Vue des invités (0.5.0, 0.8.0) : jeton par séjour, rien que le chemin et les photos phares (ouvrables en grand) ; le propriétaire garde seul corrections, Raconter et Immich.
- Hors V1 : page imprimable, arbre généalogique, vidéo, sillages croisés, « ce jour-là ».
- Technique : celle du dépôt socle.

## Ce que la première sonde (11/11/2026) avait montré

Voir [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md) : un dossier est un évènement court (8 sur 10 tiennent en 3 jours), lire Immich à la demande suffit, un chemin peut dépasser 500 évènements (d'où les temps forts).
