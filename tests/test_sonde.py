"""Tests de la sonde contre un faux Immich : mesures justes, aucun nom dans le rapport, refus tolérés."""
import importlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "sonde"))

PERSONNES = [
    {"id": "p-camille", "name": "Camille ROUSSEL", "birthDate": "1987-03-14", "isHidden": False},
    {"id": "p-hugo", "name": "Hugo MARCHAND", "birthDate": None, "isHidden": False},
    {"id": "p-mamie", "name": "Mamie", "birthDate": None, "isHidden": False},
    {"id": "p-anonyme", "name": "", "birthDate": None, "isHidden": True},
]


def photo(i, chemin, jour, type_="IMAGE"):
    return {"id": f"a{i}", "type": type_, "originalPath": chemin, "localDateTime": f"{jour}T12:00:00.000Z"}


PHOTOS = {
    "p-camille": [
        photo(1, "/synologyphotos/Pellicule/2019/06/2019-06-15 Mariage Camille et Hugo/IMG_1.jpg", "2019-06-15"),
        photo(2, "/synologyphotos/Pellicule/2019/06/2019-06-15 Mariage Camille et Hugo/IMG_2.jpg", "2019-06-16"),
        photo(3, "/synologyphotos/Pellicule/2019/06/2019-06-15 Mariage Camille et Hugo/IMG_3.jpg", "2019-07-30"),
        photo(4, "/synologyphotos/Pellicule/2020/12/Noël chez Mamie/IMG_4.jpg", "2020-12-25"),
        photo(5, "/synologyphotos/Pellicule/2020/12/Noël chez Mamie/VID_5.mp4", "2021-01-02", "VIDEO"),
        photo(6, "/synologyphotos/Albums/Vrac/IMG_6.jpg", "2015-05-01"),
    ],
    "p-hugo": [photo(7, "/synologyphotos/Pellicule/2019/06/2019-06-15 Mariage Camille et Hugo/IMG_1.jpg", "2019-06-15")],
    "p-mamie": [],
}
DOSSIERS = [
    "/synologyphotos/Pellicule/2019/06/2019-06-15 Mariage Camille et Hugo",
    "/synologyphotos/Pellicule/2018/05/2018-05-02 Mariage Louise",
    "/synologyphotos/Pellicule/2017/09/2017-09-09 Mariage Noé",
    "/synologyphotos/Pellicule/2020/12/Noël chez Mamie",
    "/synologyphotos/Albums/Vrac",
]
REFUS: set = set()


class FauxImmich(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, corps, statut=200):
        donnees = json.dumps(corps).encode()
        self.send_response(statut)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(donnees)))
        self.end_headers()
        self.wfile.write(donnees)

    def _route(self):
        u = urlparse(self.path)
        chemin, q = u.path.removeprefix("/api"), parse_qs(u.query)
        if self.headers.get("x-api-key") != "cle-de-test":
            return self._json({"message": "non"}, 401)
        if chemin in REFUS:
            return self._json({"message": "interdit"}, 403)
        if chemin == "/server/version":
            return self._json({"major": 2, "minor": 3, "patch": 1})
        if chemin == "/users/me":
            return self._json({"isAdmin": False})
        if chemin == "/people":
            return self._json({"people": PERSONNES, "hasNextPage": False})
        if chemin.startswith("/people/") and chemin.endswith("/statistics"):
            return self._json({"assets": len(PHOTOS.get(chemin.split("/")[2], []))})
        if chemin == "/view/folder/unique-paths":
            return self._json(DOSSIERS)
        if chemin == "/search/metadata":
            corps = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            return self._json({"assets": {"items": PHOTOS[corps["personIds"][0]], "nextPage": None}})
        if chemin.startswith("/assets/") and chemin.endswith("/thumbnail"):
            self.send_response(200)
            self.send_header("Content-Length", "2048")
            self.end_headers()
            return self.wfile.write(b"x" * 2048)
        if chemin == "/faces":
            return self._json([{"boundingBoxX1": 1, "boundingBoxY1": 1, "boundingBoxX2": 9, "boundingBoxY2": 9,
                                "imageWidth": 100, "imageHeight": 100, "person": {"name": "Camille ROUSSEL"}}])
        if chemin == "/albums":
            return self._json([{"id": "al1"}, {"id": "al2"}])
        return self._json({"message": "inconnu"}, 404)

    do_GET = do_POST = _route


