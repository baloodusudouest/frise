"""Sillage : le chemin de vie d'une personne, lu dans Immich. Lecture seule.

Routes : /health (publique), /api/session, /api/connexion, /api/deconnexion, /api/personnes,
/api/chemin/{personne} (et /marque), /api/recit/{personne}, /api/portrait/{personne}, /api/vignette/{photo}, /api/services, puis l'interface.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
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
                personnes=None, lues={}, albums={}, connues={}, derniere_lecture=None, toutes=None, invites={},
                base=Base(cfg.data / "sillage.db"))
    yield
    ETAT["base"].fermer()


app = FastAPI(title=APPLI, version=__version__, lifespan=cycle, docs_url=None, redoc_url=None)


@app.middleware("http")
async def garde(request: Request, appel):
    chemin = request.url.path
    if chemin.startswith("/ha/"):
        # 0.5 : Home Assistant prépare les invitations des chambres, avec son propre jeton
        jeton = ETAT["cfg"].jeton_ha
        if not jeton or not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {jeton}"):
            return JSONResponse({"detail": "Jeton manquant ou invalide."}, status_code=401)
    elif chemin.startswith("/api/") and chemin not in PUBLIQUES and not chemin.startswith("/api/invite/") \
            and not ETAT["sessions"].connecte(request.cookies):
        return JSONResponse({"detail": "Connexion nécessaire."}, status_code=401)
    reponse = await appel(request)
    if chemin.startswith(("/api/", "/ha/")) and not chemin.startswith(IMAGES) and "/vignette/" not in chemin:
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


# ================================================================ invités des chambres (0.5)

def _toutes() -> list[dict]:
    """Toutes les personnes nommées d'Immich (masquées comprises), gardées dix minutes : pour retrouver un invité."""
    garde_ = ETAT["toutes"]
    if not garde_ or time.monotonic() - garde_[0] > MEMOIRE:
        garde_ = (time.monotonic(), [p for p in ETAT["immich"].personnes() if (p.get("name") or "").strip()])
        ETAT["toutes"] = garde_
    return garde_[1]


def _trouver(nom: str) -> dict | None:
    """La personne d'Immich qui porte exactement ce nom (comme l'intégration des chambres : à l'identique,
    puis sans accents ni majuscules). Deux personnes du même nom : aucune, on ne devine pas."""
    import unicodedata
    voulu = unicodedata.normalize("NFC", nom.strip())
    for egal in (lambda p: unicodedata.normalize("NFC", p["name"].strip()) == voulu,
                 lambda p: calcul._plat(p["name"].strip()) == calcul._plat(voulu)):
        trouves = [p for p in _toutes() if egal(p)]
        if len(trouves) == 1:
            return trouves[0]
        if len(trouves) > 1:
            return None
    return None


@app.post("/ha/sejour")
def sejour(corps: dict = Body(...)):
    """Home Assistant prépare l'invitation d'une chambre pour son séjour : les noms des invités, le dernier jour.
    Rend le chemin de la page à afficher (/invite/<jeton>), valable jusqu'au lendemain midi. Sans nom : l'invitation
    de la chambre est retirée. Rien n'est écrit dans Immich."""
    chambre = str(corps.get("chambre", "")).strip()[:40]
    if not chambre:
        raise HTTPException(422, "Chambre manquante.")
    noms = [str(n).strip() for n in (corps.get("noms") or []) if str(n).strip()][:4]
    if not noms:
        ETAT["base"].retirer_invites(chambre)
        return {"chemin": "", "trouves": [], "manquants": [], "expire": None}
    try:
        dernier = date.fromisoformat(str(corps.get("jusqu_au", ""))[:10])
    except ValueError:
        raise HTTPException(422, "Date de fin illisible (AAAA-MM-JJ).")
    if not date.today() <= dernier <= date.today() + timedelta(days=400):
        raise HTTPException(422, "Date de fin hors du séjour possible.")
    expire = datetime.combine(dernier + timedelta(days=1), datetime.min.time()).replace(hour=12).isoformat(timespec="seconds")
    trouves, manquants = [], []
    for n in noms:
        p = _trouver(n)
        (trouves.append({"id": p["id"], "nom": n}) if p else manquants.append(n))
    jeton = ETAT["base"].poser_invite(chambre, trouves or [{"id": "", "nom": n} for n in noms], expire)
    ETAT["invites"].pop(jeton, None)
    return {"chemin": f"/invite/{jeton}", "trouves": [t["nom"] for t in trouves], "manquants": manquants, "expire": expire}


