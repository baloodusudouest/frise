#!/usr/bin/env python3
"""
Frise — étape 0 : sonde d'Immich (lecture seule).

Répond, avec les vraies données, aux questions dont dépend la conception de Frise :
  1. La clé d'API suffit-elle ? Quelle version d'Immich ?
  2. Combien de personnes nommées, avec ou sans date de naissance ?
  3. Comment les dossiers sont-ils réellement nommés (« AAAA-MM-JJ évènement » ou autre) ?
  4. Pour une personne : combien de photos, combien d'évènements, sur combien d'années,
     et la date du dossier concorde-t-elle avec la date de la photo ?
  5. Combien de temps prennent les lectures (liste d'une personne, vignettes) ?
  6. Les visages ont-ils un cadre exploitable pour recadrer la photo phare ?

Rien n'est écrit dans Immich. Le rapport ne contient ni nom de personne, ni nom de dossier :
les personnes sont notées P1, P2… et les dossiers réduits à leur forme (« AAAA-MM-JJ texte »).
Seule exception, désactivable (MOTS_EVENEMENTS=0) : le premier mot des dossiers d'évènement
quand il revient au moins 3 fois (mariage, anniversaire, noël…).

Variables : IMMICH_URL, IMMICH_API_KEY, DATA_DIR, PERSONNES_ECHANTILLON,
MAX_PHOTOS_PAR_PERSONNE, MOTS_EVENEMENTS.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path, PurePosixPath

import requests

__version__ = "0.1.1"

URL = os.environ.get("IMMICH_URL", "http://immich_server:2283").rstrip("/")
CLE = os.environ.get("IMMICH_API_KEY", "")
DATA = Path(os.environ.get("DATA_DIR", "/data"))
ECHANTILLON = int(os.environ.get("PERSONNES_ECHANTILLON", "10"))
MAX_PHOTOS = int(os.environ.get("MAX_PHOTOS_PAR_PERSONNE", "5000"))
MOTS = os.environ.get("MOTS_EVENEMENTS", "1") == "1"
RACINE_LITTERALE = 2          # segments de tête gardés tels quels (ex. /synologyphotos/Pellicule)

S = requests.Session()
S.headers.update({"x-api-key": CLE, "Accept": "application/json"})


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


class Refus(Exception):
    def __init__(self, statut: int, chemin: str):
        super().__init__(f"HTTP {statut} sur {chemin}")
        self.statut = statut


def brut(methode: str, chemin: str, **kw) -> requests.Response:
    """Un appel à Immich, réessayé 2 fois sur un raté passager."""
    for essai in range(3):
        try:
            r = S.request(methode, f"{URL}/api{chemin}", timeout=120, **kw)
        except requests.RequestException:
            if essai == 2:
                raise
            time.sleep(2 * (essai + 1))
            continue
        if r.status_code >= 500 and essai < 2:
            time.sleep(2 * (essai + 1))
            continue
        if r.status_code >= 400:
            raise Refus(r.status_code, chemin)
        return r
    raise RuntimeError("inatteignable")


def api(methode: str, chemin: str, **kw):
    return brut(methode, chemin, **kw).json()


# ----------------------------------------------------------------- formes de dossiers

MOIS = r"(0[1-9]|1[0-2])"
JOUR = r"(0[1-9]|[12]\d|3[01])"
FORMES = [
    ("AAAA-MM-JJ texte", re.compile(rf"^(\d{{4}})[-_. ]{MOIS}[-_. ]{JOUR}[-_. ]+\S.*$")),
    ("AAAA-MM-JJ", re.compile(rf"^(\d{{4}})[-_. ]{MOIS}[-_. ]{JOUR}$")),
    ("AAAA-MM texte", re.compile(rf"^(\d{{4}})[-_. ]{MOIS}[-_. ]+\D.*$")),
    ("AAAA-MM", re.compile(rf"^(\d{{4}})[-_. ]{MOIS}$")),
    ("AAAA texte", re.compile(r"^(\d{4})[-_. ]+\D.*$")),
    ("AAAA", re.compile(r"^(\d{4})$")),
    ("MM texte", re.compile(rf"^{MOIS}[-_. ]+\D.*$")),
    ("MM", re.compile(rf"^{MOIS}$")),
]


def forme_segment(segment: str) -> str:
    for nom, motif in FORMES:
        if motif.match(segment):
            return nom
    return "texte"


def forme_chemin(dossier: str) -> str:
    """/racine/Pellicule/2019/06/Mariage de X → /racine/Pellicule/AAAA/MM/texte"""
    segments = [s for s in PurePosixPath(dossier).parts if s != "/"]
    tete = segments[:RACINE_LITTERALE]
    return "/" + "/".join(tete + [forme_segment(s) for s in segments[RACINE_LITTERALE:]])


def date_du_dossier(dossier: str):
    """Date portée par le chemin et sa précision : ('jour'|'mois'|'annee', date) ou (None, None)."""
    annee = mois = jour = None
    for s in [x for x in PurePosixPath(dossier).parts if x != "/"][RACINE_LITTERALE:]:
        f = forme_segment(s)
        chiffres = [int(x) for x in re.findall(r"\d+", s)]
        if f.startswith("AAAA-MM-JJ"):
            annee, mois, jour = chiffres[:3]
        elif f.startswith("AAAA-MM"):
            annee, mois, jour = chiffres[0], chiffres[1], None
        elif f.startswith("AAAA"):
            annee, mois, jour = chiffres[0], None, None
        elif f.startswith("MM") and annee and not mois:
            mois = chiffres[0]
    if not annee or not 1800 <= annee <= date.today().year + 1:
        return None, None
    try:
        if jour:
            return "jour", date(annee, mois, jour)
        if mois:
            return "mois", date(annee, mois, 1)
        return "annee", date(annee, 1, 1)
    except ValueError:
        return None, None


def premier_mot(dossier: str) -> str | None:
    """Premier mot du nom d'évènement, sans la date : « 2019-06-15 Mariage de X » → « mariage »."""
    nom = PurePosixPath(dossier).name
    texte = re.sub(r"^[\d\-_. ]+", "", nom)
    m = re.match(r"[^\W\d_]{3,}", texte)
    return m.group(0).lower() if m else None


