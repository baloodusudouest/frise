# Dossier de Sillage — le chemin de vie d'une personne, à partir d'Immich

Écrit le 12/11/2026 à partir du grill (quatre tours) et des décisions déjà prises pour « Frise », l'ancien nom du projet. Rien n'est codé, sauf la sonde.

## 1. Besoin

Choisir une personne et voir sa vie se dérouler le long d'un chemin : ses évènements dans l'ordre, chacun avec une photo phare et sa galerie, et l'âge qu'elle avait. On ouvre sur les temps forts (mariage, baptême, communion, anniversaire, diplôme, Noël, vacances…), puis on peut tout déplier.

Décidé au grill :

- **Nom : Sillage. Couleur : miel doré.** Une icône, comme les autres applis.
- **La personne se choisit parmi les contacts de carnet** reliés à Immich (portrait, date de naissance). Chaque fiche de carnet porte un lien vers son sillage.
- **Une étape = un album d'Immich**, daté par ses photos, nommé par l'album. Les albums viennent des dossiers « date + évènement », repris par Transhumance. Un album étalé sur plus de 30 jours est découpé en moments.
- **Photos sans album** : regroupées par journée, en retrait entre les étapes, repliées par défaut.
- **Temps fort** : reconnu par les mots du nom de l'album, corrigeable à la main (cocher, décocher).
- **Photo phare** : choisie par Sillage (personne nette, bien centrée, même notation que les portraits de carnet), remplaçable d'un clic.
- **Galerie d'une étape** : d'abord les photos où la personne est reconnue ; « Tout l'album » montre le reste.
- **Dates de carnet** : la naissance ouvre le chemin et donne l'âge à chaque étape ; les autres dates de la fiche sont posées comme repères, avec ou sans photo.
- **Découpage par âge, en décennies** (« 0 à 9 ans », « 10 à 19 ans »…), l'année en repère. Sans date de naissance : par année.
- **Photos mal datées** (avant la naissance, scan pas encore daté) : sorties du chemin, listées dans une tuile « À vérifier », avec un lien pour corriger la date dans Millésime ou Immich.
- **Animation** : le chemin se dessine au défilement, les étapes apparaissent en douceur, la photo phare s'ouvre en grand. En plus, un mode **« Raconter »** fait défiler la vie étape par étape. Tout est coupé si l'appareil demande moins d'animations.
- **Lecture seule d'Immich.** Les réglages de l'utilisateur (temps fort, photo phare, étape masquée) restent dans une base propre à Sillage.
- **Accès** : le mot de passe commun, réseau local et Tailscale.

Hors de la V1 : page imprimable du journal de naissance, carte Home Assistant et diaporama des invités, Treemich, vidéo. Fusion dans carnet envisagée après un mois d'usage stable.

## 2. Technique

**Pile.** Celle du socle : FastAPI, SQLite, Svelte 5, Tailwind 4, shadcn-svelte. Un conteneur « sillage », une image publiée, le mot de passe commun obligatoire.

**Immich n'est que lu.** Une clé d'API dédiée, limitée à la lecture (albums, photos, personnes, visages). Sillage n'a aucune fonction qui écrit dans Immich : rien à protéger par un mode lecture seule, mais un test le prouve (aucune demande autre que de lecture ne part).

**Lecture à la demande, avec une mémoire courte.** La sonde a montré que lire les photos d'une personne prend quelques secondes (4 980 photos en 2,5 s). Pour une personne :

1. ses photos : recherche par personne, avec date, lieu, type ;
2. les albums et leur contenu (lus une fois, gardés en mémoire, relus toutes les heures ou sur « Synchroniser ») ;
3. le croisement : pour chaque album où elle figure, la liste de ses photos et la date de l'étape (médiane des dates de ses photos dans l'album) ;
4. les photos sans album, regroupées par journée.