def _pour_invite(c: dict) -> dict:
    """Ce qu'un invité voit d'un chemin : les étapes visibles, la photo phare de chacune. Ni corrections,
    ni photos mises de côté, ni lien vers Immich."""
    chapitres = []
    for ch in c["chapitres"]:
        etapes = [{k: e[k] for k in ("cle", "nom", "debut", "fin", "age", "nombre", "phare", "temps_fort")}
                  for e in ch["etapes"] if not e["masquee"]]
        if etapes:
            chapitres.append({"cle": ch["cle"], "titre": ch["titre"], "etapes": etapes})
    return {"nom": c["personne"]["nom"], "chapitres": chapitres, "etapes": sum(len(ch["etapes"]) for ch in chapitres)}


def _invitation(jeton: str) -> dict:
    inv = ETAT["base"].invite(jeton)
    if not inv:
        raise HTTPException(404, "Cette invitation n'existe pas ou a expiré.")
    garde_ = ETAT["invites"].get(jeton)
    if garde_ and time.monotonic() - garde_[0] < MEMOIRE:
        return garde_[1]
    gens = [p for p in inv["personnes"] if p["id"]]
    fiches = {p["id"]: p for p in _toutes()}
    lire_marques = ETAT["base"].marques
    cfg = ETAT["cfg"]

    def seul(g):
        fiche = {**fiches.get(g["id"], {"id": g["id"]}), "name": g["nom"]}
        return calcul.calculer(fiche, ETAT["immich"].photos_de(g["id"]), _noms_d_albums, cfg.mots, lire_marques(g["id"]), cfg.muets)

    commun, chacun = None, []
    if len(gens) > 1:
        marques: dict = {}
        for g in gens:
            for empreinte, m in lire_marques(g["id"]).items():
                marques.setdefault(empreinte, {}).update(m)
        noms = [g["nom"] for g in gens]
        fiche = {"id": gens[0]["id"], "name": ", ".join(noms[:-1]) + " et " + noms[-1]}
        c = _pour_invite(calcul.calculer(fiche, ETAT["immich"].photos_ensemble([g["id"] for g in gens]), _noms_d_albums,
                                          cfg.mots, marques, cfg.muets, decennies=True))
        commun = c if c["etapes"] else None
    if commun is None:
        chacun = [c for c in (_pour_invite(seul(g)) for g in gens) if c["etapes"]]
    resultat = {"invites": [p["nom"] for p in inv["personnes"]], "commun": commun, "chacun": chacun,
                "accueil": commun is None and not chacun}
    phares = {e["phare"] for c in ([commun] if commun else []) + chacun for ch in c["chapitres"] for e in ch["etapes"]}
    ETAT["invites"][jeton] = (time.monotonic(), {**resultat, "_phares": phares})
    return ETAT["invites"][jeton][1]


@app.get("/api/invite/{jeton}")
def invitation(jeton: str):
    return {k: v for k, v in _invitation(jeton).items() if not k.startswith("_")}


@app.get("/api/invite/{jeton}/vignette/{photo}")
def vignette_invite(jeton: str, photo: str):
    """Seules les photos phares du chemin de l'invitation sont servies."""
    if not UUID.match(photo) or photo not in _invitation(jeton)["_phares"]:
        raise HTTPException(404, "Photo inconnue de cette invitation.")
    return _image(*ETAT["immich"].image(f"/assets/{photo}/thumbnail", "la lecture d'une image", size="preview"))


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
