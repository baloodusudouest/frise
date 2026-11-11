# Reprise — Frise

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- **Étape 0 terminée.** La sonde a tourné deux fois sur le vrai Immich ; résultats et conséquences dans [`docs/sonde-immich-2026-11-11.md`](docs/sonde-immich-2026-11-11.md).
- Pas encore de dossier de conception, pas d'appli.

## Ce que la sonde a tranché

- L'hypothèse « dossiers AAAA-MM-JJ évènement » est fausse : 198 dossiers sur 1 130 seulement sont datés au jour.
- Mais un dossier est bien un évènement court : 8 dossiers sur 10 tiennent en 3 jours ou moins. **Évènement = dossier, daté par ses photos, nommé par le dossier.**
- Lire Immich à la demande suffit (4 980 photos en 2,5 s).
- Une frise peut dépasser 500 dossiers : il faut des niveaux et des temps forts.

## Prochaine étape

1. Trancher avec Julien les 4 questions ouvertes par la sonde (dossiers longs, taille de la frise, migration vers le stockage Immich, dates aberrantes).
2. Écrire `docs/dossier.md` (6 sections).
3. Un passage au conseil, puis le plan d'implémentation.

## Décisions tranchées

- Frise est le pilote de la méthode (dossier à 6 sections, sonde d'abord) et du design (minimalisme + bento, animation narrative permise ici).
- Conteneur « frise » séparé ; fusion dans carnet envisagée après un mois stable.
- V1 en lecture seule : dossiers + visages Immich. Rien n'est écrit dans Immich ni dans Treemich. La façon de reconnaître un évènement reste à trancher après la sonde (voir plus bas).
- Style « chemin narratif », vertical sur iPhone ; une photo phare par évènement + galerie.
- Usages : consultation par Julien et Yves, invités, impression (page du journal de naissance).
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
