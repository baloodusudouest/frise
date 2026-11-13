"""0.10 : les vignettes lues dans Immich, gardées sur le disque de Sillage (dossier /data/vignettes).

Une vignette déjà vue s'affiche sans redemander Immich, même après un redémarrage. La place est bornée :
au-delà de la limite, les fichiers les moins récemment servis partent les premiers. Rien de personnel dans
les noms de fichiers : l'identifiant Immich de la photo et la taille demandée."""
from __future__ import annotations

import os
import re
import threading
from pathlib import Path

SORTES = {"image/jpeg": "jpg", "image/webp": "webp", "image/png": "png", "image/svg+xml": "svg"}
TYPES = {v: k for k, v in SORTES.items()}
CLE = re.compile(r"^[0-9a-f-]{36}-(thumbnail|preview)$")


class Cache:
    def __init__(self, dossier: Path, limite_mo: int):
        self.dossier = dossier
        self.limite = max(0, limite_mo) * 1024 * 1024
        self._verrou = threading.Lock()
        self._ecrits = 0
        if self.limite:
            dossier.mkdir(parents=True, exist_ok=True)

    def _fichiers(self, cle: str):
        return [self.dossier / f"{cle}.{ext}" for ext in TYPES]

    def lire(self, cle: str) -> tuple[bytes, str] | None:
        if not self.limite or not CLE.match(cle):
            return None
        for f in self._fichiers(cle):
            try:
                contenu = f.read_bytes()
            except OSError:
                continue
            try:
                os.utime(f)                          # servie : elle reste plus longtemps
            except OSError:
                pass
            return contenu, TYPES[f.suffix[1:]]
        return None

    def garder(self, cle: str, contenu: bytes, sorte: str) -> None:
        ext = SORTES.get(sorte.split(";")[0].strip())
        if not self.limite or not ext or not CLE.match(cle) or not contenu:
            return
        f = self.dossier / f"{cle}.{ext}"
        try:
            temp = f.with_suffix(".tmp")
            temp.write_bytes(contenu)
            temp.replace(f)
        except OSError:
            return                                   # disque plein ou en lecture seule : on sert sans garder
        with self._verrou:
            self._ecrits += 1
            if self._ecrits % 50 == 1:
                self.elaguer()

    def elaguer(self) -> None:
        """Ramène le dossier sous sa limite, en retirant les vignettes les moins récemment servies."""
        try:
            fichiers = [(f.stat().st_mtime, f.stat().st_size, f) for f in self.dossier.iterdir() if f.is_file()]
        except OSError:
            return
        total = sum(t for _, t, _ in fichiers)
        for _, taille, f in sorted(fichiers):
            if total <= self.limite * 0.9:
                break
            try:
                f.unlink()
                total -= taille
            except OSError:
                pass

    def place(self) -> dict:
        try:
            tailles = [f.stat().st_size for f in self.dossier.iterdir() if f.is_file()] if self.limite else []
        except OSError:
            tailles = []
        return {"fichiers": len(tailles), "mo": round(sum(tailles) / 1048576, 1), "limite_mo": self.limite // 1048576}
