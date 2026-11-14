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

from .faux_immich import ANONYME, CACHEE, CAMILLE, HOTE, HUGO, FauxImmich, ident, photo

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
    assert r["immich"] == "http://photos.exemple" and r["immich_port"] == 0


def test_ni_corbeille_ni_archive_ni_verrou(c):
    r = c.get(f"/api/chemin/{CAMILLE}").json()
    montrees = {p["id"] for e in etapes(r) for p in e["photos"]}
    assert ident("avant") not in montrees
    for cachee in ("corbeille", "archive", "verrou"):
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


def marque(c, **corps):
    r = c.post(f"/api/chemin/{CAMILLE}/marque", json=corps)
    assert r.status_code == 200, r.text
    return r.json()


def test_corrections(monde, c):
    _, faux = monde
    c.get(f"/api/chemin/{CAMILLE}")
    lus = len(faux.demandes)
    # Nommer une étape : elle devient un temps fort, et son nom n'est plus cherché dans les albums
    r = marque(c, sorte="titre", poser=ident("plage"), valeur="Été à la mer")
    plage = etapes(r)[1]
    assert (plage["nom"], plage["nom_choisi"], plage["temps_fort"]) == ("Été à la mer", True, True)
    assert marque(c, sorte="titre", effacer=[ident("plage")])["chapitres"][0]["etapes"][1]["nom"] == ""
    # Choisir la photo phare
    r = marque(c, sorte="phare", effacer=[ident("bapteme1"), ident("bapteme2"), ident("bapteme3")], poser=ident("bapteme1"))
    assert (etapes(r)[0]["phare"], etapes(r)[0]["phare_choisie"]) == (ident("bapteme1"), True)
    # « Ce n'est pas elle » et « retirer » : la photo quitte le chemin, on peut la remettre
    r = marque(c, sorte="pas_elle", poser=ident("mariage1"))
    assert etapes(r)[2]["nombre"] == 1 and r["de_cote"] == [{"id": ident("mariage1"), "sorte": "pas_elle", "video": False}]
    r = marque(c, sorte="retiree", poser=ident("bapteme3"))
    assert etapes(r)[0]["nombre"] == 2 and len(r["de_cote"]) == 2
    assert c.get(f"/api/vignette/{ident('mariage1')}").status_code == 200           # toujours visible dans « mises de côté »
    r = marque(c, sorte="pas_elle", effacer=[ident("mariage1")])
    assert etapes(r)[2]["nombre"] == 2
    # Masquer une étape : elle reste dans la réponse, marquée, et ne compte plus
    r = marque(c, sorte="masquee", poser=ident("plage"))
    assert etapes(r)[1]["masquee"] is True and (r["etapes"], r["masquees"]) == (2, 1)
    # Rien de tout cela n'a relu les photos ni écrit dans Immich
    assert not [d for d in faux.demandes[lus:] if d == ("POST", "/search/metadata")]
    assert {m for m, _ in faux.demandes} <= {"GET", "POST"} and {ch for m, ch in faux.demandes if m == "POST"} == {"/search/metadata"}


def test_les_corrections_suivent_l_empreinte(monde, c):
    """La photo est renvoyée dans Immich (migration) : nouvel identifiant, même fichier. La correction tient."""
    _, faux = monde
    c.get(f"/api/chemin/{CAMILLE}")
    marque(c, sorte="titre", poser=ident("plage"), valeur="Été à la mer")
    marque(c, sorte="retiree", poser=ident("mariage1"))
    for p in faux.photos[CAMILLE]:
        p["id"] = ident("apres-migration-" + p["originalPath"])
    r = c.get(f"/api/chemin/{CAMILLE}?frais=true").json()
    assert etapes(r)[1]["nom"] == "Été à la mer" and etapes(r)[2]["nombre"] == 1 and len(r["de_cote"]) == 1


