"""Sillage : le chemin de vie d'une personne, lu dans Immich. Lecture seule.

Routes : /health (publique), /api/session, /api/connexion, /api/deconnexion, /api/personnes,
/api/chemin/{personne} (et /marque), /api/recit/{personne}, /api/portrait/{personne}, /api/vignette/{photo}, /api/services, puis l'interface.
"""
from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import httpx
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from . import __version__, chemin as calcul, recit as recits
from .base import SORTES, Base
from .auth import COMMUN, DUREE, Sessions
from .config import APPLI, Config, charger
from .immich import ErreurImmich, Immich

ETAT: dict = {}
PUBLIQUES = ("/api/connexion", "/api/session")
IMAGES = ("/api/portrait/", "/api/vignette/")
MEMOIRE = 600            # secondes pendant lesquelles un chemin ou la liste des personnes est gardé
UUID = re.compile(r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
VERROU = threading.Lock()
log = logging.getLogger("sillage")


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
                personnes=None, lues={}, albums={}, connues={}, derniere_lecture=None,
                base=Base(cfg.data / "sillage.db"))
    yield
    ETAT["base"].fermer()


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

def _de_carnet() -> tuple[dict[str, dict], str]:
    """Les fiches de carnet liées à une personne d'Immich : identifiant Immich → fiche. Une lecture seule,
    avec le jeton de Sillage. Rend aussi la raison quand carnet ne répond pas (alors : Immich seul)."""
    cfg = ETAT["cfg"]
    if not cfg.carnet_jeton:
        return {}, ""
    try:
        with httpx.Client(timeout=10, transport=ETAT.get("carnet_transport")) as client:
            r = client.get(cfg.carnet_url + "/sillage/personnes", headers={"Authorization": f"Bearer {cfg.carnet_jeton}"})
        if r.status_code == 401:
            return {}, "carnet refuse le jeton de Sillage."
        r.raise_for_status()
        return {p["immich_id"]: p for p in r.json()["personnes"] if p.get("immich_id")}, ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        log.warning("carnet ne répond pas : %s", exc.__class__.__name__)
        return {}, "carnet ne répond pas."


def _personnes(frais: bool = False) -> dict[str, dict]:
    """Les personnes que Sillage connaît, gardées dix minutes : celles des fiches de carnet liées à Immich,
    et les personnes nommées et non masquées d'Immich. Le nom de la fiche passe devant celui d'Immich ;
    la date de naissance est toujours celle d'Immich."""
    garde_ = ETAT["personnes"]
    if garde_ and not frais and time.monotonic() - garde_[0] < MEMOIRE:
        return garde_[1]
    fiches, erreur = _de_carnet()
    liste = {}
    for p in ETAT["immich"].personnes():
        fiche = fiches.get(p["id"])
        if fiche:
            liste[p["id"]] = {**p, "name": fiche.get("nom") or p.get("name") or "", "carnet": True,
                              "proche": bool(fiche.get("proche")), "decede": bool(fiche.get("decede"))}
        elif (p.get("name") or "").strip() and not p.get("isHidden"):
            liste[p["id"]] = {**p, "carnet": False}
    ETAT["personnes"] = (time.monotonic(), liste)
    ETAT["carnet"] = {"regle": bool(ETAT["cfg"].carnet_jeton), "erreur": erreur, "fiches": len(fiches)}
    ETAT["derniere_lecture"] = time.time()
    return liste


@app.get("/api/personnes")
def personnes(frais: bool = False):
    """La liste d'ouverture. Avec carnet : ses fiches d'abord, les autres personnes d'Immich se trouvent par la recherche."""
    aujourd_hui = date.today()
    sortie = []
    for p in _personnes(frais).values():
        naissance = calcul.jour(p.get("birthDate"))
        sortie.append({"id": p["id"], "nom": p["name"].strip(), "naissance": naissance.isoformat() if naissance else None,
                       "age": calcul.age(naissance, aujourd_hui) if naissance and not p.get("decede") else None,
                       "carnet": bool(p.get("carnet")), "proche": bool(p.get("proche")), "decede": bool(p.get("decede"))})
    par_carnet = any(p["carnet"] for p in sortie)
    return {"personnes": sorted(sortie, key=lambda p: calcul._plat(p["nom"])), "par_carnet": par_carnet,
            "carnet": ETAT.get("carnet", {})}


