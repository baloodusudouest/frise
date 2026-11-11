# Reprise — Frise

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- **Étape 0 en cours : la sonde d'Immich.** Sonde 0.1.0 écrite, 5 tests verts contre un faux Immich. Jamais lancée sur le vrai Immich.
- Pas de dossier de conception, pas d'appli.

## Prochaine étape

1. Julien lance la sonde dans Portainer (README) et transmet `rapport-sonde-frise.md`.
2. Écrire dans `docs/dossier.md` la section technique à partir du rapport, puis les 5 autres sections.
3. Un passage au conseil, puis le plan d'implémentation.

## Décisions tranchées

- Frise est le pilote de la méthode (dossier à 6 sections, sonde d'abord) et du design (minimalisme + bento, animation narrative permise ici).
- Conteneur « frise » séparé ; fusion dans carnet envisagée après un mois stable.
- V1 en lecture seule : dossiers d'évènement + visages Immich. Rien n'est écrit dans Immich ni dans Treemich.
- Style « chemin narratif », vertical sur iPhone ; une photo phare par évènement + galerie.
- Usages : consultation par Julien et Yves, invités, impression (page du journal de naissance).
- Home Assistant : carte Lovelace et extension du diaporama invités, plus tard ; aucune automatisation.
- Technique : celle du dépôt socle (FastAPI, Svelte 5, Tailwind 4, shadcn-svelte), validée sur le NAS le 11/11/2026.
- Ordre après la V1 : un mois d'usage → livret + carte HA → Treemich → vidéo.

## Ce que la sonde doit trancher

- La forme réelle des dossiers : la V1 suppose « AAAA-MM-JJ évènement ». Si la date est portée par les dossiers parents (année/mois), le repérage des évènements change.
- La fiabilité de la date du dossier face à la date de la photo.
- La taille d'une frise : nombre d'évènements et de photos pour les personnes les plus photographiées.
- Le temps de lecture : faut-il un cache local ou peut-on lire Immich à la demande ?

## Pièges

- Les noms de points d'accès d'Immich changent selon les versions : la sonde note chaque refus au lieu de s'arrêter.
- Le rapport ne doit jamais contenir de nom : un test le vérifie, le garder vert.

## Non-objectifs de la V1

- Pas d'écriture dans Immich, Treemich ou carnet.
- Pas de vidéo, pas de livret imprimé, pas de carte Home Assistant.