def test_corrections_refusees(c):
    c.get(f"/api/chemin/{CAMILLE}")
    for corps, code in (({"sorte": "n-importe-quoi", "poser": ident("plage")}, 422), ({"sorte": "retiree"}, 404),
                        ({"sorte": "retiree", "poser": ident("inconnue")}, 404), ({"sorte": "retiree", "poser": ident("corbeille")}, 404),
                        ({"sorte": "titre", "poser": ident("plage"), "valeur": "  "}, 422)):
        assert c.post(f"/api/chemin/{CAMILLE}/marque", json=corps).status_code == code, corps
    assert c.post(f"/api/chemin/{ident('personne')}/marque", json={"sorte": "retiree", "poser": ident("plage")}).status_code == 404


def test_le_nom_vient_de_l_album_le_plus_frequent_puis_du_dossier():
    photos = [{"id": str(i), "checksum": str(i), "type": "IMAGE", "localDateTime": f"2020-05-0{1 + i // 3}T10:0{i}:00.000Z",
               "originalPath": f"/p/{dossier}/{i}.jpg", "visibility": "timeline", "people": []}
              for i, dossier in enumerate(("DCIM", "100APPLE", "2020-05 Fête au jardin", "Pellicule", "Camera", "Divers"))]
    noms = lambda ids: {"0": "Un album", "5": "Un album", "3": "Autre"}
    r = calcul.calculer({"id": "x", "name": "X"}, photos, noms)
    assert [e["nom"] for ch in r["chapitres"] for e in ch["etapes"]] == ["Un album"]
    r = calcul.calculer({"id": "x", "name": "X"}, photos[:3], lambda ids: {})
    assert [e["nom"] for ch in r["chapitres"] for e in ch["etapes"]] == [""]         # phare = première image : « DCIM » ne dit rien
    r = calcul.calculer({"id": "x", "name": "X"}, photos[:1], lambda ids: {"0": "noël chez mamie"})
    assert [e["nom"] for ch in r["chapitres"] for e in ch["etapes"]] == ["Noël chez mamie"]      # majuscule d'office, reste intact
    assert calcul.majuscule("  été à la mer ") == "Été à la mer" and calcul.majuscule("") == "" and calcul.majuscule("iPhone de Léa") == "IPhone de Léa"
    for dossier, attendu in (("2004-04-01 50 ans de mariage pépé mémé", "50 ans de mariage pépé mémé"), ("2004 50 ans de mariage", "50 ans de mariage"),
                             ("2019-06 Mariage", "Mariage"), ("20190615 Mariage", "Mariage"), ("15-06-2019 Mariage", "Mariage"),
                             ("2004-04-01 - 2004-04-03 Voyage à Rome", "Voyage à Rome"), ("2004-04-01 au 2004-04-03 Voyage", "Voyage"),
                             ("18 ans de Léa", "18 ans de Léa"), ("2010 12 ans de Léa", "12 ans de Léa"), ("3 jours à Paris", "3 jours à Paris"),
                             ("1er mai", "1er mai"), ("2019", ""), ("2019-06-15", ""), ("2019_06_15_Fête", "Fête")):
        assert calcul.nom_du_dossier({"originalPath": f"/a/{dossier}/x.jpg"}) == attendu, dossier
    for muet in ("DCIM", "100APPLE", "Pellicule", "2019", "2020-05-01"):
        assert calcul.nom_du_dossier({"originalPath": f"/a/{muet}/x.jpg"}) == "", muet
    assert calcul.nom_du_dossier({"originalPath": "/a/Mon dossier/x.jpg"}, muets=("mon dossier",)) == ""


def test_raconter(c):
    marque_ = lambda **k: marque(c, **k)
    c.get(f"/api/chemin/{CAMILLE}")
    r = c.get(f"/api/recit/{CAMILLE}").json()
    assert r["garde_le"] is None and r["texte"] == r["propose"]
    assert r["propose"] == (
        "Camille ROUSSEL\n\nNaissance le 14 mars 1987.\n\n"
        "0 à 9 ans\nDu 7 au 8 juin 1987, avant un an : Baptême de Camille.\nEt 1 autre moment en photos.\n\n"
        "30 à 39 ans\nDu 15 au 16 juin 2019, à 32 ans : Mariage de Camille et Hugo.\n")
    marque_(sorte="masquee", poser=ident("plage"))
    assert "autre moment" not in c.get(f"/api/recit/{CAMILLE}").json()["propose"]      # une étape masquée ne se raconte pas
    r = c.put(f"/api/recit/{CAMILLE}", json={"texte": "Mon texte relu."}).json()
    assert r["texte"] == "Mon texte relu." and r["garde_le"] and r["propose"].startswith("Camille ROUSSEL")
    assert c.get(f"/api/recit/{CAMILLE}").json()["texte"] == "Mon texte relu."
    assert c.put(f"/api/recit/{CAMILLE}", json={"texte": None}).json()["garde_le"] is None   # repartir du chemin
    assert c.put(f"/api/recit/{CAMILLE}", json={"texte": 12}).status_code == 422
    assert c.put(f"/api/recit/{ident('personne')}", json={"texte": "x"}).status_code == 404


