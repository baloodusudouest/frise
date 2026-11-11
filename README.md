# Frise

Frise de vie d'une personne à partir d'Immich : ses photos, rangées par évènement et par date.

**État : étape 0, la sonde.** L'appli n'est pas encore conçue. Avant d'écrire son dossier, une sonde lit Immich pour mesurer ce dont la conception dépend. Voir [`REPRISE.md`](REPRISE.md).

## La sonde d'Immich

Image : `ghcr.io/baloodusudouest/frise:sonde`. Le conteneur tourne une fois, écrit un rapport, puis s'arrête. Il ne modifie rien dans Immich.

### Ce qu'elle mesure

| Question | Mesure |
|---|---|
| La clé suffit-elle ? | Version d'Immich, accès refusés étape par étape |
| Qui peut avoir une frise ? | Personnes nommées, avec ou sans date de naissance, au format « Prénom NOM » |
| Quelle taille de frise ? | Photos par personne : maximum, médiane, répartition |
| Les dossiers sont-ils des évènements ? | Formes réelles des chemins, précision de la date portée par le dossier |
| Peut-on se fier à la date du dossier ? | Écarts entre date du dossier et date de la photo, sur un échantillon de personnes |
| Est-ce assez rapide ? | Temps de lecture des photos d'une personne, temps et poids des vignettes |
| Peut-on recadrer la photo phare ? | Présence du cadre des visages |

### Ce que contient le rapport

Ni nom de personne, ni nom de dossier. Les personnes sont notées P1, P2… Les dossiers sont réduits à leur forme, par exemple `/synologyphotos/Pellicule/AAAA/MM/AAAA-MM-JJ texte`.

Une exception : le premier mot des dossiers d'évènement, quand il revient dans 3 dossiers au moins (mariage, anniversaire, noël…). Il sert à savoir quels types d'évènements reconnaître. Pour le retirer : `MOTS_EVENEMENTS=0`.

### Lancer la sonde (Portainer)

1. Dans Immich, créer une clé d'API **en lecture seule** : Paramètres du compte → Clés d'API. Cocher uniquement des droits de lecture (personnes, visages, photos, dossiers, albums, serveur, utilisateur). Si un droit manque, le rapport dit quelle étape a été refusée.
2. Dans les variables de la stack `homelab.yml`, ajouter `FRISE_SONDE_IMMICH_CLE` avec cette clé.
3. Créer le dossier `frise/sonde` dans le dossier docker du NAS.
4. Ajouter le service ci-dessous à `homelab.yml`, mettre à jour la stack.
5. Le conteneur s'arrête seul. Le rapport est dans `frise/sonde/rapport-sonde-frise.md` (et dans les journaux du conteneur).
6. Retirer le service de la stack et supprimer la clé d'API dans Immich.

```yaml
  frise-sonde:
    image: ghcr.io/baloodusudouest/frise:sonde
    container_name: frise_sonde
    depends_on:
      - immich-server
    environment:
      - TZ=${TZ}
      - IMMICH_URL=http://immich_server:2283
      - IMMICH_API_KEY=${FRISE_SONDE_IMMICH_CLE}   # clé en lecture seule, à supprimer après la sonde
    volumes:
      - ${DOCKER_ROOT}/frise/sonde:/data           # le rapport y est écrit
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    restart: "no"                                  # tourne une fois puis s'arrête
```

### Réglages

| Variable | Défaut | Rôle |
|---|---|---|
| `IMMICH_URL` | `http://immich_server:2283` | Adresse d'Immich vue du conteneur |
| `IMMICH_API_KEY` | (obligatoire) | Clé d'API en lecture seule |
| `PERSONNES_ECHANTILLON` | `10` | Personnes étudiées en détail (les plus photographiées et des moyennes) |
| `MAX_PHOTOS_PAR_PERSONNE` | `5000` | Plafond de photos lues par personne |
| `MOTS_EVENEMENTS` | `1` | `0` : aucun mot de dossier dans le rapport |

## Développer

```sh
pip install -r requirements-dev.txt
python -m pytest -q          # la sonde contre un faux Immich
```
