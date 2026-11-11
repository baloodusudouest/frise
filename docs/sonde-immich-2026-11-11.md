# Résultats de la sonde d'Immich — 11/11/2026

Sonde 0.1.0 (10:12) puis 0.1.1 (10:20), en lecture seule, sur Immich 3.4.0. Aucun nom de personne ni de dossier ici.

## Personnes

| Mesure | Nombre |
|---|---|
| Personnes (visages regroupés) | 3 440 |
| Nommées | 220 |
| Nommées au format « Prénom NOM » | 219 |
| Nommées avec date de naissance | 89 |

Photos par personne nommée : maximum 4 977, médiane 62. 6 personnes ont plus de 1 000 photos, 63 entre 100 et 1 000, 129 entre 10 et 99, 22 moins de 10.

## Dossiers

1 130 dossiers. Date portée par le chemin : au mois 546, à l'année 321, au jour 198, aucune 65.

| Forme | Dossiers |
|---|---|
| `/synologyphotos/Pellicule/AAAA/AAAA texte` | 253 |
| `/synologyphotos/Pellicule/AAAA/AAAA-MM-JJ texte` | 149 |
| `/synologyphotos/Photos numérisées/texte/AAAA/MM` | 149 |
| `/synologyphotos/Photos numérisées/texte/AAAA/MM/texte` | 148 |
| `/synologyphotos/Pellicule/AAAA/AAAA-MM texte` | 112 |
| `/data/library/texte/texte/AAAA/AAAA-MM texte` | 63 |
| Autres formes (moins de 30 dossiers chacune) | environ 256 |

Mots d'évènement fréquents en tête de nom : anniversaire (avec « anniv », « annif », « ans »), vacances, mariage, noël, séminaire, visite, journée, communion, repas, spectacle, baptême, départ, week-end, soirée, séjour, voyage, réunion, fêtes.

## Échantillon de 10 personnes (5 les plus photographiées, 5 moyennes)

| Pers. | Photos | Vidéos | Lecture (s) | Années couvertes | Dossiers | Photos / dossier daté (méd.) | (max) |
|---|---|---|---|---|---|---|---|
| P1 | 4 980 | 219 | 2,49 | 37 | 527 | 3 | 130 |
| P2 | 2 262 | 135 | 0,60 | 33 | 263 | 4 | 114 |
| P3 | 1 339 | 39 | 0,42 | 19 | 119 | 4 | 58 |
| P4 | 1 182 | 26 | 0,25 | 40 | 233 | 2 | 72 |
| P5 | 1 057 | 13 | 0,23 | 19 | 60 | 4,5 | 305 |
| P6 à P10 | 59 à 64 | 0 à 6 | 0,02 à 0,06 | 4 à 9 | 7 à 14 | 1 à 5 | 1 à 40 |

### Un dossier est-il un évènement ?

Étendue des dates des photos de la personne dans chaque dossier : médiane **1 jour** pour 9 personnes sur 10.

| Pers. | Dossiers | 3 jours ou moins | 4 à 30 jours | Plus de 30 jours |
|---|---|---|---|---|
| P1 | 527 | 438 (83 %) | 46 | 43 (8 %) |
| P2 | 263 | 206 (78 %) | 29 | 28 (11 %) |
| P3 | 119 | 82 (69 %) | 14 | 23 (19 %) |
| P4 | 233 | 207 (89 %) | 10 | 16 (7 %) |
| P5 | 60 | 49 (82 %) | 5 | 6 (10 %) |

### Date du dossier contre date de la photo

| Pers. | Photos en dossier daté au jour | Écart > 1 j | Écart > 7 j | En dossier daté au mois | Mois différent | En dossier daté à l'année | Sans date dans le chemin |
|---|---|---|---|---|---|---|---|
| P1 | 1 223 | 77 (6 %) | 7 | 1 252 | 40 (3 %) | 2 029 | 476 |
| P2 | 515 | 24 | 4 | 656 | 10 | 1 016 | 75 |
| P3 | 257 | 14 | 1 | 207 | 11 | 870 | 5 |
| P4 | 180 | 4 | 0 | 344 | 0 | 500 | 158 |
| P5 | 437 | 0 | 0 | 349 | 6 | 263 | 8 |

Une personne a une première année à 1900 : des dates aberrantes existent.

## Visages

58 visages sur 20 photos, tous avec un cadre complet, 35 nommés. Médiane 2 visages par photo, maximum 8.

## Non mesuré

La vitesse des vignettes : refus 403, la clé n'avait pas le droit d'afficher les images (`asset.view`). La clé de l'appli devra l'avoir.

## Ce que cela impose à la conception

1. **Un évènement = un dossier, daté par ses photos.** Le nom du dossier ne donne le jour que pour 18 % des dossiers, mais 8 dossiers sur 10 tiennent en 3 jours ou moins. Le nom fournit le libellé, les photos fournissent la date.
2. **Les dossiers longs (7 à 19 % selon la personne) ne sont pas des évènements** : il faut une règle pour eux.
3. **Une frise peut compter plus de 500 dossiers** sur 37 ans : il faut des niveaux (années, puis évènements) et une sélection des temps forts.
4. **Pas de cache nécessaire pour les listes** : 4 980 photos lues en 2,5 s, une personne moyenne en moins de 0,1 s.
5. **L'âge ne s'affiche que pour 89 personnes sur 220** : les autres relèvent de la révision « Sans anniversaire » de carnet.
6. **Dates aberrantes (1900) à écarter** dans une rubrique « date inconnue ».
7. **Ne pas dépendre de la racine du chemin** : `/synologyphotos/…` et `/data/library/…` coexistent, et la bibliothèque doit migrer vers le stockage Immich.
8. **Le cadre des visages est toujours présent** : le recadrage de la photo phare sur le visage est possible.