def avec_carnet(reponse):
    """Sillage réglé pour lire carnet, et un faux carnet qui répond `reponse` (code, corps)."""
    import dataclasses

    import httpx
    vues = []

    def repondre(demande):
        vues.append((demande.method, demande.url.path, demande.headers.get("authorization")))
        return httpx.Response(reponse[0], json=reponse[1])
    main.ETAT["cfg"] = dataclasses.replace(main.ETAT["cfg"], carnet_url="http://carnet", carnet_jeton="jeton-sillage")
    main.ETAT["carnet_transport"] = httpx.MockTransport(repondre)
    main.ETAT["personnes"] = None
    return vues


def test_les_personnes_viennent_de_carnet(c):
    vues = avec_carnet((200, {"personnes": [
        {"carnet_id": "f1", "nom": "Camille R.", "immich_id": CAMILLE, "groupes": ["Famille"], "proche": True, "decede": False},
        {"carnet_id": "f2", "nom": "Tante Lise", "immich_id": CACHEE, "groupes": [], "proche": False, "decede": True},
        {"carnet_id": "f3", "nom": "Fiche sans personne", "immich_id": ident("disparue"), "groupes": [], "proche": False, "decede": False}]}))
    r = c.get("/api/personnes").json()
    assert vues == [("GET", "/sillage/personnes", "Bearer jeton-sillage")]
    par_nom = {p["nom"]: p for p in r["personnes"]}
    assert set(par_nom) == {"Camille R.", "Tante Lise", "Hugo MARCHAND"}             # le nom de la fiche passe devant
    assert par_nom["Camille R."]["carnet"] and par_nom["Camille R."]["proche"] and par_nom["Camille R."]["naissance"] == "1987-03-14"
    assert par_nom["Tante Lise"]["carnet"] and par_nom["Tante Lise"]["decede"] and par_nom["Tante Lise"]["age"] is None
    assert par_nom["Hugo MARCHAND"]["carnet"] is False                                # hors carnet : par la recherche
    assert r["par_carnet"] is True and r["carnet"] == {"regle": True, "erreur": "", "fiches": 3}
    assert c.get(f"/api/chemin/{CAMILLE}").json()["personne"]["nom"] == "Camille R."
    assert c.get(f"/api/chemin/{CACHEE}").status_code == 200                          # masquée dans Immich, mais liée par carnet
    assert c.get("/api/services").json()["carnet"]["fiches"] == 3


def test_carnet_muet_ou_ferme_immich_en_secours(c):
    avec_carnet((500, {}))
    r = c.get("/api/personnes").json()
    assert [p["nom"] for p in r["personnes"]] == ["Camille ROUSSEL", "Hugo MARCHAND"]
    assert r["par_carnet"] is False and r["carnet"]["erreur"] == "carnet ne répond pas."
    avec_carnet((401, {"detail": "non"}))
    assert c.get("/api/personnes").json()["carnet"]["erreur"] == "carnet refuse le jeton de Sillage."
    avec_carnet((200, {"autre": "chose"}))
    assert c.get("/api/personnes").json()["carnet"]["erreur"] == "carnet ne répond pas."


# ------------------------------------------------------------ 0.5 : invités des chambres

def avec_jeton_ha():
    import dataclasses
    main.ETAT["cfg"] = dataclasses.replace(main.ETAT["cfg"], jeton_ha="jeton-ha")
    return {"Authorization": "Bearer jeton-ha"}


