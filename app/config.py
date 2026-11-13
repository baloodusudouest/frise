"""Réglages lus dans l'environnement du conteneur. Aucune valeur personnelle dans le code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APPLI = "sillage"


@dataclass(frozen=True)
class Config:
    password: str
    immich_url: str
    immich_cle: str
    data: Path
    static: Path
    immich_adresse: str = ""         # adresse d'Immich dans le navigateur (lien « Ouvrir dans Immich »)
    mots: tuple[str, ...] = ()       # mots qui font d'une étape un temps fort ; vide : la liste par défaut
    immich_port: int = 0             # port d'Immich sur le NAS : sans adresse réglée, le lien vise le même hôte que Sillage
    carnet_url: str = ""             # adresse de carnet vue depuis la stack ; avec le jeton, la liste vient de carnet
    carnet_jeton: str = ""           # le même jeton que CARNET_JETON_SILLAGE côté carnet ; vide : personnes d'Immich
    jeton_ha: str = ""               # 0.5 : jeton de Home Assistant pour /ha/sejour ; vide : adresse fermée
    muets: tuple[str, ...] = ()      # noms de dossier qui ne disent rien, en plus de la liste par défaut
    attente_connexion: bool = True   # délai anti-essais ; coupé dans les tests


def charger() -> Config:
    mot_de_passe = os.environ.get("SILLAGE_PASSWORD", "")
    if len(mot_de_passe) < 12:
        raise SystemExit("SILLAGE_PASSWORD est absent ou trop court (12 caractères au moins) : Sillage ne démarre pas.")
    cle = os.environ.get("SILLAGE_IMMICH_CLE", "").strip()
    if not cle:
        raise SystemExit("SILLAGE_IMMICH_CLE est absente : Sillage ne démarre pas (clé d'API Immich en lecture).")
    return Config(
        password=mot_de_passe,
        immich_url=os.environ.get("SILLAGE_IMMICH_URL", "http://immich_server:2283").rstrip("/"),
        immich_cle=cle,
        data=Path(os.environ.get("SILLAGE_DATA", "/data")),
        static=Path(__file__).parent / "static",
        immich_adresse=os.environ.get("SILLAGE_IMMICH_ADRESSE", "").rstrip("/"),
        immich_port=int(os.environ.get("SILLAGE_IMMICH_PORT") or 0) if (os.environ.get("SILLAGE_IMMICH_PORT") or "0").strip().isdigit() else 0,
        carnet_url=os.environ.get("SILLAGE_CARNET_URL", "http://carnet:8096").rstrip("/"),
        carnet_jeton=os.environ.get("SILLAGE_CARNET_JETON", "").strip(),
        jeton_ha=os.environ.get("SILLAGE_JETON_HA", "").strip(),
        muets=tuple(m.strip() for m in os.environ.get("SILLAGE_DOSSIERS_MUETS", "").split(",") if m.strip()),
        mots=tuple(m.strip().lower() for m in os.environ.get("SILLAGE_MOTS", "").split(",") if m.strip()),
    )