**Photo phare.** Pour chaque étape, les visages de la personne sur ses photos (cadre, taille de l'image) : note = visage assez grand, centré, entier, peu d'autres visages. Seules les premières photos candidates sont notées, pour ne pas multiplier les appels. Le choix de l'utilisateur passe devant.

**Images.** Le navigateur ne parle jamais à Immich : Sillage sert les vignettes et les aperçus (la clé reste sur le NAS), avec un cache sur disque borné.

**carnet.** Sillage lit dans carnet la liste des contacts reliés à Immich : nom affiché, identifiant de la personne dans Immich, date de naissance, autres dates de la fiche. Il faut pour cela une adresse nouvelle dans carnet, ouverte par un jeton (comme carnet lit déjà l'état de Millésime). carnet reçoit en échange l'adresse du sillage d'une personne, pour le lien dans la fiche. Si carnet ne répond pas, Sillage garde la dernière liste lue.

**Temps forts.** Une liste de mots (mariage, noces, baptême, communion, anniversaire, diplôme, remise, naissance, Noël, vacances, voyage…) modifiable dans Réglages. Les mots réels ne sont pas dans le dépôt au-delà de cette liste générique.

**Mal daté.** Une photo est écartée du chemin si elle est datée avant la naissance, ou si elle porte la marque des scans non datés (nom d'album ou de tag donné par une variable de la stack, comme dans Millésime).

## 3. Parcours des clics et des écrans

Quatre entrées : **Sillages**, **À vérifier**, **Connexion**, **Réglages**. Rail sur PC, pilule sur iPhone.

**Sillages** (écran d'ouverture) — la liste des personnes : portrait, nom, âge, nombre d'étapes. Recherche par nom, groupes de carnet en filtre. Toucher une personne ouvre son chemin.

**Le chemin d'une personne** — en tête : portrait, nom, dates, « Raconter », et le choix « Temps forts / Tout ». Puis le chemin, vertical : un chapitre par décennie d'âge ; dans chaque chapitre, les étapes posées le long du trait, alternées à gauche et à droite sur PC, d'un seul côté sur iPhone. Une étape montre sa photo phare, son nom, sa date, l'âge (« à 7 ans »), le nombre de photos. Entre les étapes, en petit : les journées sans album et les repères venus de carnet. Une règle des âges, sur le côté, saute d'un chapitre à l'autre.

**Une étape ouverte** — la photo phare en grand, puis la galerie (ses photos ; « Tout l'album »). Trois gestes : « Photo phare » sur une photo, « Temps fort » (coché ou non), « Masquer cette étape ». Un lien « Ouvrir dans Immich ». Une photo s'ouvre en plein écran, on passe de l'une à l'autre au doigt ou aux flèches.

**Raconter** — plein écran : les étapes se suivent seules (photo phare, nom, âge, deux ou trois photos), avec pause, précédent, suivant, sortie. Sur les temps forts par défaut.

**À vérifier** — des tuiles : photos datées avant la naissance ; scans non datés où la personne figure ; personnes sans date de naissance (lien vers carnet) ; étapes masquées (pour les rétablir).

**Connexion** — Immich (version, dernière lecture, nombre d'albums) et carnet (dernière liste lue), avec « Vérifier » et « Synchroniser ». **Réglages** — mots des temps forts, vitesse de « Raconter », version, déconnexion.

## 4. Design

Format commun (neutres chauds, sombre par défaut, Inter). **Couleur : miel doré** (à fixer à l'écran, autour de `#e3b556` en sombre et `#a8790f` en clair ; elle doit rester distincte de l'ocre de carnet).

**Signature : le trait du chemin**, une ligne miel qui se dessine en descendant, avec une courbe douce d'une étape à l'autre, comme le sillage derrière un bateau. Les temps forts sont de grandes cartes, les journées sans album de simples points sur le trait. L'âge est écrit en grand au début de chaque chapitre.

C'est la seule appli où l'animation raconte quelque chose : tracé au défilement, apparition des étapes, ouverture de la photo phare, mode « Raconter ». Tout s'efface avec « réduire les animations ». Bibliothèque d'animation à choisir à l'essai (motion ou animations CSS liées au défilement), la plus légère qui tienne sur iPhone.

**Icône** : un trait courbe miel qui s'élargit, sur fond sombre, trois points posés dessus.

## 5. Schéma de données

Sillage ne garde que ses propres réglages et des copies de travail ; tout le reste se relit.

```
reglages_etapes   personne (id Immich), etape (id d'album, ou jour « AAAA-MM-JJ »),
                  temps_fort (oui | non | vide = automatique), photo_phare (id de photo), masquee, le
personnes         copie de la liste lue dans carnet : id Immich, nom affiché, naissance, autres dates, lue_le
albums            copie de travail : id, nom, nombre de photos, début, fin, lue_le
mots              mots des temps forts
journal           le, quoi (réglage changé, synchro) — sans nom de personne
```

Cache des vignettes sur disque, borné, effaçable. Après la migration, les identifiants de photos changent : un choix de photo phare fait avant la fin de Transhumance pourrait devenir orphelin ; Sillage retombe alors sur son choix automatique et le signale dans « À vérifier ».

## 6. Plan d'implémentation

Étapes livrables et testées, dans l'ordre :

1. **Sonde sur les albums** (lecture seule, la sonde existe) : nombre d'albums, durée, albums par personne, part des photos sans album, temps de lecture. Rapport sans nom.
2. **carnet** : l'adresse à jeton qui donne les contacts reliés à Immich et leurs dates ; le lien « Sillage » dans la fiche.
3. **Squelette** depuis le socle : nom, couleur, icône, mot de passe, Connexion (Immich, carnet), liste des personnes.
4. **Le chemin** sans animation : étapes, chapitres par âge, journées sans album, repères de carnet, galerie, plein écran.
5. **Temps forts, photo phare, masquer**, et la tuile « À vérifier ».
6. **Animation** du chemin, puis **« Raconter »**.
7. Déploiement dans `homelab.yml`, un mois d'usage, liste des écarts.

Tests : faux Immich et fausse liste de carnet (personnes inventées) ; un test prouve qu'aucune écriture ne part vers Immich ; tests d'écran sur PC et iPhone pour le chemin, une étape ouverte, « Raconter » ; un test du découpage (âges, album de plus de 30 jours, photo avant la naissance).

## Questions ouvertes pour le conseil

1. **Faut-il commencer avant la fin de la migration ?** Aujourd'hui une partie seulement des dossiers est devenue des albums ; le reste est encore en bibliothèque externe, sans album. Sillage serait à moitié vide pendant quelques semaines.
2. **Album = étape, est-ce assez ?** Un album de vacances de trois semaines, un album « Noël » qui mélange plusieurs années, un évènement où la personne n'est reconnue sur aucune photo.
3. **La photo phare automatique** vaut-elle son coût (appels à Immich, notation), ou faut-il partir de la couverture de l'album et ne garder que le choix manuel ?
4. **« Raconter » dans la V1** : est-ce le cœur de l'appli ou ce qui la retarde ?
5. **Dépendre de carnet** pour la liste des personnes : bon choix, ou faut-il pouvoir fonctionner sur les seules personnes d'Immich ?
6. **Que manque-t-il** pour qu'on ait envie de rouvrir Sillage après la première semaine ?
