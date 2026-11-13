# Reprise — Sillage (ancien nom : Frise)

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (13/11/2026)

- **0.2.0** (13/11/2026) : connexion commune avec l'Anneau — cookie `maison_session` (accepté ; `Sessions.connecte`, `commun_valide` dans `app/auth.py`). Jamais essayée sur la vraie installation.
- **Version 0.1.0 codée et publiée** (`ghcr.io/baloodusudouest/sillage:latest`, port 8093) : personnes d'Immich, chemin d'une personne, étape ouverte, photo en grand. Lecture seule d'Immich. 16 tests du serveur, 8 d'écran (PC et iPhone), 3 de l'ancienne sonde.
- **Jamais lancée sur la vraie photothèque.** C'est elle qui sert de sonde : à regarder sur cinq personnes.
- Dossier ([`docs/dossier.md`](docs/dossier.md)), conseil ([`docs/conseil.md`](docs/conseil.md)), décisions d'après conseil en fin de dossier.

## À vérifier sur la vraie installation

- La clé d'API (droits `person.read`, `asset.read`, `asset.view`, `album.read`) suffit-elle ? Un refus s'affiche dans « Connexion ».
- La recherche rend-elle bien les visages (`withPeople`) ? Sinon la photo phare est la première image du groupe.
- Le temps de lecture d'une personne très photographiée, et celui des noms d'albums (une lecture par étape de plus d'une photo, huit de front, gardées dix minutes).
- L'écart de deux jours donne-t-il des étapes qui ressemblent à des évènements ?

## Pas encore fait (dans l'ordre du plan)

1. Personnes venues de carnet (adresse à jeton dans carnet), lien dans la fiche.
2. Corrections gardées dans Sillage : « ce n'est pas elle », « retirer cette photo », « masquer cette étape », titre modifiable, choix de la photo phare ; base SQLite, réglages rattachés à l'empreinte.
3. « Raconter », puis l'animation du trait.
4. Scans datés « vers … », date de fin, tuile « À vérifier », cache des vignettes sur disque, lecture des vidéos.

## Décisions à ne pas rouvrir sans raison

- Étape = groupe de photos de la personne proches en dates ; l'album la nomme.
- Lecture seule d'Immich ; réglages dans la base de Sillage, rattachés à l'empreinte des fichiers.
- Personnes : carnet d'abord, Immich en secours.
- « Raconter » dans la V1, sobre, avec relecture.
- Hors V1 : page imprimable, carte Home Assistant, arbre généalogique, vidéo, lien partageable, sillages croisés, « ce jour-là ».
- Technique : celle du dépôt socle.

## Ce que la première sonde (11/11/2026) avait montré

Voir [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md) : un dossier est un évènement court (8 sur 10 tiennent en 3 jours), lire Immich à la demande suffit, un chemin peut dépasser 500 évènements (d'où les temps forts).
