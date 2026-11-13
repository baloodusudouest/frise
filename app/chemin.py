"""Le chemin d'une personne : ses photos rangées en étapes, les étapes en chapitres d'âge.

Une étape est un groupe de photos proches en dates (moins de deux jours entre deux photos qui se
suivent). Elle porte le nom de l'album de sa photo phare, à défaut celui de son dossier, à défaut
sa date. Rien ici ne parle à Immich : les fonctions reçoivent ce qui a été lu."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Callable, Iterable

ECART = timedelta(days=2)
MOTS = ("mariage", "noces", "bapteme", "communion", "anniversaire", "diplome", "remise", "naissance",
        "noel", "vacances", "voyage", "fete")
_DATE_EN_TETE = re.compile(r"^[\s\d._/-]+")


def _plat(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn")


def visible(photo: dict) -> bool:
    """Ce qui est à la corbeille, archivé, masqué ou verrouillé dans Immich n'est pas montré."""
    return (not photo.get("isTrashed") and not photo.get("isArchived")
            and photo.get("visibility") in (None, "timeline"))


def date_de(photo: dict) -> datetime | None:
    brut = photo.get("localDateTime") or photo.get("fileCreatedAt") or ""
    try:
        return datetime.fromisoformat(brut.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def jour(texte: str | None) -> date | None:
    try:
        return date.fromisoformat((texte or "")[:10])
    except ValueError:
        return None


def age(naissance: date, le: date) -> int:
    return le.year - naissance.year - ((le.month, le.day) < (naissance.month, naissance.day))


def nom_du_dossier(photo: dict) -> str:
    """Le nom du dossier qui porte la photo, sans sa date de tête ; vide s'il ne dit rien."""
    morceaux = (photo.get("originalPath") or "").replace("\\", "/").split("/")
    if len(morceaux) < 2:
        return ""
    nom = _DATE_EN_TETE.sub("", morceaux[-2]).strip(" -_")
    return nom if re.search(r"[^\W\d_]{3}", nom) else ""


def _taille_du_visage(photo: dict, personne: str) -> float:
    plus_grand = 0.0
    for p in photo.get("people") or []:
        if p.get("id") != personne:
            continue
        for v in p.get("faces") or []:
            surface = (v.get("imageWidth") or 0) * (v.get("imageHeight") or 0)
            if surface:
                plus_grand = max(plus_grand, abs((v["boundingBoxX2"] - v["boundingBoxX1"])
                                                 * (v["boundingBoxY2"] - v["boundingBoxY1"])) / surface)
    return plus_grand


def photo_phare(groupe: list[dict], personne: str) -> dict:
    """Le plus grand visage de la personne dans le groupe ; une image plutôt qu'une vidéo."""
    return max(groupe, key=lambda p: (p.get("type") != "VIDEO", _taille_du_visage(p, personne), bool(p.get("isFavorite"))))


def grouper(photos: Iterable[tuple[datetime, dict]]) -> list[list[tuple[datetime, dict]]]:
    groupes: list[list[tuple[datetime, dict]]] = []
    for quand, photo in sorted(photos, key=lambda x: x[0]):
        if groupes and quand - groupes[-1][-1][0] <= ECART:
            groupes[-1].append((quand, photo))
        else:
            groupes.append([(quand, photo)])
    return groupes


def calculer(personne: dict, photos: Iterable[dict], noms_d_albums: Callable[[list[str]], dict[str, str]],
             mots: tuple[str, ...] = ()) -> dict:
    """Le chemin complet. `noms_d_albums` reçoit des identifiants de photos phares et rend, pour
    celles qui sont dans un album, le nom de cet album."""
    mots = tuple(_plat(m) for m in (mots or MOTS))
    naissance = jour(personne.get("birthDate"))
    datees, sans_date, avant = [], 0, 0
    for p in photos:
        if not visible(p):
            continue
        quand = date_de(p)
        if quand is None:
            sans_date += 1
        elif naissance and quand.date() < naissance:
            avant += 1
        else:
            datees.append((quand, p))

    etapes = []
    for groupe in grouper(datees):
        phare = photo_phare([p for _, p in groupe], personne["id"])
        etapes.append({"debut": groupe[0][0], "fin": groupe[-1][0], "phare": phare,
                       "photos": [{"id": p["id"], "video": p.get("type") == "VIDEO"} for _, p in groupe]})
    albums = noms_d_albums([e["phare"]["id"] for e in etapes if len(e["photos"]) > 1])

    chapitres: list[dict] = []
    for e in etapes:
        debut = e["debut"].date()
        nom = albums.get(e["phare"]["id"]) or nom_du_dossier(e["phare"])
        ans = age(naissance, debut) if naissance else None
        if ans is None:
            cle, titre = str(debut.year), str(debut.year)
        else:
            dizaine = ans // 10 * 10
            cle, titre = f"age-{dizaine}", f"{dizaine} à {dizaine + 9} ans"
        if not chapitres or chapitres[-1]["cle"] != cle:
            chapitres.append({"cle": cle, "titre": titre, "etapes": []})
        chapitres[-1]["etapes"].append({
            "cle": f"{e['debut']:%Y%m%d%H%M%S}", "nom": nom, "debut": debut.isoformat(), "fin": e["fin"].date().isoformat(),
            "age": ans, "nombre": len(e["photos"]), "phare": e["phare"]["id"],
            "temps_fort": bool(nom) and any(m in _plat(nom) for m in mots), "photos": e["photos"]})
    return {
        "personne": {"id": personne["id"], "nom": personne.get("name") or "", "naissance": naissance.isoformat() if naissance else None},
        "chapitres": chapitres,
        "etapes": sum(len(c["etapes"]) for c in chapitres), "photos": len(datees),
        "ecartees": {"avant_naissance": avant, "sans_date": sans_date},
    }