def date_asset(a: dict):
    for cle in ("localDateTime", "fileCreatedAt"):
        v = a.get(cle)
        if v:
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
            except ValueError:
                continue
    return None


def med(valeurs):
    return round(statistics.median(valeurs), 1) if valeurs else None


# ----------------------------------------------------------------- étapes

RAPPORT: dict = {"sonde": __version__, "date": datetime.now().isoformat(timespec="seconds"), "etapes": {}}


def etape(cle: str, titre: str, fonction):
    """Lance une étape, la chronomètre, et note un refus sans arrêter la sonde."""
    log(titre + "…")
    t = time.monotonic()
    try:
        resultat = {"ok": True, **(fonction() or {})}
    except Refus as r:
        resultat = {"ok": False, "erreur": str(r), "statut": r.statut}
        log(f"  refusé : {r}")
    except Exception as e:  # noqa: BLE001 — la sonde doit aller au bout
        resultat = {"ok": False, "erreur": f"{type(e).__name__}: {e}"}
        log(f"  échec : {resultat['erreur']}")
    resultat["secondes"] = round(time.monotonic() - t, 2)
    RAPPORT["etapes"][cle] = resultat
    return resultat


PERSONNES: list = []
ECHANT: list = []          # [(étiquette, id, nb photos annoncé)]
PHOTOS_P1: list = []


def e_serveur():
    v = api("GET", "/server/version")
    return {"version": f"{v.get('major')}.{v.get('minor')}.{v.get('patch')}"}


def e_cle():
    moi = api("GET", "/users/me")
    return {"admin": bool(moi.get("isAdmin"))}


