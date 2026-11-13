"""La mémoire de Sillage : les corrections faites à la main et les récits relus. Un petit fichier SQLite.

Une correction est rattachée à l'empreinte du fichier, pas à l'identifiant de la photo dans Immich :
l'identifiant change quand la photo est renvoyée (migration), l'empreinte non."""
from __future__ import annotations

import json
import secrets
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
            CREATE TABLE IF NOT EXISTS invites (jeton TEXT PRIMARY KEY, chambre TEXT NOT NULL, personnes TEXT NOT NULL,
                                                expire TEXT NOT NULL, cree_le TEXT NOT NULL);
        """)
        # 0.6 : date d'arrivée, pour l'onglet « Chambres » (bases de la 0.5 : colonne ajoutée)
        if "du" not in [l["name"] for l in self._c.execute("PRAGMA table_info(invites)")]:
            self._c.execute("ALTER TABLE invites ADD COLUMN du TEXT NOT NULL DEFAULT ''")
            self._c.commit()

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

    # ------------------------------------------------------------ 0.5 : invités des chambres
    def invite(self, jeton: str) -> dict | None:
        """L'invitation de ce jeton, si elle n'a pas expiré : {chambre, personnes: [{id, nom}], expire}."""
        with self._verrou:
            l = self._c.execute("SELECT * FROM invites WHERE jeton = ? AND expire > ?",
                                (jeton, datetime.now().isoformat(timespec="seconds"))).fetchone()
        return {"chambre": l["chambre"], "personnes": json.loads(l["personnes"]), "expire": l["expire"]} if l else None

    def poser_invite(self, chambre: str, personnes: list[dict], expire: str, du: str = "") -> str:
        """Une invitation par chambre : la même si rien n'a changé, sinon une nouvelle (l'ancienne ne marche plus).
        La date d'arrivée ne compte pas : la changer garde le lien."""
        corps = json.dumps(personnes, ensure_ascii=False, sort_keys=True)
        maintenant = datetime.now().isoformat(timespec="seconds")
        with self._verrou, self._c:
            self._c.execute("DELETE FROM invites WHERE expire <= ?", (maintenant,))
            l = self._c.execute("SELECT jeton FROM invites WHERE chambre = ? AND personnes = ? AND expire = ?",
                                (chambre, corps, expire)).fetchone()
            if l:
                self._c.execute("UPDATE invites SET du = ? WHERE jeton = ?", (du, l["jeton"]))
                return l["jeton"]
            self._c.execute("DELETE FROM invites WHERE chambre = ?", (chambre,))
            jeton = secrets.token_urlsafe(24)
            self._c.execute("INSERT INTO invites (jeton, chambre, personnes, expire, cree_le, du) VALUES (?, ?, ?, ?, ?, ?)",
                            (jeton, chambre, corps, expire, maintenant, du))
            return jeton

    def invitations(self) -> list[dict]:
        """Les invitations encore valables, par date d'arrivée : {jeton, chambre, personnes, expire, du}."""
        with self._verrou:
            lignes = self._c.execute("SELECT * FROM invites WHERE expire > ? ORDER BY du, chambre",
                                     (datetime.now().isoformat(timespec="seconds"),)).fetchall()
        return [{"jeton": l["jeton"], "chambre": l["chambre"], "personnes": json.loads(l["personnes"]),
                 "expire": l["expire"], "du": l["du"]} for l in lignes]

    def retirer_invites(self, chambre: str) -> None:
        with self._verrou, self._c:
            self._c.execute("DELETE FROM invites WHERE chambre = ?", (chambre,))
