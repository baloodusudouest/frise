# Reprise — Frise

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- **En attente de la migration vers le stockage Immich.**
- Étape 0 terminée sur les dossiers. La sonde a tourné deux fois sur le vrai Immich ; résultats et conséquences dans [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md).
- Pas encore de dossier de conception, pas d'appli.

## Ce que la sonde a tranché

- L'hypothèse « dossiers AAAA-MM-JJ évènement » est fausse : 198 dossiers sur 1 130 seulement sont datés au jour.
- Mais un dossier est bien un évènement court : 8 dossiers sur 10 tiennent en 3 jours ou moins. **Évènement = dossier, daté par ses photos, nommé par le dossier.**
- Lire Immich à la demande suffit (4 980 photos en 2,5 s).
- Une frise peut dépasser 500 dossiers : il faut des niveaux et des temps forts.

## Prochaine étape

**Frise est en attente** (décision du 11/11/2026). Elle reprend quand ces trois chantiers sont finis :

1. Millésime : dater les photos non datées (les dates aberrantes et les dates de naissance manquantes se traitent là, pas dans Frise).
2. Vérif dates photos : inscrire les dates dans les fichiers.
3. Migration de la Pellicule vers le stockage Immich, avec les dossiers repris en albums.

À la reprise : relancer la sonde sur les albums (elle ne mesure aujourd'hui que les dossiers), puis écrire `docs/dossier.md`, un passage au conseil, le plan.

## Décisions tranchées

- Frise est le pilote de la méthode (dossier à 6 sections, sonde d'abord) et du design (minimalisme + bento, animation narrative permise ici).
- Conteneur « frise » séparé ; fusion dans carnet envisagée après un mois stable.
- V1 en lecture seule : **albums** + visages Immich. Frise sera conçue directement sur les albums, après la migration ; pas de version intermédiaire sur les dossiers.
- Un évènement est daté par ses photos, nommé par son album.
- Un album qui s'étale sur plus de 30 jours est découpé automatiquement en moments, chacun placé à sa date.
- À l'ouverture : les temps forts reconnus par leur nom (mariage, anniversaire, baptême, communion, noël, vacances…), année par année ; un geste déplie tous les évènements d'une année.
- Dates aberrantes et dates de naissance manquantes : attendre le passage de Millésime avant de fixer une règle.
- Style « chemin narratif », vertical sur iPhone ; une photo phare par évènement + galerie.
- Usages : consultation par les habitants de la maison, invités, impression (page du journal de naissance).
- Home Assistant : carte Lovelace et extension du diaporama invités, plus tard ; aucune automatisation.
- Technique : celle du dépôt socle (FastAPI, Svelte 5, Tailwind 4, shadcn-svelte), validée sur le NAS le 11/11/2026.
- Ordre après la V1 : un mois d'usage → livret + carte HA → Treemich → vidéo.

## Pièges

- Les noms de points d'accès d'Immich changent selon les versions : la sonde note chaque refus au lieu de s'arrêter.
- Le rapport ne doit jamais contenir de nom : un test le vérifie, le garder vert. Limite connue : les « premiers mots fréquents » laissent passer un prénom placé en tête de 3 dossiers ou plus.
- Dans Immich 3, les droits `person.statistics` (comptage) et `asset.view` (images) sont distincts des droits de lecture : la clé de l'appli doit les avoir tous.

## Non-objectifs de la V1

- Pas d'écriture dans Immich, Treemich ou carnet.
- Pas de vidéo, pas de livret imprimé, pas de carte Home Assistant.
