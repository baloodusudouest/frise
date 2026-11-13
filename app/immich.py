"""Ce que Sillage demande à Immich : uniquement des lectures.

Trois gestes, pas un de plus : lire une adresse (GET), chercher des photos (POST /search/metadata,
qui est une lecture malgré sa méthode), et lire une image. Sillage n'a aucune fonction qui écrit
dans Immich ; un test le vérifie sur ce fichier."""
from __future__ import annotations

import httpx

LECTURES_EN_POST = ("/search/metadata",)


class ErreurImmich(Exception):
    pass


class Immich:
    def __init__(self, url: str, cle: str, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(base_url=url + "/api", headers={"x-api-key": cle, "Accept": "application/json"},
                                   timeout=httpx.Timeout(60, connect=10), transport=transport)

    def fermer(self) -> None:
        self.client.close()

    def _lire(self, chemin: str, quoi: str, corps: dict | None = None, **params):
        if corps is not None and chemin not in LECTURES_EN_POST:
            raise ErreurImmich("Sillage ne fait que lire Immich.")
        try:
            r = self.client.post(chemin, json=corps) if corps is not None else self.client.get(chemin, params=params or None)
        except httpx.HTTPError as exc:
            raise ErreurImmich(f"Immich injoignable pendant {quoi} ({exc.__class__.__name__}).") from exc
        if r.status_code in (401, 403):
            raise ErreurImmich(f"Immich refuse {quoi} : la clé d'API de Sillage n'en a pas le droit ({r.status_code}).")
        if r.status_code >= 400:
            raise ErreurImmich(f"Immich a refusé {quoi} ({r.status_code}).")
        return r

    def version(self) -> str:
        v = self._lire("/server/version", "la lecture de la version").json()
        return f"{v['major']}.{v['minor']}.{v['patch']}"

    def personnes(self) -> list[dict]:
        """Toutes les personnes, page par page (les masquées aussi : c'est Sillage qui trie)."""
        sortie, page = [], 1
        while page:
            r = self._lire("/people", "la lecture des personnes", page=page, size=1000, withHidden="true").json()
            sortie += r.get("people", [])
            page = page + 1 if r.get("hasNextPage") else 0
        return sortie

    def photos_de(self, personne: str):
        """Toutes les photos et vidéos visibles où la personne est reconnue."""
        yield from self.photos_ensemble([personne])

    def photos_ensemble(self, personnes: list[str]):
        """Les photos où toutes ces personnes sont reconnues ensemble (Immich croise les personnes demandées)."""
        page = 1
        while page:
            r = self._lire("/search/metadata", "la lecture des photos d'une personne",
                           corps={"personIds": list(personnes), "size": 1000, "page": page, "withPeople": True}).json()
            yield from r["assets"]["items"]
            suite = r["assets"].get("nextPage")
            page = int(suite) if suite else 0

    def album_de(self, photo: str) -> str:
        """Le nom du premier album qui contient la photo ; vide si elle n'est dans aucun."""
        albums = self._lire("/albums", "la lecture des albums d'une photo", assetId=photo).json()
        return albums[0].get("albumName", "") if albums else ""

    def image(self, chemin: str, quoi: str, **params) -> tuple[bytes, str]:
        r = self._lire(chemin, quoi, **params)
        return r.content, r.headers.get("content-type", "image/jpeg")
