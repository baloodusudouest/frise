# Reprise — Sillage (ancien nom : Frise)

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (12/11/2026)

- Le projet s'appelle **Sillage** (dépôt renommé). Couleur : miel doré. Une icône est à faire avec le squelette.
- Grill fini, **dossier écrit** ([`docs/dossier.md`](docs/dossier.md)), **conseil passé** ([`docs/conseil.md`](docs/conseil.md)), décisions d'après conseil en fin de dossier.
- **Rien n'est codé**, sauf la sonde (`sonde/`), qui ne mesure que les dossiers.
- La migration vers le stockage d'Immich est en cours (appli Transhumance) ; Sillage ne l'attend plus.

## Prochaine étape

**La sonde, par le navigateur, en lecture seule**, sur cinq personnes choisies par l'utilisateur, quand aucun lot de migration ne tourne : photos par décennie d'âge, part en album, part de scans non datés, photos sans date d'origine, personnes en double probable. Rapport sans nom de personne. Puis révision du plan, puis le squelette depuis le socle.

## Décisions à ne pas rouvrir sans raison

- Étape = groupe de photos de la personne proches en dates ; l'album la nomme.
- Lecture seule d'Immich ; réglages dans la base de Sillage, rattachés à l'empreinte des fichiers.
- Personnes : carnet d'abord, Immich en secours.
- « Raconter » dans la V1, sobre, avec relecture.
- Hors V1 : page imprimable, carte Home Assistant, arbre généalogique, vidéo, lien partageable, sillages croisés, « ce jour-là ».
- Technique : celle du dépôt socle.

## Ce que la première sonde (11/11/2026) avait montré

Voir [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md) : un dossier est un évènement court (8 sur 10 tiennent en 3 jours), lire Immich à la demande suffit, un chemin peut dépasser 500 évènements (d'où les temps forts).
