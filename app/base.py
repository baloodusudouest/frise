"""La mémoire de Sillage : les corrections faites à la main et les récits relus. Un petit fichier SQLite.

Une correction est rattachée à l'empreinte du fichier, pas à l'identifiant de la photo dans Immich :
l'identifiant change quand la photo est renvoyée (migration), l'empreinte non."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

SORTES = ("pas_elle", "retiree", "phare", "titre", "masquee")


class Base:
    def __init__(self, chemin: Path):
        self._verrou = threading.Lock()
        self._c = sqlite3.connect(chemin, check_same_thread=False)
        self._c.row_factory = sqlite3.Row
        self._c.executescript("""
            CREATE TABLE IF NOT EXISTS marques (personne TEXT NOT NULL, empreinte TEXT NOT NULL, sorte TEXT NOT NULL,
                                               valeur TEXT NOT NULL DEFAULT '', le TEXT NOT NULL,
                                               PRIMARY KEY (personne, empreinte, sorte));
            CREATE TABLE IF NOT EXISTS recits (personne TEXT PRIMARY KEY, texte TEXT NOT NULL, le TEXT NOT NULL);
        """)

    def fermer(self) -> None:
        self._c.close()

    def marques(self, personne: str) -> dict[str, dict[str, str]]:
        """empreinte → {sorte: valeur} pour une personne."""
        sortie: dict[str, dict[str, str]] = {}
        with self._verrou:
            for l in self._c.execute("SELECT empreinte, sorte, valeur FROM marques WHERE personne = ?", (personne,)):
                sortie.setdefault(l["empreinte"], {})[l["sorte"]] = l["valeur"]
        return sortie

    def marquer(self, personne: str, sorte: str, effacer: list[str], poser: str | None, valeur: str = "") -> None:
        """Retire la marque de ces empreintes, puis la pose sur une seule (ou sur aucune)."""
        with self._verrou, self._c:
            self._c.executemany("DELETE FROM marques WHERE personne = ? AND empreinte = ? AND sorte = ?",
                                [(personne, e, sorte) for e in effacer])
            if poser:
                self._c.execute("INSERT OR REPLACE INTO marques VALUES (?, ?, ?, ?, ?)",
                                (personne, poser, sorte, valeur, datetime.now().isoformat(timespec="seconds")))

    def recit(self, personne: str) -> dict | None:
        with self._verrou:
            l = self._c.execute("SELECT texte, le FROM recits WHERE personne = ?", (personne,)).fetchone()
        return dict(l) if l else None

    def garder_recit(self, personne: str, texte: str | None) -> None:
        with self._verrou, self._c:
            if texte is None:
                self._c.execute("DELETE FROM recits WHERE personne = ?", (personne,))
            else:
                self._c.execute("INSERT OR REPLACE INTO recits VALUES (?, ?, ?)",
                                (personne, texte, datetime.now().isoformat(timespec="seconds")))