def sejour(c, h, **corps):
    from datetime import date, timedelta
    corps.setdefault("chambre", "ami")
    corps.setdefault("jusqu_au", (date.today() + timedelta(days=2)).isoformat())
    r = c.post("/ha/sejour", json=corps, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_ha_prepare_l_invitation(monde):
    client, faux = monde
    assert client.post("/ha/sejour", json={"chambre": "ami", "noms": ["Camille ROUSSEL"]}).status_code == 401   # fermé sans jeton
    h = avec_jeton_ha()
    assert client.post("/ha/sejour", json={"chambre": "ami", "noms": ["x"]}, headers={"Authorization": "Bearer faux"}).status_code == 401
    r = sejour(client, h, noms=["camille roussel", "Inconnu TOTAL"])                     # sans majuscules : trouvée
    assert r["chemin"].startswith("/invite/") and r["trouves"] == ["camille roussel"] and r["manquants"] == ["Inconnu TOTAL"]
    assert sejour(client, h, noms=["camille roussel", "Inconnu TOTAL"])["chemin"] == r["chemin"]   # rien n'a changé : même jeton
    autre = sejour(client, h, noms=["Camille ROUSSEL"])
    assert autre["chemin"] != r["chemin"]
    assert client.get("/api" + r["chemin"]).status_code == 404                           # l'ancienne invitation ne marche plus
    assert client.get("/api" + autre["chemin"]).status_code == 200                       # sans mot de passe : c'est le jeton qui ouvre
    for faux_corps in ({"noms": ["A"]}, {"chambre": "ami", "noms": ["A"], "jusqu_au": "demain"},
                       {"chambre": "ami", "noms": ["A"], "jusqu_au": "2001-01-01"}):
        assert client.post("/ha/sejour", json=faux_corps, headers=h).status_code == 422
    assert sejour(client, h, noms=[])["chemin"] == ""                                    # séjour fini : l'invitation est retirée
    assert client.get("/api" + autre["chemin"]).status_code == 404
    assert {(m, ch) for m, ch in faux.demandes if m != "GET"} <= {("POST", "/search/metadata")}


def test_l_invite_seul_voit_son_chemin(monde):
    client, _ = monde
    h = avec_jeton_ha()
    jeton = sejour(client, h, noms=["Camille ROUSSEL"])["chemin"].split("/")[-1]
    r = client.get(f"/api/invite/{jeton}").json()
    assert r["commun"] is None and r["accueil"] is False and r["invites"] == ["Camille ROUSSEL"]
    (c,) = r["chacun"]
    assert [ch["titre"] for ch in c["chapitres"]] == ["0 à 9 ans", "30 à 39 ans"]       # seul : par âge
    e = c["chapitres"][0]["etapes"][0]
    assert set(e) == {"cle", "nom", "debut", "fin", "quand", "fois", "age", "nombre", "phare", "temps_fort"}   # pas la liste des photos
    assert "immich" not in r and "de_cote" not in c
    assert client.get(f"/api/invite/{jeton}/vignette/{e['phare']}").status_code == 200
    assert client.get(f"/api/invite/{jeton}/vignette/{ident('bapteme1')}").status_code == 404   # pas une photo phare
    assert client.get(f"/api/invite/autre-jeton/vignette/{e['phare']}").status_code == 404


def test_deux_invites_une_frise_en_couleurs(monde, c):
    """0.7 : moments communs, et chacun seul ou avec les hôtes ; jamais une photo où il y a quelqu'un d'autre."""
    client, faux = monde
    faux.personnes.append({"id": HOTE, "name": "Alex DUPRÉ", "birthDate": None, "isHidden": False})
    faux.photos[CAMILLE] += [photo("cafe", "2015-04-01T10:00:00", "2015/2015-04-01 Café du port", aussi=[HOTE]),
                             photo("foule", "2016-05-01T10:00:00", "2016/2016-05-01 Fête du village", aussi=[ANONYME])]
    h = avec_jeton_ha()
    jeton = sejour(client, h, chambre="ado", noms=["Camille ROUSSEL", "Hugo MARCHAND"])["chemin"].split("/")[-1]
    r = client.get(f"/api/invite/{jeton}").json()
    f = r["commun"]
    assert f["ensemble"] and f["invites"] == ["Camille ROUSSEL", "Hugo MARCHAND"] and r["chacun"] == []
    assert [ch["titre"] for ch in f["chapitres"]] == ["Années 1980", "Années 1990", "Années 2000", "Années 2010"]
    vus = {(e["nom"] or e["debut"], e["qui"]) for ch in f["chapitres"] for e in ch["etapes"]}
    assert ("Mariage de Camille et Hugo", "ensemble") in vus
    assert ("Baptême de Camille", 0) in vus and ("2001-02-03", 1) in vus
    assert not any(n == "Café du port" for n, _ in vus)                                # sans hôte réglé : seul seulement
    assert not any(n == "Fête du village" for n, _ in vus)                             # quelqu'un d'autre : jamais
    assert len({e["cle"] for ch in f["chapitres"] for e in ch["etapes"]}) == f["etapes"]
    # Les hôtes se règlent dans Sillage ; la photo avec l'hôte entre dans la frise de Camille
    assert c.put("/api/reglages", json={"hotes": ["pas-une-personne"]}).status_code == 422
    assert c.put("/api/reglages", json={"hotes": [HOTE]}).json() == {"hotes": [{"id": HOTE, "nom": "Alex DUPRÉ"}]}
    r = client.get(f"/api/invite/{jeton}").json()
    vus = {(e["nom"], e["qui"]) for ch in r["commun"]["chapitres"] for e in ch["etapes"]}
    assert ("Café du port", 0) in vus and not any(n == "Fête du village" for n, _ in vus)
    # Une étape masquée par l'hôte n'est pas montrée
    c.get(f"/api/chemin/{CAMILLE}")
    marque(c, sorte="masquee", poser=ident("mariage1"))
    main.ETAT["invites"].clear()
    r = client.get(f"/api/invite/{jeton}").json()
    assert all(e["nom"] != "Mariage de Camille et Hugo" for ch in r["commun"]["chapitres"] for e in ch["etapes"])


def test_personne_trouvee_le_mot_d_accueil(monde):
    client, _ = monde
    h = avec_jeton_ha()
    r = sejour(client, h, noms=["Personne INCONNUE"])
    assert r["trouves"] == [] and r["chemin"]
    inv = client.get("/api" + r["chemin"]).json()
    assert inv == {"invites": ["Personne INCONNUE"], "commun": None, "chacun": [], "accueil": True}


def test_invitation_expiree(monde):
    client, _ = monde
    h = avec_jeton_ha()
    chemin = sejour(client, h, noms=["Camille ROUSSEL"])["chemin"]
    main.ETAT["base"]._c.execute("UPDATE invites SET expire = '2000-01-01T00:00:00'")
    main.ETAT["base"]._c.commit()
    main.ETAT["invites"].clear()
    assert client.get("/api" + chemin).status_code == 404


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


def test_onglet_chambres_montre_les_pages_preparees(monde):
    """0.6 : le propriétaire voit les pages préparées par HA, par date d'arrivée ; la date d'arrivée garde le lien."""
    from datetime import date, timedelta
    client, _ = monde
    h = avec_jeton_ha()
    assert client.get("/api/chambres").status_code == 401                                # réservé au propriétaire
    d1, d5 = (date.today() + timedelta(days=1)).isoformat(), (date.today() + timedelta(days=5)).isoformat()
    a = sejour(client, h, chambre="stitch", noms=["Camille ROUSSEL"], du=d5,
               jusqu_au=(date.today() + timedelta(days=7)).isoformat())
    sejour(client, h, chambre="ami", noms=["Camille ROUSSEL", "Inconnu TOTAL"], du=d1)
    assert sejour(client, h, chambre="stitch", noms=["Camille ROUSSEL"], du=d1,
                  jusqu_au=(date.today() + timedelta(days=7)).isoformat())["chemin"] == a["chemin"]
    assert client.post("/api/connexion", json={"mot_de_passe": MDP}).status_code == 200
    ch = client.get("/api/chambres").json()["chambres"]
    assert [c["chambre"] for c in ch] == ["ami", "stitch"]                               # même arrivée : par chambre
    ami = ch[0]
    assert ami["noms"] == ["Camille ROUSSEL"] and ami["introuvables"] == [] and ami["du"] == d1
    assert ami["au"] == (date.today() + timedelta(days=2)).isoformat()
    assert ch[1]["jeton"] == a["chemin"].split("/")[-1]
    sejour(client, h, chambre="ami", noms=["Inconnu TOTAL"], du="pas une date")         # personne de trouvé, date illisible
    ami = next(c for c in client.get("/api/chambres").json()["chambres"] if c["chambre"] == "ami")
    assert ami["introuvables"] == ["Inconnu TOTAL"] and ami["du"] == ""


def test_regroupements_meme_nom_et_scans_par_annee(monde, c):
    """0.9 : « Apéro » chaque semaine devient une étape ; les scans au 1er du mois se réunissent par année."""
    client, faux = monde
    faux.photos[CAMILLE] += [
        photo("apero1", "2021-01-08T19:00:00", "2021/Apéro"), photo("apero2", "2021-01-22T19:00:00", "2021/Apéro"),
        photo("noel21", "2021-02-01T12:00:00", "2021/2021-02-01 Fête des voisins"),
        photo("apero3", "2021-03-05T19:00:00", "2021/Apéro"),
        photo("apero4", "2021-08-20T19:00:00", "2021/Apéro"),                              # plus de deux mois après : à part
        photo("scan1", "1992-03-01T00:00:00", "1992/1992-03-01"), photo("scan2", "1992-09-01T00:00:00", "1992/1992-09"),
        photo("scan3", "1993-01-01T00:00:00", "1993"),
    ]
    main.ETAT["personnes"] = None
    r = c.get(f"/api/chemin/{CAMILLE}?frais=true").json()
    tout = etapes(r)
    aperos = [e for e in tout if e["nom"] == "Apéro"]
    assert [(e["debut"], e["fin"], e["fois"], e["nombre"]) for e in aperos] == [
        ("2021-01-08", "2021-03-05", 3, 3), ("2021-08-20", "2021-08-20", 1, 1)]
    assert any(e["nom"] == "Fête des voisins" for e in tout)                             # l'étape entre les deux reste
    scans = [e for e in tout if e["quand"] in ("1992", "1993")]
    assert [(e["quand"], e["nombre"], e["nom"]) for e in scans] == [("1992", 2, ""), ("1993", 1, "")]
    # Nommer ou masquer l'étape réunie la touche toute entière (la marque n'est posée que sur la photo phare)
    reunie = aperos[0]
    r = marque(c, sorte="titre", effacer=[p["id"] for p in reunie["photos"]], poser=reunie["phare"], valeur="Apéros du vendredi")
    assert [(e["nom"], e["fois"]) for e in etapes(r) if e["debut"] == "2021-01-08"] == [("Apéros du vendredi", 3)]
    r = marque(c, sorte="masquee", poser=reunie["phare"])
    assert [e["masquee"] for e in etapes(r) if e["debut"] == "2021-01-08"] == [True]


def test_vignettes_gardees_sur_disque(monde, c, tmp_path):
    """0.10 : une vignette lue une fois dans Immich est servie du disque ensuite."""
    _, faux = monde
    c.get(f"/api/chemin/{CAMILLE}")
    p = ident("bapteme1")
    lectures = lambda: sum(1 for m, ch in faux.demandes if ch == f"/assets/{p}/thumbnail")
    assert c.get(f"/api/vignette/{p}").status_code == 200 and lectures() == 1
    assert c.get(f"/api/vignette/{p}").content == c.get(f"/api/vignette/{p}").content and lectures() == 1
    assert c.get(f"/api/vignette/{p}?grande=true").status_code == 200 and lectures() == 2     # autre taille, autre fichier
    assert len(list((tmp_path / "vignettes").iterdir())) == 2
    assert c.get("/api/services").json()["cache"]["fichiers"] == 2
    # La limite est tenue : au-delà, les moins récemment servies partent
    from app.cache import Cache
    petit = Cache(tmp_path / "petit", 1)
    for i in range(30):
        petit.garder(f"{ident(str(i))}-preview", b"x" * 60_000, "image/jpeg")
    petit.elaguer()
    assert petit.place()["mo"] <= 1


def test_video_lue_par_morceaux(monde, c):
    """0.10 : les vidéos du chemin se lisent, l'en-tête Range est transmis à Immich ; jamais une vidéo inconnue."""
    c.get(f"/api/chemin/{CAMILLE}")
    v = ident("bapteme3")
    r = c.get(f"/api/video/{v}")
    assert r.status_code == 200 and r.headers["content-type"] == "video/mp4" and len(r.content) == 1000
    r = c.get(f"/api/video/{v}", headers={"Range": "bytes=10-19"})
    assert r.status_code == 206 and r.content == bytes(range(10, 20)) and r.headers["content-range"] == "bytes 10-19/1000"
    assert c.get(f"/api/video/{ident('inconnue')}").status_code == 404


def test_noms_d_albums_nettoyes():
    """0.10 : l'année en tête d'un album part ; un lot de numérisation n'est pas un nom d'étape."""
    from app.chemin import nom_d_album
    assert nom_d_album("2007 - Soirée d'été") == "Soirée d'été"
    assert nom_d_album("1998 Numérisation de la famille") == "" and nom_d_album("Scans de grand-mère") == ""
    assert nom_d_album("50 ans de mariage") == "50 ans de mariage" and nom_d_album("Apéro 2021") == "Apéro 2021"


def test_0_12_l_album_d_une_photo(monde, c):
    """Le propriétaire voit tout l'album ; l'invité, seulement les photos de l'album où il est reconnu."""
    client, faux = monde
    nom = "Mariage de Camille et Hugo"
    faux.albums = {ident("mariage1"): nom, ident("mariage2"): nom, ident("tiers"): nom}
    faux.photos[ANONYME] = [photo("tiers", "2019-06-15T20:00:00")]                      # dans l'album, sans Camille
    assert c.get(f"/api/album/{ident('tiers')}").status_code == 404                       # pas encore une photo du chemin
    c.get(f"/api/chemin/{CAMILLE}")
    a = c.get(f"/api/album/{ident('mariage2')}").json()
    assert a["nom"] == nom and [p["id"] for p in a["photos"]] == [ident("mariage1"), ident("tiers"), ident("mariage2")]  # par date
    assert c.get(f"/api/vignette/{ident('tiers')}").status_code == 200                    # ouverte par l'album
    assert c.get(f"/api/album/{ident('plage')}").json() == {"nom": "", "photos": [], "total": 0}
    assert {(m, ch) for m, ch in faux.demandes if m != "GET"} <= {("POST", "/search/metadata")}   # rien d'écrit dans Immich
    # L'invité
    jeton = sejour(client, avec_jeton_ha(), noms=["Camille ROUSSEL"])["chemin"].split("/")[-1]
    r = client.get(f"/api/invite/{jeton}").json()
    phares = {e["phare"] for ch in r["chacun"][0]["chapitres"] for e in ch["etapes"]}
    phare = next(p for p in phares if p in faux.albums)
    a = client.get(f"/api/invite/{jeton}/album/{phare}").json()
    assert a["nom"] == nom and ident("tiers") not in [p["id"] for p in a["photos"]] and ident("mariage1") in [p["id"] for p in a["photos"]]
    assert client.get(f"/api/invite/{jeton}/vignette/{ident('mariage1')}?petite=true").status_code == 200
    assert client.get(f"/api/invite/{jeton}/vignette/{ident('tiers')}").status_code == 404
    assert client.get(f"/api/invite/{jeton}/album/{ident('tiers')}").status_code == 404   # pas une photo phare
    # 0.12.1 : une étape hors de tout album (nom tiré du dossier) : « Voir l'album » montre ses propres photos
    faux.albums = {}
    main.ETAT["invites"].clear()
    r = client.get(f"/api/invite/{jeton}").json()
    bapteme = next(e for ch in r["chacun"][0]["chapitres"] for e in ch["etapes"] if e["nom"] == "Baptême de Camille")
    a = client.get(f"/api/invite/{jeton}/album/{bapteme['phare']}").json()
    assert a["nom"] == "" and set(p["id"] for p in a["photos"]) == {ident("bapteme1"), ident("bapteme2")}   # la vidéo n'est pas servie
    assert all(client.get(f"/api/invite/{jeton}/vignette/{p['id']}?petite=true").status_code == 200 for p in a["photos"])

