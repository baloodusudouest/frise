"""Un faux Immich pour les tests : personnes et photos inventées, et le relevé de tout ce qui lui est demandé."""
from __future__ import annotations

import json
import uuid

import httpx

IMAGE = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                      "0000000d49444154789c6360f8cfc0f01f0005050201c5a2d5d90000000049454e44ae426082")


def ident(nom: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, nom))


CAMILLE, HUGO, ANONYME, CACHEE = ident("camille"), ident("hugo"), ident("anonyme"), ident("cachee")
HOTE = ident("hote")       # 0.7 : un hôte de la maison (inventé)


def photo(nom, quand, dossier="2020/2020-01-01", visage=0.0, **plus):
    p = {"id": ident(nom), "type": "IMAGE", "originalPath": f"/photos/{dossier}/{nom}.jpg",
         "localDateTime": quand + ".000Z", "isTrashed": False, "isArchived": False, "visibility": "timeline", "people": [],
         "checksum": "somme-" + nom}
    if visage:
        p["people"] = [{"id": CAMILLE, "faces": [{"imageWidth": 1000, "imageHeight": 1000, "boundingBoxX1": 0,
                                                  "boundingBoxY1": 0, "boundingBoxX2": int(1000 * visage), "boundingBoxY2": 1000}]}]
    p.update(plus)
    return p


class FauxImmich:
    def __init__(self):
        self.demandes: list[tuple[str, str]] = []
        self.refuse = 0          # code à répondre partout (401, 500…) ; 0 : tout va bien
        self.personnes = [
            {"id": CAMILLE, "name": "Camille ROUSSEL", "birthDate": "1987-03-14", "isHidden": False},
            {"id": HUGO, "name": "Hugo MARCHAND", "birthDate": None, "isHidden": False},
            {"id": ANONYME, "name": "", "birthDate": None, "isHidden": False},
            {"id": CACHEE, "name": "Tante Cachée", "birthDate": None, "isHidden": True},
        ]
        self.photos = {
            CAMILLE: [
                photo("avant", "1980-05-01T10:00:00"),
                photo("bapteme1", "1987-06-07T11:00:00", "1987/1987-06-07 Baptême de Camille", visage=0.1),
                photo("bapteme2", "1987-06-07T15:00:00", "1987/1987-06-07 Baptême de Camille", visage=0.4),
                photo("bapteme3", "1987-06-08T09:00:00", "1987/1987-06-07 Baptême de Camille", type="VIDEO"),
                photo("plage", "1995-07-20T09:00:00"),
                photo("mariage1", "2019-06-15T14:00:00", visage=0.2, aussi=[HUGO]),
                photo("mariage2", "2019-06-16T01:00:00", visage=0.3, aussi=[HUGO]),
                photo("corbeille", "2019-06-15T15:00:00", isTrashed=True),
                photo("archive", "2019-06-15T16:00:00", isArchived=True),
                photo("verrou", "2019-06-15T17:00:00", visibility="locked"),
            ],
            HUGO: [photo("hugo1", "2001-02-03T10:00:00"), photo("hugo2", "2002-02-03T10:00:00")],
        }
        self.albums = {ident("mariage2"): "Mariage de Camille et Hugo"}

    @staticmethod
    def _avec_visages(p: dict, qui: str) -> dict:
        """Comme Immich avec withPeople : toutes les personnes reconnues sur la photo (la personne cherchée, et « aussi »)."""
        vus = {x["id"] for x in p["people"]}
        en_plus = [{"id": i, "faces": []} for i in dict.fromkeys([qui, *p.get("aussi", [])]) if i not in vus]
        return {**p, "people": p["people"] + en_plus}

    def repondre(self, demande: httpx.Request) -> httpx.Response:
        chemin = demande.url.path.removeprefix("/api")
        self.demandes.append((demande.method, chemin))
        if self.refuse:
            return httpx.Response(self.refuse, json={"message": "non"})
        if chemin == "/server/version":
            return httpx.Response(200, json={"major": 3, "minor": 4, "patch": 1})
        if chemin == "/people":
            return httpx.Response(200, json={"people": self.personnes, "hasNextPage": False})
        if chemin == "/search/metadata" and demande.method == "POST":
            corps = json.loads(demande.content)
            ids = corps["personIds"]
            items = [self._avec_visages(p, ids[0]) for p in self.photos.get(ids[0], [])]
            if len(ids) > 1:                       # comme Immich : les photos où toutes ces personnes sont reconnues
                items = [p for p in items if set(ids[1:]) <= {x["id"] for x in p["people"]}]
            return httpx.Response(200, json={"assets": {"items": items, "nextPage": None}})
        if chemin == "/albums":
            nom = self.albums.get(demande.url.params.get("assetId"))
            return httpx.Response(200, json=[{"albumName": nom, "id": ident(nom)}] if nom else [])
        if chemin.startswith("/albums/"):                # 0.12 : un album et ses photos (avec leurs personnes)
            nom = next((n for n in set(self.albums.values()) if ident(n) == chemin.split("/")[2]), None)
            if not nom:
                return httpx.Response(404, json={"message": "album inconnu"})
            vues = {}
            for qui, liste in self.photos.items():
                for x in liste:
                    if self.albums.get(x["id"]) == nom:
                        vues.setdefault(x["id"], self._avec_visages(x, qui))
            return httpx.Response(200, json={"id": ident(nom), "albumName": nom, "assets": list(vues.values())})
        if chemin.endswith("/video/playback"):           # 0.10 : une « vidéo » de 1 000 octets, lue par morceaux
            corps = bytes(range(250)) * 4
            plage = demande.headers.get("range", "")
            if plage.startswith("bytes="):
                debut, _, fin = plage[6:].partition("-")
                debut, fin = int(debut), int(fin or len(corps) - 1)
                return httpx.Response(206, content=corps[debut:fin + 1], headers={
                    "content-type": "video/mp4", "accept-ranges": "bytes", "content-range": f"bytes {debut}-{fin}/{len(corps)}"})
            return httpx.Response(200, content=corps, headers={"content-type": "video/mp4", "accept-ranges": "bytes"})
        if chemin.endswith("/thumbnail"):
            return httpx.Response(200, content=IMAGE, headers={"content-type": "image/png"})
        return httpx.Response(404, json={"message": "inconnu"})

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.repondre)