@pytest.fixture()
def sonde(tmp_path, monkeypatch):
    serveur = ThreadingHTTPServer(("127.0.0.1", 0), FauxImmich)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    monkeypatch.setenv("IMMICH_URL", f"http://127.0.0.1:{serveur.server_port}")
    monkeypatch.setenv("IMMICH_API_KEY", "cle-de-test")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    REFUS.clear()
    sys.modules.pop("sonde", None)
    module = importlib.import_module("sonde")
    yield module, tmp_path
    serveur.shutdown()


def test_formes_et_dates(sonde):
    s, _ = sonde
    assert s.forme_chemin(DOSSIERS[0]) == "/synologyphotos/Pellicule/AAAA/MM/AAAA-MM-JJ texte"
    assert s.forme_chemin(DOSSIERS[3]) == "/synologyphotos/Pellicule/AAAA/MM/texte"
    assert s.date_du_dossier(DOSSIERS[0])[0] == "jour"
    assert s.date_du_dossier(DOSSIERS[3]) == ("mois", s.date(2020, 12, 1))
    assert s.date_du_dossier(DOSSIERS[4]) == (None, None)
    assert s.date_du_dossier("/a/b/2019-13-45 Faux")[0] is None or s.date_du_dossier("/a/b/2019-13-45 Faux")[0] == "annee"
    assert s.premier_mot(DOSSIERS[0]) == "mariage"


def test_rapport_complet_et_juste(sonde):
    s, dossier = sonde
    assert s.main() == 0
    r = json.loads((dossier / "rapport-sonde-frise.json").read_text(encoding="utf-8"))["etapes"]
    assert all(e["ok"] for e in r.values())
    assert r["serveur"]["version"] == "2.3.1"
    assert r["personnes"] == {**r["personnes"], "total": 4, "nommees": 3, "nommees_avec_naissance": 1,
                              "nommees_format_prenom_NOM": 2, "nommees_un_seul_mot": 1, "masquees": 1}
    assert r["dossiers"]["precision_de_la_date"] == {"jour": 3, "mois": 1, "aucune date": 1}
    assert r["dossiers"]["premiers_mots_frequents"] == [{"mot": "mariage", "dossiers": 3}]
    p1 = r["personnes_detail"]["personnes"][0]
    assert p1["photos_lues"] == 6 and p1["videos"] == 1
    assert p1["dossiers_distincts"] == 3 and p1["evenements_dates"] == 2
    assert (p1["dossier_au_jour_comparables"], p1["ecart_de_plus_de_1_jour"], p1["ecart_de_plus_de_7_jours"]) == (3, 1, 1)
    assert (p1["dossier_au_mois_comparables"], p1["mois_different"]) == (2, 1)
    assert r["visages"]["visages_avec_cadre"] == r["visages"]["visages"] == 5
    assert r["albums"]["albums"] == 2


def test_aucun_nom_dans_le_rapport(sonde):
    s, dossier = sonde
    s.main()
    for fichier in ("rapport-sonde-frise.md", "rapport-sonde-frise.json"):
        texte = (dossier / fichier).read_text(encoding="utf-8")
        for interdit in ("Camille", "ROUSSEL", "Hugo", "MARCHAND", "Mamie", "Louise", "Vrac", "p-camille", "cle-de-test"):
            assert interdit not in texte, f"« {interdit} » apparaît dans {fichier}"


def test_un_refus_n_arrete_pas_la_sonde(sonde):
    s, dossier = sonde
    REFUS.add("/view/folder/unique-paths")
    assert s.main() == 0
    r = json.loads((dossier / "rapport-sonde-frise.json").read_text(encoding="utf-8"))["etapes"]
    assert r["dossiers"]["ok"] is False and r["dossiers"]["statut"] == 403
    assert r["personnes_detail"]["ok"] and r["albums"]["ok"]
    assert "HTTP 403" in (dossier / "rapport-sonde-frise.md").read_text(encoding="utf-8")


def test_cle_refusee(sonde, monkeypatch):
    s, dossier = sonde
    s.S.headers["x-api-key"] = "mauvaise"
    assert s.main() == 0
    r = json.loads((dossier / "rapport-sonde-frise.json").read_text(encoding="utf-8"))["etapes"]
    assert r["cle"]["statut"] == 401 and "personnes" not in r
