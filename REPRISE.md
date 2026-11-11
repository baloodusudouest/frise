# Reprise — Frise

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- **Étape 0 en cours : la sonde d'Immich.** Sonde 0.1.1, 7 tests verts.
- Premier passage sur le vrai Immich (sonde 0.1.0, 11/11 à 10:12) : partiel. Le comptage par personne a été refusé (droit `person.statistics` absent de la clé), donc l'échantillon de personnes, les vignettes et les visages n'ont pas été mesurés.
- La 0.1.1 étudie quand même un échantillon quand ce droit manque, et mesure l'étendue réelle des dates dans chaque dossier.
- Pas de dossier de conception, pas d'appli.

## Ce que le premier passage a déjà établi

- Immich 3.4.0. La clé en lecture seule suffit pour les personnes, les dossiers et les albums.
- 3 443 personnes dont 220 nommées ; 219 au format « Prénom NOM » ; 89 seulement ont une date de naissance.
- 1 130 dossiers. Date portée par le chemin : au mois pour 546, à l'année pour 321, **au jour pour 198 seulement**, aucune pour 65.
- **L'hypothèse de la V1 (« dossiers AAAA-MM-JJ évènement ») est fausse pour plus de 80 % des dossiers.** Formes dominantes : `Pellicule/AAAA/AAAA texte` (253), `Pellicule/AAAA/AAAA-MM-JJ texte` (149), `Photos numérisées/texte/AAAA/MM[/texte]` (environ 300), `Pellicule/AAAA/AAAA-MM texte` (112), `/data/library/…/AAAA/AAAA-MM texte` (63, déjà migrés dans le stockage Immich).
- Types d'évènements lisibles dans les noms : anniversaire (avec « anniv », « annif », « ans »), vacances, mariage, noël, séminaire, communion, baptême, repas, spectacle, voyage, week-end.
- 70 albums.

## Prochaine étape

1. Julien relance la sonde 0.1.1 (image re-téléchargée), idéalement après avoir ajouté le droit `person.statistics` à la clé, et transmet le rapport.
2. Écrire dans `docs/dossier.md` la section technique à partir des deux rapports, puis les 5 autres sections.
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

## Ce que la sonde doit encore trancher

- Un dossier daté seulement à l'année ou au mois correspond-il à un évènement court ? (étendue des dates des photos dans chaque dossier)
- La date du dossier concorde-t-elle avec la date de la photo, surtout pour les photos numérisées ?
- La taille d'une frise : nombre d'évènements et de photos pour les personnes les plus photographiées.
- Le temps de lecture : faut-il un cache local ou peut-on lire Immich à la demande ?
- Le chemin `/data/library/…` : la bibliothèque est en cours de migration vers le stockage Immich ; Frise ne doit pas dépendre de la racine du chemin.

## Pièges

- Les noms de points d'accès d'Immich changent selon les versions : la sonde note chaque refus au lieu de s'arrêter.
- Le rapport ne doit jamais contenir de nom : un test le vérifie, le garder vert. Limite connue : les « premiers mots fréquents » laissent passer un prénom placé en tête de 3 dossiers ou plus.
- Le droit `person.statistics` est distinct du droit de lecture des personnes dans Immich 3.

## Non-objectifs de la V1

- Pas d'écriture dans Immich, Treemich ou carnet.
- Pas de vidéo, pas de livret imprimé, pas de carte Home Assistant.