def e_personnes():
    page = 1
    while True:
        bloc = api("GET", "/people", params={"page": page, "size": 1000, "withHidden": "true"})
        PERSONNES.extend(bloc.get("people", []))
        if not bloc.get("hasNextPage"):
            break
        page += 1
    nommees = [p for p in PERSONNES if (p.get("name") or "").strip()]
    prenom_nom = re.compile(r"^\S.*\s[^\Wa-z\d_][^a-z]*$")       # dernier mot tout en capitales
    return {
        "total": len(PERSONNES),
        "nommees": len(nommees),
        "sans_nom": len(PERSONNES) - len(nommees),
        "masquees": sum(1 for p in PERSONNES if p.get("isHidden")),
        "nommees_avec_naissance": sum(1 for p in nommees if p.get("birthDate")),
        "nommees_format_prenom_NOM": sum(1 for p in nommees if prenom_nom.match(p["name"].strip())),
        "nommees_un_seul_mot": sum(1 for p in nommees if len(p["name"].split()) == 1),
    }


def e_volumes():
    nommees = [p for p in PERSONNES if (p.get("name") or "").strip() and not p.get("isHidden")][:600]
    comptes = []
    for i, p in enumerate(nommees, 1):
        try:
            comptes.append((api("GET", f"/people/{p['id']}/statistics").get("assets", 0), p["id"]))
        except Refus as r:
            if r.statut != 403 or comptes:
                raise
            # Droit « person.statistics » absent : on étudie quand même un échantillon, pris à intervalles réguliers
            pas = max(1, len(nommees) // max(1, ECHANTILLON))
            for j, q in enumerate(nommees[::pas][:ECHANTILLON], 1):
                ECHANT.append((f"P{j}", q["id"], None))
            log("  comptage par personne refusé (droit person.statistics) : échantillon pris sans classement")
            return {"comptage_refuse": True, "personnes_comptees": 0}
        if i % 100 == 0:
            log(f"  {i}/{len(nommees)} personnes comptées")
    comptes.sort(reverse=True)
    n = [c for c, _ in comptes]
    # Échantillon : les plus photographiées, puis des personnes « moyennes »
    haut = comptes[: (ECHANTILLON + 1) // 2]
    milieu_debut = max(len(haut), len(comptes) // 2 - ECHANTILLON // 4)
    milieu = [c for c in comptes[milieu_debut: milieu_debut + ECHANTILLON // 2] if c[0] > 0]
    for i, (nb, pid) in enumerate(haut + milieu, 1):
        ECHANT.append((f"P{i}", pid, nb))
    return {
        "personnes_comptees": len(n),
        "photos_max": n[0] if n else 0,
        "photos_mediane": med(n),
        "plus_de_1000_photos": sum(1 for x in n if x > 1000),
        "de_100_a_1000": sum(1 for x in n if 100 <= x <= 1000),
        "de_10_a_99": sum(1 for x in n if 10 <= x < 100),
        "moins_de_10": sum(1 for x in n if x < 10),
    }


def e_dossiers():
    chemins = api("GET", "/view/folder/unique-paths")
    formes = Counter(forme_chemin(c) for c in chemins)
    precision = Counter((date_du_dossier(c)[0] or "aucune date") for c in chemins)
    mots = Counter()
    if MOTS:
        for c in chemins:
            if date_du_dossier(c)[0] in ("jour", "mois"):
                m = premier_mot(c)
                if m:
                    mots[m] += 1
    return {
        "dossiers": len(chemins),
        "precision_de_la_date": dict(precision),
        "formes_les_plus_frequentes": [{"forme": f, "dossiers": n} for f, n in formes.most_common(20)],
        "premiers_mots_frequents": [{"mot": m, "dossiers": n} for m, n in mots.most_common(40) if n >= 3],
    }


def photos_de(pid: str) -> tuple[list, int]:
    photos, page, pages = [], 1, 0
    while page and len(photos) < MAX_PHOTOS:
        bloc = api("POST", "/search/metadata", json={"personIds": [pid], "page": page, "size": 250})["assets"]
        photos += bloc.get("items", [])
        pages += 1
        page = int(bloc["nextPage"]) if bloc.get("nextPage") else None
    return photos[:MAX_PHOTOS], pages


def e_personnes_detail():
    lignes = []
    for etiquette, pid, annonce in ECHANT:
        t = time.monotonic()
        photos, pages = photos_de(pid)
        duree = round(time.monotonic() - t, 2)
        if etiquette == "P1":
            PHOTOS_P1.extend(photos)
        par_dossier: dict = {}
        jours_par_dossier: dict = {}
        precision = Counter()
        ecart_1j = ecart_7j = comparables = mois_faux = mois_comparables = sans_chemin = 0
        annees = set()
        for a in photos:
            chemin = a.get("originalPath")
            d = date_asset(a)
            if d:
                annees.add(d.year)
            if not chemin:
                sans_chemin += 1
                continue
            dossier = str(PurePosixPath(chemin).parent)
            par_dossier[dossier] = par_dossier.get(dossier, 0) + 1
            if d:
                jours_par_dossier.setdefault(dossier, []).append(d)
            p, dd = date_du_dossier(dossier)
            precision[p or "aucune date"] += 1
            if d and p == "jour":
                comparables += 1
                ecart = abs((d - dd).days)
                ecart_1j += ecart > 1
                ecart_7j += ecart > 7
            elif d and p == "mois":
                mois_comparables += 1
                mois_faux += (d.year, d.month) != (dd.year, dd.month)
        evenements = [n for dossier, n in par_dossier.items() if date_du_dossier(dossier)[0] in ("jour", "mois")]
        durees = [(max(j) - min(j)).days + 1 for j in jours_par_dossier.values()]
        lignes.append({
            "personne": etiquette,
            "duree_dossier_jours_mediane": med(durees),
            "dossiers_de_3_jours_ou_moins": sum(1 for x in durees if x <= 3),
            "dossiers_de_4_a_30_jours": sum(1 for x in durees if 4 <= x <= 30),
            "dossiers_de_plus_de_30_jours": sum(1 for x in durees if x > 30),
            "photos_annoncees": annonce,
            "photos_lues": len(photos),
            "plafonnee": len(photos) >= MAX_PHOTOS,
            "videos": sum(1 for a in photos if a.get("type") == "VIDEO"),
            "secondes_lecture": duree,
            "pages": pages,
            "premiere_annee": min(annees) if annees else None,
            "derniere_annee": max(annees) if annees else None,
            "annees_couvertes": len(annees),
            "dossiers_distincts": len(par_dossier),
            "evenements_dates": len(evenements),
            "photos_par_evenement_mediane": med(evenements),
            "photos_par_evenement_max": max(evenements) if evenements else None,
            "photos_selon_precision_du_dossier": dict(precision),
            "photos_sans_chemin": sans_chemin,
            "dossier_au_jour_comparables": comparables,
            "ecart_de_plus_de_1_jour": ecart_1j,
            "ecart_de_plus_de_7_jours": ecart_7j,
            "dossier_au_mois_comparables": mois_comparables,
            "mois_different": mois_faux,
        })
        log(f"  {etiquette} : {len(photos)} photos lues en {duree} s")
    return {"personnes": lignes}


def e_vignettes():
    mesures = []
    for a in [x for x in PHOTOS_P1 if x.get("type") == "IMAGE"][:5]:
        for taille in ("thumbnail", "preview"):
            t = time.monotonic()
            r = brut("GET", f"/assets/{a['id']}/thumbnail", params={"size": taille})
            mesures.append((taille, round(1000 * (time.monotonic() - t)), len(r.content)))
    sortie = {}
    for taille in ("thumbnail", "preview"):
        m = [x for x in mesures if x[0] == taille]
        sortie[taille] = {"lues": len(m), "ms_mediane": med([x[1] for x in m]), "ko_mediane": med([round(x[2] / 1024) for x in m])}
    return sortie


def e_visages():
    photos = [x for x in PHOTOS_P1 if x.get("type") == "IMAGE"][:20]
    total = cadres = nommes = 0
    par_photo = []
    for a in photos:
        faces = api("GET", "/faces", params={"id": a["id"]})
        par_photo.append(len(faces))
        for f in faces:
            total += 1
            cadres += all(f.get(k) is not None for k in ("boundingBoxX1", "boundingBoxY1", "boundingBoxX2", "boundingBoxY2", "imageWidth", "imageHeight"))
            nommes += bool((f.get("person") or {}).get("name"))
    return {"photos_lues": len(photos), "visages": total, "visages_avec_cadre": cadres, "visages_nommes": nommes,
            "visages_par_photo_mediane": med(par_photo), "visages_par_photo_max": max(par_photo) if par_photo else None}


def e_albums():
    return {"albums": len(api("GET", "/albums"))}


# ----------------------------------------------------------------- rapport

def tableau(entetes: list, lignes: list) -> str:
    out = ["| " + " | ".join(entetes) + " |", "|" + "|".join("---" for _ in entetes) + "|"]
    out += ["| " + " | ".join("" if v is None else str(v) for v in ligne) + " |" for ligne in lignes]
    return "\n".join(out)


def rapport_md() -> str:
    e = RAPPORT["etapes"]
    md = [f"# Sonde Immich pour Frise — {RAPPORT['date'][:16].replace('T', ' ')}",
          "",
          f"Sonde {__version__}, lecture seule. Aucun nom de personne ni de dossier dans ce rapport"
          + (" (sauf les premiers mots fréquents des dossiers d'évènement)." if MOTS else "."), ""]

    md += ["## Déroulement", "", tableau(["Étape", "Résultat", "Durée (s)"], [
        [cle, "ok" if r["ok"] else r.get("erreur", "échec"), r["secondes"]] for cle, r in e.items()]), ""]

    def bloc(cle, titre, lignes):
        r = e.get(cle)
        if r and r["ok"]:
            md.extend([f"## {titre}", "", *lignes(r), ""])

    bloc("serveur", "Serveur", lambda r: [f"- Immich {r['version']}"])
    bloc("personnes", "Personnes", lambda r: [tableau(["Mesure", "Nombre"], [
        ["Personnes (visages regroupés)", r["total"]], ["Nommées", r["nommees"]], ["Sans nom", r["sans_nom"]],
        ["Masquées", r["masquees"]], ["Nommées avec date de naissance", r["nommees_avec_naissance"]],
        ["Nommées au format « Prénom NOM »", r["nommees_format_prenom_NOM"]],
        ["Nommées d'un seul mot", r["nommees_un_seul_mot"]]])])
    bloc("volumes", "Photos par personne nommée", lambda r: [
        "- Comptage refusé : il manque le droit `person.statistics` à la clé. L'échantillon ci-dessous est pris "
        "à intervalles réguliers, pas parmi les personnes les plus photographiées."] if r.get("comptage_refuse") else [tableau(["Mesure", "Valeur"], [
        ["Personnes comptées", r["personnes_comptees"]], ["Maximum", r["photos_max"]], ["Médiane", r["photos_mediane"]],
        ["Plus de 1 000 photos", r["plus_de_1000_photos"]], ["De 100 à 1 000", r["de_100_a_1000"]],
        ["De 10 à 99", r["de_10_a_99"]], ["Moins de 10", r["moins_de_10"]]])])
    bloc("dossiers", "Dossiers", lambda r: [
        f"- {r['dossiers']} dossiers contenant des photos.",
        "- Précision de la date portée par le chemin : "
        + ", ".join(f"{k} : {v}" for k, v in sorted(r["precision_de_la_date"].items(), key=lambda x: -x[1])) + ".",
        "", "### Formes de chemin les plus fréquentes", "",
        tableau(["Forme", "Dossiers"], [[f"`{x['forme']}`", x["dossiers"]] for x in r["formes_les_plus_frequentes"]]),
        *((["", "### Premiers mots des dossiers d'évènement (3 dossiers au moins)", "",
            ", ".join(f"{x['mot']} ({x['dossiers']})" for x in r["premiers_mots_frequents"]) or "Aucun."]) if MOTS else [])])
    bloc("personnes_detail", "Échantillon de personnes", lambda r: [
        tableau(["Pers.", "Photos lues", "Vidéos", "Lecture (s)", "Années", "Dossiers", "Évènements datés",
                 "Photos / évèn. (méd.)", "Photos / évèn. (max)"],
                [[p["personne"], f"{p['photos_lues']}{' (plafond)' if p['plafonnee'] else ''}", p["videos"], p["secondes_lecture"],
                  (f"{p['premiere_annee']}–{p['derniere_annee']} ({p['annees_couvertes']})" if p['annees_couvertes'] else "—"), p["dossiers_distincts"],
                  p["evenements_dates"], p["photos_par_evenement_mediane"], p["photos_par_evenement_max"]] for p in r["personnes"]]),
        "", "### Un dossier est-il un évènement ? (étendue des dates des photos de la personne dans chaque dossier)", "",
        tableau(["Pers.", "Dossiers", "Étendue médiane (j)", "3 jours ou moins", "4 à 30 jours", "Plus de 30 jours"],
                [[p["personne"], p["dossiers_distincts"], p["duree_dossier_jours_mediane"], p["dossiers_de_3_jours_ou_moins"],
                  p["dossiers_de_4_a_30_jours"], p["dossiers_de_plus_de_30_jours"]] for p in r["personnes"]]),
        "", "### Date du dossier contre date de la photo", "",
        tableau(["Pers.", "Dossier au jour", "Écart > 1 j", "Écart > 7 j", "Dossier au mois", "Mois différent",
                 "Dossier à l'année", "Sans date", "Sans chemin"],
                [[p["personne"], p["dossier_au_jour_comparables"], p["ecart_de_plus_de_1_jour"], p["ecart_de_plus_de_7_jours"],
                  p["dossier_au_mois_comparables"], p["mois_different"],
                  p["photos_selon_precision_du_dossier"].get("annee", 0),
                  p["photos_selon_precision_du_dossier"].get("aucune date", 0), p["photos_sans_chemin"]] for p in r["personnes"]])])
    bloc("vignettes", "Vitesse des images (personne P1)", lambda r: [tableau(["Taille", "Lues", "Temps médian (ms)", "Poids médian (Ko)"], [
        [k, r[k]["lues"], r[k]["ms_mediane"], r[k]["ko_mediane"]] for k in ("thumbnail", "preview")])])
    bloc("visages", "Visages (20 photos de P1)", lambda r: [
        f"- {r['visages']} visages sur {r['photos_lues']} photos, dont {r['visages_avec_cadre']} avec un cadre complet et {r['visages_nommes']} nommés.",
        f"- Visages par photo : médiane {r['visages_par_photo_mediane']}, maximum {r['visages_par_photo_max']}."])
    bloc("albums", "Albums", lambda r: [f"- {r['albums']} albums."])
    return "\n".join(md) + "\n"


def main() -> int:
    if not CLE:
        print("IMMICH_API_KEY est absente : la sonde ne peut pas lire Immich.", file=sys.stderr)
        return 2
    log(f"Sonde Frise {__version__} — {URL}")
    etape("serveur", "Version du serveur", e_serveur)
    if not etape("cle", "Clé d'API", e_cle)["ok"] and RAPPORT["etapes"]["cle"].get("statut") == 401:
        log("Clé d'API refusée (401) : rien d'autre ne peut être lu.")
    elif etape("personnes", "Personnes", e_personnes)["ok"]:
        if etape("volumes", "Photos par personne", e_volumes)["ok"] and ECHANT:
            if etape("personnes_detail", f"Détail de {len(ECHANT)} personnes", e_personnes_detail)["ok"] and PHOTOS_P1:
                etape("vignettes", "Vitesse des vignettes", e_vignettes)
                etape("visages", "Cadres des visages", e_visages)
    etape("dossiers", "Dossiers", e_dossiers)
    etape("albums", "Albums", e_albums)

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "rapport-sonde-frise.json").write_text(json.dumps(RAPPORT, ensure_ascii=False, indent=2), encoding="utf-8")
    md = rapport_md()
    (DATA / "rapport-sonde-frise.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    log(f"Rapport écrit dans {DATA}/rapport-sonde-frise.md — la sonde s'arrête.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
