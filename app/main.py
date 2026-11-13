"""Sillage : le chemin de vie d'une personne, lu dans Immich. Lecture seule.

Routes : /health (publique), /api/session, /api/connexion, /api/deconnexion, /api/personnes,
/api/chemin/{personne}, /api/portrait/{personne}, /api/vignette/{photo}, /api/services, puis l'interface.
"""
from __future__ import annotations

import asyncio
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from . import __version__, chemin as calcul
from .auth import COMMUN, DUREE, Sessions
from .config import APPLI, Config, charger
from .immich import ErreurImmich, Immich

ETAT: dict = {}
PUBLIQUES = ("/api/connexion", "/api/session")
IMAGES = ("/api/portrait/", "/api/vignette/")
MEMOIRE = 600            # secondes pendant lesquelles un chemin ou la liste des personnes est gardé
UUID = re.compile(r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
VERROU = threading.Lock()


def _fichier_generation(cfg: Config) -> Path:
    return cfg.data / "session_generation"


def _lire_generation(cfg: Config) -> int:
    try:
        return int(_fichier_generation(cfg).read_text().strip())
    except (OSError, ValueError):
        return 0


@asynccontextmanager
async def cycle(app: FastAPI):
    cfg = ETAT.get("cfg") or charger()
    cfg.data.mkdir(parents=True, exist_ok=True)
    ETAT.setdefault("immich", Immich(cfg.immich_url, cfg.immich_cle))
    ETAT.update(cfg=cfg, sessions=Sessions(APPLI, cfg.password, _lire_generation(cfg)),
                personnes=None, chemins={}, albums={}, connues=set(), derniere_lecture=None)
    yield


app = FastAPI(title=APPLI, version=__version__, lifespan=cycle, docs_url=None, redoc_url=None)


@app.middleware("http")
async def garde(request: Request, appel):
    chemin = request.url.path
    if chemin.startswith("/api/") and chemin not in PUBLIQUES \
            and not ETAT["sessions"].connecte(request.cookies):
        return JSONResponse({"detail": "Connexion nécessaire."}, status_code=401)
    reponse = await appel(request)
    if chemin.startswith("/api/") and not chemin.startswith(IMAGES):
        reponse.headers["Cache-Control"] = "no-store"
    return reponse


@app.exception_handler(ErreurImmich)
async def _immich(_: Request, exc: ErreurImmich):
    return JSONResponse({"detail": str(exc)}, status_code=502)


@app.get("/health")
def sante():
    return {"ok": True, "version": __version__}


# ================================================================ connexion

@app.get("/api/session")
def session(request: Request):
    s = ETAT["sessions"]
    return {"connecte": s.connecte(request.cookies), "version": __version__}


@app.post("/api/connexion")
async def connexion(corps: dict = Body(...)):
    s = ETAT["sessions"]
    if ETAT["cfg"].attente_connexion:
        await asyncio.sleep(s.attente())
    if not s.verifier_mot_de_passe(str(corps.get("mot_de_passe", ""))):
        raise HTTPException(401, "Mot de passe incorrect.")
    r = JSONResponse({"ok": True})
    r.set_cookie(s.cookie, s.creer(), max_age=DUREE, httponly=True, samesite="strict")
    return r


@app.post("/api/deconnexion")
def deconnexion():
    s = ETAT["sessions"]
    s.generation += 1
    try:
        _fichier_generation(ETAT["cfg"]).write_text(str(s.generation))
    except OSError:
        pass
    r = JSONResponse({"ok": True})
    r.delete_cookie(s.cookie)
    r.delete_cookie(COMMUN)      # « Se déconnecter » ferme aussi la connexion commune
    return r


# ================================================================ personnes

def _personnes(frais: bool = False) -> dict[str, dict]:
    """Les personnes nommées et non masquées d'Immich, gardées dix minutes."""
    garde_ = ETAT["personnes"]
    if garde_ and not frais and time.monotonic() - garde_[0] < MEMOIRE:
        return garde_[1]
    liste = {p["id"]: p for p in ETAT["immich"].personnes() if (p.get("name") or "").strip() and not p.get("isHidden")}
    ETAT["personnes"] = (time.monotonic(), liste)
    ETAT["derniere_lecture"] = time.time()
    return liste


@app.get("/api/personnes")
def personnes(frais: bool = False):
    aujourd_hui = date.today()
    sortie = []
    for p in _personnes(frais).values():
        naissance = calcul.jour(p.get("birthDate"))
        sortie.append({"id": p["id"], "nom": p["name"].strip(), "naissance": naissance.isoformat() if naissance else None,
                       "age": calcul.age(naissance, aujourd_hui) if naissance else None})
    return {"personnes": sorted(sortie, key=lambda p: calcul._plat(p["nom"]))}


def _noms_d_albums(photos: list[str]) -> dict[str, str]:
    """Le nom d'album de chaque photo phare, lu une fois puis gardé (huit lectures de front)."""
    connus: dict[str, str] = ETAT["albums"]
    a_lire = [p for p in photos if p not in connus]
    if a_lire:
        with ThreadPoolExecutor(max_workers=8) as file_:
            for photo, nom in zip(a_lire, file_.map(ETAT["immich"].album_de, a_lire)):
                connus[photo] = nom
    return {p: connus[p] for p in photos if connus.get(p)}


@app.get("/api/chemin/{personne}")
def chemin(personne: str, frais: bool = False):
    fiche = _personnes().get(personne)
    if not fiche:
        raise HTTPException(404, "Personne inconnue de Sillage.")
    garde_ = ETAT["chemins"].get(personne)
    if garde_ and not frais and time.monotonic() - garde_[0] < MEMOIRE:
        return garde_[1]
    if frais:
        ETAT["albums"].clear()
    resultat = calcul.calculer(fiche, ETAT["immich"].photos_de(personne), _noms_d_albums, ETAT["cfg"].mots)
    resultat["immich"] = ETAT["cfg"].immich_adresse
    with VERROU:
        ETAT["connues"].update(p["id"] for c in resultat["chapitres"] for e in c["etapes"] for p in e["photos"])
        ETAT["chemins"][personne] = (time.monotonic(), resultat)
    return resultat


# ================================================================ images (derrière la session)

def _image(contenu: bytes, sorte: str) -> Response:
    return Response(contenu, media_type=sorte, headers={"Cache-Control": "private, max-age=86400"})


@app.get("/api/portrait/{personne}")
def portrait(personne: str):
    if personne not in _personnes():
        raise HTTPException(404, "Personne inconnue de Sillage.")
    return _image(*ETAT["immich"].image(f"/people/{personne}/thumbnail", "la lecture d'un portrait"))


@app.get("/api/vignette/{photo}")
def vignette(photo: str, grande: bool = False):
    """Seules les photos d'un chemin déjà calculé sont servies : Sillage n'ouvre pas tout Immich."""
    if not UUID.match(photo) or photo not in ETAT["connues"]:
        raise HTTPException(404, "Photo inconnue de Sillage.")
    return _image(*ETAT["immich"].image(f"/assets/{photo}/thumbnail", "la lecture d'une image",
                                         size="preview" if grande else "thumbnail"))


# ================================================================ services

@app.get("/api/services")
def services():
    try:
        version, erreur = ETAT["immich"].version(), ""
        nombre = len(_personnes(frais=True))
    except ErreurImmich as exc:
        version, erreur, nombre = "", str(exc), 0
    return {"immich": {"repond": not erreur, "version": version, "erreur": erreur, "personnes": nombre,
                       "lecture_seule": True}}


# ================================================================ interface

@app.get("/{chemin:path}")
def interface(chemin: str):
    statique = ETAT["cfg"].static
    fichier = (statique / chemin).resolve() if chemin else None
    if fichier and fichier.is_file() and statique.resolve() in fichier.parents:
        return FileResponse(fichier)
    index = statique / "index.html"
    if index.is_file():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return JSONResponse({"detail": "Interface non compilée."}, status_code=404)