def _noms_d_albums(photos: list[str]) -> dict[str, str]:
    """Le nom d'album de chaque photo phare, lu une fois puis gardé (huit lectures de front)."""
    connus: dict[str, str] = ETAT["albums"]
    a_lire = [p for p in photos if p not in connus]
    if a_lire:
        with ThreadPoolExecutor(max_workers=8) as file_:
            for photo, nom in zip(a_lire, file_.map(ETAT["immich"].album_de, a_lire)):
                connus[photo] = nom
    return {p: connus[p] for p in photos if connus.get(p)}


def _chemin(personne: str, frais: bool = False) -> dict:
    """Le chemin d'une personne. Les photos lues dans Immich sont gardées dix minutes : une correction
    recalcule le chemin sans rien relire."""
    fiche = _personnes().get(personne)
    if not fiche:
        raise HTTPException(404, "Personne inconnue de Sillage.")
    garde_ = ETAT["lues"].get(personne)
    if not garde_ or frais or time.monotonic() - garde_[0] > MEMOIRE:
        if frais:
            ETAT["albums"].clear()
        garde_ = (time.monotonic(), list(ETAT["immich"].photos_de(personne)))
        with VERROU:
            ETAT["lues"][personne] = garde_
            ETAT["connues"].update({p["id"]: p.get("checksum") or "" for p in garde_[1] if calcul.visible(p)})
    resultat = calcul.calculer(fiche, garde_[1], _noms_d_albums, ETAT["cfg"].mots, ETAT["base"].marques(personne), ETAT["cfg"].muets)
    resultat["immich"] = ETAT["cfg"].immich_adresse
    resultat["immich_port"] = ETAT["cfg"].immich_port
    return resultat


@app.get("/api/chemin/{personne}")
def chemin(personne: str, frais: bool = False):
    return _chemin(personne, frais)


@app.post("/api/chemin/{personne}/marque")
def marquer(personne: str, corps: dict = Body(...)):
    """Une correction : « ce n'est pas elle », retirer une photo, choisir la photo phare, nommer ou masquer une étape.
    `effacer` : les photos dont on retire la marque ; `poser` : la photo qui la reçoit (aucune : on ne fait que retirer).
    Rien n'est écrit dans Immich."""
    if personne not in _personnes():
        raise HTTPException(404, "Personne inconnue de Sillage.")
    sorte, valeur = str(corps.get("sorte", "")), str(corps.get("valeur") or "").strip()[:200]
    if sorte not in SORTES:
        raise HTTPException(422, "Correction inconnue.")
    connues = ETAT["connues"]
    demandees = [str(i) for i in (corps.get("effacer") or [])] + ([str(corps["poser"])] if corps.get("poser") else [])
    if not demandees or any(not connues.get(i) for i in demandees):
        raise HTTPException(404, "Photo inconnue de Sillage : relis le chemin.")
    if sorte == "titre" and corps.get("poser") and not valeur:
        raise HTTPException(422, "Le nom est vide.")
    ETAT["base"].marquer(personne, sorte, [connues[str(i)] for i in (corps.get("effacer") or [])],
                         connues[str(corps["poser"])] if corps.get("poser") else None, valeur)
    return _chemin(personne)


# ================================================================ raconter

@app.get("/api/recit/{personne}")
def recit(personne: str):
    propose = recits.proposer(_chemin(personne))
    garde_ = ETAT["base"].recit(personne)
    return {"texte": garde_["texte"] if garde_ else propose, "propose": propose, "garde_le": garde_["le"] if garde_ else None}


@app.put("/api/recit/{personne}")
def garder_recit(personne: str, corps: dict = Body(...)):
    if personne not in _personnes():
        raise HTTPException(404, "Personne inconnue de Sillage.")
    texte = corps.get("texte")
    if texte is not None and (not isinstance(texte, str) or len(texte) > 100_000):
        raise HTTPException(422, "Texte refusé.")
    ETAT["base"].garder_recit(personne, texte)
    return recit(personne)


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
                       "lecture_seule": True},
            "carnet": ETAT.get("carnet", {"regle": bool(ETAT["cfg"].carnet_jeton), "erreur": "", "fiches": 0})}


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
