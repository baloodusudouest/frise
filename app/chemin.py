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
# Une date en tête de nom de dossier : « 2004 », « 2004-04 », « 2004-04-01 », « 20040401 », « 01-04-2004 ».
# Seulement une vraie date : « 50 ans de mariage » garde son nombre.
_MOIS, _JOUR = r"(?:0?[1-9]|1[0-2])", r"(?:0?[1-9]|[12]\d|3[01])"
_DATE_EN_TETE = re.compile(rf"^(?:(?:19|20)\d{{2}}(?:[-._/]{_MOIS}(?:[-._/]{_JOUR})?)?|(?:19|20)\d{{6}}|{_JOUR}[-._/]{_MOIS}[-._/](?:19|20)\d{{2}})(?=$|[\s_\-–—])")


def sans_date_en_tete(nom: str) -> str:
    """Retire la ou les dates qui ouvrent le nom (« 2004-04-01 - 2004-04-03 Voyage » → « Voyage »)."""
    nom = nom.strip()
    for _ in range(2):
        court = _DATE_EN_TETE.sub("", nom, count=1)
        if court == nom:
            break
        nom = re.sub(r"^(?:[\s_\-–—]+|au\s+|et\s+)+", "", court)
    return nom.strip(" -_–—")


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


MUETS = ("dcim", "camera", "camera roll", "pellicule", "photos", "images", "pictures", "upload", "library", "import",
         "mobilebackup", "whatsapp images", "screenshots", "captures", "divers", "vrac", "nouveau dossier", "new folder")


def nom_du_dossier(photo: dict, muets: tuple[str, ...] = ()) -> str:
    """Le nom du dossier qui porte la photo, sans sa date de tête ; vide s'il ne dit rien
    (une date seule, un nom d'appareil, un dossier fourre-tout)."""
    morceaux = (photo.get("originalPath") or "").replace("\\", "/").split("/")
    if len(morceaux) < 2:
        return ""
    brut = morceaux[-2].strip()
    nom = sans_date_en_tete(brut)
    sourds = {_plat(m) for m in MUETS + tuple(muets)}
    if re.fullmatch(r"\d{3}[A-Za-z_]{3,8}", brut) or _plat(brut) in sourds or _plat(nom) in sourds:   # « 100APPLE », « DCIM »
        return ""
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


def majuscule(nom: str) -> str:
    """La première lettre en majuscule, le reste tel qu'il est écrit (« noël chez mamie » → « Noël chez mamie »)."""
    nom = nom.strip()
    return nom[:1].upper() + nom[1:]


def _plus_frequent(noms: list[str]) -> str:
    noms = [n for n in noms if n]
    return max(noms, key=lambda n: (noms.count(n), -noms.index(n))) if noms else ""


def calculer(personne: dict, photos: Iterable[dict], noms_d_albums: Callable[[list[str]], dict[str, str]],
             mots: tuple[str, ...] = (), marques: dict[str, dict[str, str]] | None = None,
             muets: tuple[str, ...] = ()) -> dict:
    """Le chemin complet. `noms_d_albums` reçoit des identifiants de photos et rend, pour celles qui sont dans un
    album, le nom de cet album. `marques` : les corrections faites à la main, par empreinte de fichier."""
    mots = tuple(_plat(m) for m in (mots or MOTS))
    marques = marques or {}
    marque = lambda p: marques.get(p.get("checksum") or "", {})
    naissance = jour(personne.get("birthDate"))
    datees, sans_date, avant, de_cote = [], 0, 0, []
    for p in photos:
        if not visible(p):
            continue
        m = marque(p)
        if "pas_elle" in m or "retiree" in m:
            de_cote.append({"id": p["id"], "sorte": "pas_elle" if "pas_elle" in m else "retiree", "video": p.get("type") == "VIDEO"})
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
        du_groupe = [p for _, p in groupe]
        choisie = next((p for p in du_groupe if "phare" in marque(p)), None)
        etapes.append({"debut": groupe[0][0], "fin": groupe[-1][0], "phare": choisie or photo_phare(du_groupe, personne["id"]),
                       "phare_choisie": choisie is not None, "groupe": du_groupe,
                       "titre": next((marque(p)["titre"] for p in du_groupe if marque(p).get("titre")), ""),
                       "masquee": any("masquee" in marque(p) for p in du_groupe)})
    # Le nom vient de l'album : celui de la photo phare, de la première et de la dernière, le plus fréquent des trois.
    temoins = {id(e): list(dict.fromkeys(p["id"] for p in (e["phare"], e["groupe"][0], e["groupe"][-1]))) for e in etapes}
    albums = noms_d_albums([i for e in etapes if not e["titre"] for i in temoins[id(e)]])

    chapitres: list[dict] = []
    masquees = 0
    for e in etapes:
        debut = e["debut"].date()
        propose = _plus_frequent([albums.get(i, "") for i in temoins[id(e)]]) or nom_du_dossier(e["phare"], muets)
        nom = majuscule(e["titre"] or propose)
        ans = age(naissance, debut) if naissance else None
        if ans is None:
            cle, titre = str(debut.year), str(debut.year)
        else:
            dizaine = ans // 10 * 10
            cle, titre = f"age-{dizaine}", f"{dizaine} à {dizaine + 9} ans"
        if not chapitres or chapitres[-1]["cle"] != cle:
            chapitres.append({"cle": cle, "titre": titre, "etapes": []})
        masquees += e["masquee"]
        chapitres[-1]["etapes"].append({
            "cle": f"{e['debut']:%Y%m%d%H%M%S}", "nom": nom, "nom_choisi": bool(e["titre"]), "debut": debut.isoformat(),
            "fin": e["fin"].date().isoformat(), "age": ans, "nombre": len(e["groupe"]), "phare": e["phare"]["id"],
            "phare_choisie": e["phare_choisie"], "masquee": e["masquee"],
            "temps_fort": bool(nom) and (bool(e["titre"]) or any(m in _plat(nom) for m in mots)),
            "photos": [{"id": p["id"], "video": p.get("type") == "VIDEO"} for p in e["groupe"]]})
    return {
        "personne": {"id": personne["id"], "nom": personne.get("name") or "", "naissance": naissance.isoformat() if naissance else None},
        "chapitres": chapitres,
        "etapes": sum(len(c["etapes"]) for c in chapitres) - masquees, "masquees": masquees, "photos": len(datees),
        "ecartees": {"avant_naissance": avant, "sans_date": sans_date}, "de_cote": de_cote,
    }
