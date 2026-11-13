"""Sillage de démonstration pour les tests d'écran : un faux Immich, une vie inventée.

    python -m tests.interface.serveur <dossier> <port>     (mot de passe : « essai-essai-essai »)"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import httpx
import uvicorn

from app import main
from app.config import Config
from app.immich import Immich
from tests.faux_immich import CAMILLE, HUGO, FauxImmich, ident, photo

MDP = "essai-essai-essai"


def dessin(nom: str) -> bytes:
    """Une image de couleur, différente pour chaque photo, pour que l'écran ressemble à quelque chose."""
    t = int(hashlib.sha1(nom.encode()).hexdigest()[:6], 16)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="hsl({t % 360} 35% 32%)"/>'
            f'<circle cx="{120 + t % 160}" cy="130" r="54" fill="hsl({(t + 40) % 360} 45% 62%)"/>'
            f'<rect y="220" width="400" height="80" fill="hsl({(t + 200) % 360} 30% 22%)"/></svg>').encode()


def vie() -> FauxImmich:
    faux = FauxImmich()
    serie = lambda nom, jour, n, dossier="2020/2020-01-01": [photo(f"{nom}{i}", f"{jour}T{10 + i % 10:02d}:00:00", dossier, visage=0.1 + i / 50) for i in range(n)]
    faux.photos[CAMILLE] = (
        serie("naissance", "1987-03-14", 4, "1987/1987-03-14 Naissance de Camille")
        + serie("bapteme", "1987-06-07", 9, "1987/1987-06-07 Baptême de Camille")
        + serie("jardin", "1989-08-02", 1)
        + serie("noel", "1992-12-25", 6, "1992/1992-12-25 Noël chez les grands-parents")
        + serie("plage", "1995-07-20", 12, "1995/1995-07 Vacances à la mer")
        + serie("classe", "1998-09-04", 1)
        + serie("communion", "1999-05-16", 7, "1999/1999-05-16 Communion")
        + serie("diplome", "2009-06-30", 3, "2009/2009-06-30 Remise des diplômes")
        + serie("rando", "2014-08-11", 5)
        + [dict(x, aussi=[HUGO]) for x in serie("mariage", "2019-06-15", 40)]
        + serie("anniv", "2022-03-14", 8, "2022/2022-03-14 Anniversaire 35 ans")
        + [photo("trop-tot", "1975-01-01T10:00:00")])
    faux.photos[CAMILLE][10 + 4]["type"] = "VIDEO"
    faux.albums = {}
    reponse = faux.repondre

    def repondre(demande: httpx.Request) -> httpx.Response:
        if demande.url.path.endswith("/thumbnail"):
            return httpx.Response(200, content=dessin(demande.url.path), headers={"content-type": "image/svg+xml"})
        if demande.url.path == "/api/albums":
            if demande.url.params.get("assetId", "") in {p["id"] for p in faux.photos[CAMILLE] if "mariage" in p["originalPath"]}:
                return httpx.Response(200, json=[{"albumName": "Mariage de Camille et Hugo"}])
            return httpx.Response(200, json=[])
        return reponse(demande)
    faux.repondre = repondre
    return faux


def main_() -> None:
    racine, port = Path(sys.argv[1]), int(sys.argv[2])
    (racine / "data").mkdir(parents=True, exist_ok=True)
    cfg = Config(password=MDP, immich_url="http://immich", immich_cle="cle", data=racine / "data",
                 static=Path(__file__).resolve().parents[2] / "app" / "static", immich_adresse="http://photos.exemple",
                 attente_connexion=False, jeton_ha="jeton-ha")
    main.ETAT.update(cfg=cfg, immich=Immich("http://immich", "cle", transport=vie().transport()))
    # 0.5 : trois invitations de démonstration, notées dans invites.json pour les tests d'écran
    import json
    import threading
    import time
    from datetime import date, timedelta

    def inviter():
        for _ in range(100):
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health").status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        fin, h = (date.today() + timedelta(days=2)).isoformat(), {"Authorization": "Bearer jeton-ha"}
        jetons = {}
        for chambre, noms in (("seule", ["Camille ROUSSEL"]), ("couple", ["Camille ROUSSEL", "Hugo MARCHAND"]), ("inconnu", ["Personne INCONNUE"])):
            r = httpx.post(f"http://127.0.0.1:{port}/ha/sejour", headers=h, json={"chambre": chambre, "noms": noms, "jusqu_au": fin})
            jetons[chambre] = r.json()["chemin"]
        (racine / "invites.json").write_text(json.dumps(jetons))
    threading.Thread(target=inviter, daemon=True).start()
    uvicorn.run(main.app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main_()
