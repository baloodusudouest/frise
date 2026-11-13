# Reprise — Sillage (ancien nom : Frise)

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (13/11/2026)

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

- **Immich : plusieurs `personIds` dans `/search/metadata` rendent-ils bien les photos où toutes les personnes sont ensemble** (intersection) ? Le faux Immich des tests le suppose. Si Immich rend l'union, le chemin commun serait faux : filtrer alors côté Sillage sur `people`.
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
- Vue des invités (0.5.0) : jeton par séjour, rien que le chemin et les photos phares ; le propriétaire garde seul corrections, Raconter et Immich.
- Hors V1 : page imprimable, arbre généalogique, vidéo, sillages croisés, « ce jour-là ».
- Technique : celle du dépôt socle.

## Ce que la première sonde (11/11/2026) avait montré

Voir [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md) : un dossier est un évènement court (8 sur 10 tiennent en 3 jours), lire Immich à la demande suffit, un chemin peut dépasser 500 évènements (d'où les temps forts).
