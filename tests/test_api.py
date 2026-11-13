"""Sillage contre un faux Immich : le chemin est juste, rien n'est écrit, rien de caché n'est montré."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import chemin as calcul
from app import main
from app.config import Config
from app.immich import ErreurImmich, Immich

from .faux_immich import ANONYME, CACHEE, CAMILLE, HUGO, FauxImmich, ident

MDP = "essai-essai-essai"


@pytest.fixture
def monde(tmp_path):
    faux = FauxImmich()
    main.ETAT.clear()
    main.ETAT.update(cfg=Config(password=MDP, immich_url="http://immich", immich_cle="cle", data=tmp_path,
                                static=tmp_path / "static", immich_adresse="http://photos.exemple", attente_connexion=False),
                     immich=Immich("http://immich", "cle", transport=faux.transport()))
    with TestClient(main.app) as c:
        yield c, faux


@pytest.fixture
def c(monde):
    client, _ = monde
    assert client.post("/api/connexion", json={"mot_de_passe": MDP}).status_code == 200
    return client


def etapes(reponse):
    return [e for ch in reponse["chapitres"] for e in ch["etapes"]]


def test_rien_sans_mot_de_passe(monde):
    client, faux = monde
    assert client.get("/health").json()["ok"] is True
    for adresse in ("/api/personnes", f"/api/chemin/{CAMILLE}", f"/api/portrait/{CAMILLE}", f"/api/vignette/{ident('plage')}", "/api/services"):
        assert client.get(adresse).status_code == 401
    assert client.post("/api/connexion", json={"mot_de_passe": "mauvais-mot-de-passe"}).status_code == 401
    assert faux.demandes == []


def test_les_personnes_nommees_et_visibles(c):
    liste = c.get("/api/personnes").json()["personnes"]
    assert [p["nom"] for p in liste] == ["Camille ROUSSEL", "Hugo MARCHAND"]
    assert liste[0]["naissance"] == "1987-03-14" and liste[0]["age"] >= 39 and liste[1]["age"] is None


def test_le_chemin_de_camille(c):
    r = c.get(f"/api/chemin/{CAMILLE}").json()
    assert [ch["titre"] for ch in r["chapitres"]] == ["0 à 9 ans", "30 à 39 ans"]
    bapteme, plage, mariage = etapes(r)
    assert (bapteme["nom"], bapteme["nombre"], bapteme["age"], bapteme["temps_fort"]) == ("Baptême de Camille", 3, 0, True)
    assert bapteme["phare"] == ident("bapteme2")                       # le plus grand visage, pas la vidéo
    assert [p["video"] for p in bapteme["photos"]] == [False, False, True]
    assert (plage["nom"], plage["nombre"], plage["age"], plage["temps_fort"]) == ("", 1, 8, False)
    assert (mariage["nom"], mariage["debut"], mariage["fin"], mariage["age"]) == ("Mariage de Camille et Hugo", "2019-06-15", "2019-06-16", 32)
    assert r["etapes"] == 3 and r["photos"] == 6
    assert r["ecartees"] == {"avant_naissance": 1, "sans_date": 0}
    assert r["immich"] == "http://photos.exemple"


def test_ni_corbeille_ni_archive_ni_verrou(c):
    r = c.get(f"/api/chemin/{CAMILLE}").json()
    montrees = {p["id"] for e in etapes(r) for p in e["photos"]}
    for cachee in ("corbeille", "archive", "verrou", "avant"):
        assert ident(cachee) not in montrees
        assert c.get(f"/api/vignette/{ident(cachee)}").status_code == 404


def test_sans_naissance_les_chapitres_sont_des_annees(c):
    r = c.get(f"/api/chemin/{HUGO}").json()
    assert [ch["titre"] for ch in r["chapitres"]] == ["2001", "2002"]
    assert all(e["age"] is None for e in etapes(r))


def test_personnes_hors_liste(c):
    for inconnue in (ANONYME, CACHEE, ident("personne"), "n-importe-quoi"):
        assert c.get(f"/api/chemin/{inconnue}").status_code == 404
        assert c.get(f"/api/portrait/{inconnue}").status_code == 404


def test_les_images_passent_par_sillage(monde, c):
    _, faux = monde
    assert c.get(f"/api/vignette/{ident('plage')}").status_code == 404   # chemin pas encore calculé
    c.get(f"/api/chemin/{CAMILLE}")
    r = c.get(f"/api/vignette/{ident('plage')}")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and "private" in r.headers["cache-control"]
    assert c.get(f"/api/vignette/{ident('plage')}?grande=true").status_code == 200
    assert c.get(f"/api/portrait/{CAMILLE}").status_code == 200
    assert c.get("/api/vignette/../../people").status_code in (401, 404)
    assert ("GET", f"/assets/{ident('plage')}/thumbnail") in faux.demandes


def test_le_chemin_est_garde_en_memoire(monde, c):
    _, faux = monde
    c.get(f"/api/chemin/{CAMILLE}")
    avant = len(faux.demandes)
    c.get(f"/api/chemin/{CAMILLE}")
    assert len(faux.demandes) == avant
    c.get(f"/api/chemin/{CAMILLE}?frais=true")
    assert len(faux.demandes) > avant


def test_aucune_ecriture_ne_part_vers_immich(monde, c):
    _, faux = monde
    c.get("/api/personnes"); c.get(f"/api/chemin/{CAMILLE}"); c.get(f"/api/chemin/{HUGO}"); c.get("/api/services")
    c.get(f"/api/portrait/{CAMILLE}"); c.get(f"/api/vignette/{ident('plage')}")
    assert faux.demandes
    assert {(m, ch) for m, ch in faux.demandes if m != "GET"} <= {("POST", "/search/metadata")}
    with pytest.raises(ErreurImmich):
        main.ETAT["immich"]._lire("/albums", "un essai", corps={"albumName": "interdit"})
    # Et dans le code : le client ne connaît que GET et POST, aucune autre méthode n'est écrite.
    source = Path(main.__file__).with_name("immich.py").read_text(encoding="utf-8")
    appels = {n.func.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not appels & {"put", "patch", "delete", "request", "stream"}


def test_immich_qui_refuse_ou_se_tait(monde, c):
    _, faux = monde
    faux.refuse = 401
    r = c.get("/api/personnes")
    assert r.status_code == 502 and "clé" in r.json()["detail"]
    s = c.get("/api/services").json()["immich"]
    assert s["repond"] is False and s["erreur"]
    faux.refuse = 0
    s = c.get("/api/services").json()["immich"]
    assert (s["repond"], s["version"], s["personnes"]) == (True, "3.4.1", 2)


def test_deconnexion(c):
    assert c.post("/api/deconnexion").status_code == 200
    assert c.get("/api/personnes").status_code == 401


def test_decoupage():
    from datetime import date, datetime
    assert calcul.age(date(1987, 3, 14), date(2019, 3, 13)) == 31 and calcul.age(date(1987, 3, 14), date(2019, 3, 14)) == 32
    assert calcul.nom_du_dossier({"originalPath": "/a/2019-06-15 Mariage/IMG.jpg"}) == "Mariage"
    assert calcul.nom_du_dossier({"originalPath": "/a/2019/2019-06-15/IMG.jpg"}) == ""
    assert calcul.nom_du_dossier({"originalPath": "IMG.jpg"}) == ""
    jours = [(datetime(2020, 1, j), {"id": str(j)}) for j in (1, 2, 4, 7, 8, 20)]
    assert [len(g) for g in calcul.grouper(jours)] == [3, 2, 1]
    assert calcul.date_de({"localDateTime": "n'importe quoi"}) is None
