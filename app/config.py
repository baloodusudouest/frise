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
        mots=tuple(m.strip().lower() for m in os.environ.get("SILLAGE_MOTS", "").split(",") if m.strip()),
    )
