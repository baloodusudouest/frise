"""Tests d'écran de Sillage, sur PC et sur iPhone, contre un faux Immich."""
from __future__ import annotations

import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from tests.faux_immich import CAMILLE

playwright = pytest.importorskip("playwright.sync_api")
RACINE = Path(__file__).resolve().parents[2]
MDP = "essai-essai-essai"
ECRANS = {"pc": {"width": 1280, "height": 860}, "iphone": {"width": 390, "height": 760}}


DOSSIER = {}


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    DOSSIER["ui"] = tmp_path_factory.mktemp("ui")
    proc = subprocess.Popen([sys.executable, "-m", "tests.interface.serveur", str(DOSSIER["ui"]), str(port)], cwd=RACINE)
    adresse = f"http://127.0.0.1:{port}"
    for _ in range(200):
        try:
            if urllib.request.urlopen(adresse + "/health", timeout=1).status == 200:
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.fail("Le Sillage de démonstration n'a pas démarré.")
    yield adresse
    proc.terminate()


@pytest.fixture(scope="module", params=list(ECRANS))
def page(base, request):
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport=ECRANS[request.param])
        pg.set_default_timeout(10000)
        erreurs = []
        pg.on("pageerror", lambda e: erreurs.append(str(e)))
        pg.goto(base + "/")
        pg.fill("#mot-de-passe", MDP)
        pg.click("button[type=submit]")
        pg.wait_for_selector("ul[aria-label=Personnes]")
        pg.base, pg.ecran = base, request.param
        yield pg
        assert erreurs == []
        b.close()


def sans_debordement(pg):
    assert pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0


def test_la_liste_et_la_recherche(page):
    page.goto(page.base + "/#/sillages")
    assert page.locator("ul[aria-label=Personnes] li").count() == 2
    page.fill("input[type=search]", "camil")
    assert page.locator("ul[aria-label=Personnes] li").count() == 1
    page.fill("input[type=search]", "zzz")
    assert page.get_by_text("Personne ne porte ce nom.").is_visible()
    sans_debordement(page)


def test_010_tuile_a_verifier(page):
    """0.10 : les personnes sans date de naissance dans Immich, d'un toucher."""
    page.goto(page.base + "/#/sillages")
    page.fill("input[type=search]", "")
    tuile = page.locator(".averifier")
    assert "1 personne sans date de naissance" in tuile.inner_text()
    tuile.click()
    assert page.locator("ul[aria-label=Personnes] li").all_inner_texts()[0].startswith("Hugo")
    assert page.locator("ul[aria-label=Personnes] li").count() == 1
    tuile.click()
    assert page.locator("ul[aria-label=Personnes] li").count() == 2


def test_010_une_video_se_lit(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.get_by_role("button", name="Noël chez les grands-parents, 6 photos").click()
    page.get_by_role("button", name="Photo 1 (vidéo)").click()
    v = page.locator(".plein video")
    v.wait_for()
    assert v.get_attribute("src").startswith("/api/video/") and v.get_attribute("controls") is not None
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")


def test_le_chemin_temps_forts_puis_tout(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.wait_for_selector(".etape")
    assert page.locator("h1").inner_text() == "Camille ROUSSEL"
    assert [t.strip() for t in page.locator(".chapitre").all_inner_texts()] == ["0 à 9 ans", "10 à 19 ans", "20 à 29 ans", "30 à 39 ans"]
    assert page.locator(".etape").count() == 8                     # les temps forts seulement
    page.get_by_role("button", name="Tout", exact=True).click()
    assert page.locator(".etape").count() == 11
    assert page.locator(".etape.petite").count() == 2
    assert page.get_by_text("d'avant sa naissance").is_visible()
    sans_debordement(page)


def test_une_etape_et_ses_photos(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.get_by_role("button", name="Mariage de Camille et Hugo, 40 photos").click()
    assert page.locator(".galerie li").count() == 40
    page.get_by_role("button", name="Photo 1", exact=True).click()
    assert page.get_by_role("group", name="Photo 1 sur 40").is_visible()
    page.keyboard.press("ArrowLeft")
    assert page.get_by_role("group", name="Photo 40 sur 40").is_visible()
    page.get_by_role("button", name="Photo suivante").click()
    assert page.get_by_role("group", name="Photo 1 sur 40").is_visible()
    assert page.get_by_role("link", name="Ouvrir dans Immich").get_attribute("href").startswith("http://photos.exemple/photos/")
    # La croix se ferme en cliquant en son centre : rien ne la recouvre (le compteur passait dessus)
    croix = page.get_by_role("button", name="Fermer la photo").bounding_box()
    assert page.evaluate("([x, y]) => document.elementFromPoint(x, y).closest('button')?.getAttribute('aria-label')",
                         [croix["x"] + croix["width"] / 2, croix["y"] + croix["height"] / 2]) == "Fermer la photo"
    for dy in (0.15, 0.5, 0.85):
        assert page.evaluate("([x, y]) => document.elementFromPoint(x, y).closest('button')?.getAttribute('aria-label')",
                             [croix["x"] + croix["width"] / 2, croix["y"] + croix["height"] * dy]) == "Fermer la photo"
    sans_debordement(page)
    page.keyboard.press("Escape")
    assert page.locator(".plein").count() == 0 and page.locator(".galerie").is_visible()


def test_012_voir_tout_l_album(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.reload()                                               # repart d'une page sans étape ouverte
    page.get_by_role("button", name="Mariage de Camille et Hugo, 40 photos").click()
    page.get_by_role("button", name="Photo 1", exact=True).click()
    page.get_by_role("button", name="Voir tout l'album").click()
    album = page.get_by_role("dialog", name="Album Mariage de Camille et Hugo")
    album.wait_for()
    album.locator(".grille li").first.wait_for()
    assert album.locator(".grille li").count() == 40
    album.get_by_role("button", name="Photo 3", exact=True).click()
    assert album.get_by_role("group", name="Photo 3 sur 40").is_visible()
    page.keyboard.press("ArrowRight")
    assert album.get_by_role("group", name="Photo 4 sur 40").is_visible()
    page.keyboard.press("Escape")                               # revient à la grille de l'album
    assert album.locator(".grille").is_visible()
    sans_debordement(page)
    page.keyboard.press("Escape")                               # ferme l'album, la photo de l'étape reste ouverte
    assert album.count() == 0 and page.locator(".plein").is_visible()
    page.keyboard.press("Escape")                               # la photo : l'étape reste ouverte, comme le test précédent la laisse
    assert page.locator(".galerie").is_visible()

    page.keyboard.press("Escape")
    assert page.locator(".galerie").count() == 0


def test_corriger_une_etape_et_une_photo(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.get_by_role("button", name=re.compile("^Communion")).click()
    page.get_by_role("button", name="Corriger l'étape").click()
    page.get_by_label("Nom de l'étape").fill("Communion de Camille")
    page.get_by_role("button", name="Nommer", exact=True).click()
    page.get_by_role("heading", name="Communion de Camille").wait_for()
    page.get_by_role("button", name="Rendre le nom d'origine").click()
    page.get_by_role("heading", name="Communion", exact=True).wait_for()
    # Une photo : la choisir comme phare, puis en retirer une autre
    # (les deux écrans partagent le même serveur : chacun choisit sa photo)
    page.get_by_role("button", name="Photo 3" if page.ecran == "pc" else "Photo 2", exact=True).click()
    page.get_by_role("button", name="En faire la photo phare").click()
    page.get_by_role("button", name="Photo phare", exact=True).wait_for()
    page.get_by_role("button", name="Photo suivante").click()
    page.get_by_role("button", name="Ce n'est pas cette personne").click()
    page.get_by_role("group", name=re.compile("Photo [34] sur 6")).wait_for()
    sans_debordement(page)
    page.keyboard.press("Escape")
    # Masquer l'étape : elle quitte le chemin, on la retrouve par « Tes corrections »
    page.get_by_role("button", name="Masquer cette étape").click()
    page.get_by_role("button", name="Remettre l'étape dans le chemin").wait_for()
    page.keyboard.press("Escape")
    page.get_by_role("button", name=re.compile("^Communion")).wait_for(state="detached")
    page.get_by_role("button", name="Afficher 1 étape masquée").click()
    page.get_by_role("button", name=re.compile("^Communion")).wait_for()
    page.get_by_role("button", name="Afficher 1 photo mise de côté").click()
    page.get_by_text("Pas cette personne").wait_for()
    page.get_by_role("button", name="Remettre").click()
    page.get_by_role("button", name=re.compile("mise de côté")).wait_for(state="detached")
    sans_debordement(page)
    # On remet tout pour l'écran suivant
    page.get_by_role("button", name=re.compile("^Communion")).click()
    page.get_by_role("button", name="Corriger l'étape").click()
    page.get_by_role("button", name="Remettre l'étape dans le chemin").click()
    page.get_by_role("button", name="Masquer cette étape").wait_for()
    page.keyboard.press("Escape")


def test_raconter(page):
    page.goto(page.base + "/#/chemin/" + CAMILLE)
    page.get_by_role("link", name="Raconter").click()
    zone = page.get_by_label("Le récit")
    zone.wait_for()
    assert "Baptême de Camille." in zone.input_value() and zone.input_value().startswith("Camille ROUSSEL")
    assert page.get_by_role("button", name="Garder ce texte").is_disabled()
    zone.fill("Un texte relu et corrigé.")
    page.get_by_role("button", name="Garder ce texte").click()
    page.get_by_text("Récit gardé.").wait_for()
    page.reload()
    page.get_by_label("Le récit").wait_for()
    assert page.get_by_label("Le récit").input_value() == "Un texte relu et corrigé."
    page.get_by_role("button", name="Repartir du chemin").click()
    page.get_by_text("Récit refait depuis le chemin.").wait_for()
    assert page.get_by_label("Le récit").input_value().startswith("Camille ROUSSEL")
    sans_debordement(page)


def test_connexion_et_reglages(page):
    page.goto(page.base + "/#/connexion")
    page.get_by_text("Répond, version 3.4.1. 2 personnes nommées.").wait_for()
    page.goto(page.base + "/#/reglages")
    from app import __version__
    page.get_by_text(f"Sillage {__version__}").wait_for()
    sans_debordement(page)


# ------------------------------------------------------------ 0.5 : la page d'un invité

def invitations():
    import json
    racine = Path(DOSSIER["ui"])
    for _ in range(100):
        if (racine / "invites.json").exists():
            return json.loads((racine / "invites.json").read_text())
        time.sleep(0.1)
    pytest.fail("Les invitations de démonstration n'ont pas été créées.")


def test_050_l_invite_voit_son_chemin_sans_mot_de_passe(page):
    jetons = invitations()
    page.context.clear_cookies()                                                        # pas de session : l'invité n'a pas le mot de passe
    page.goto(page.base + jetons["seule"])
    page.get_by_text("Votre chemin", exact=True).wait_for()
    assert page.locator("h1").inner_text().lower() == "votre chemin"                    # 0.7 : une ligne, plus de titre
    assert page.locator("nav[aria-label='Sections']").count() == 0                       # ni navigation, ni corrections, ni Immich
    assert page.get_by_role("button", name="Corriger l'étape").count() == 0 and page.get_by_text("Immich").count() == 0
    assert page.locator(".etape").count() == 8                                          # les temps forts d'abord
    page.get_by_role("button", name="Tout", exact=True).click()
    assert page.locator(".etape").count() == 11
    for src in page.locator(".etape img").evaluate_all("els => els.slice(0, 3).map(e => e.src)"):
        assert page.request.get(src).status == 200                                       # les photos phares passent par le jeton
    page.locator(".etape .ouvrir").first.click()                                        # 0.8 : la photo phare en grand
    page.get_by_role("dialog").wait_for()
    assert page.locator(".grand img").evaluate("i => i.getBoundingClientRect().width") > page.locator(".etape img").first.evaluate("i => i.getBoundingClientRect().width") * 0.9
    page.keyboard.press("Escape")
    assert page.get_by_role("dialog").count() == 0
    sans_debordement(page)


def test_050_deux_invites_le_chemin_commun(page):
    jetons = invitations()
    page.context.clear_cookies()
    page.goto(page.base + jetons["couple"])
    page.get_by_text("Votre chemin ensemble").wait_for()
    assert page.locator(".legende li").all_inner_texts() == ["Camille", "Hugo", "Ensemble"]   # 0.7 : une couleur chacun (0.11 : des boutons)
    if page.get_by_role("button", name="Tout", exact=True).count():
        page.get_by_role("button", name="Tout", exact=True).click()
    titres = [t.strip() for t in page.locator(".chapitre").all_inner_texts()]
    assert "Années 2000" in titres and "Années 2010" in titres
    mariage = page.locator(".etape", has_text="Mariage de Camille et Hugo")
    assert "Ensemble" in mariage.inner_text().title()
    couleurs = set(page.locator(".etape.colore").evaluate_all("els => els.map(e => getComputedStyle(e.querySelector('.carte')).borderLeftColor)"))
    assert len(couleurs) == 3                                                           # Camille, Hugo, ensemble
    # 0.11 : un clic sur un prénom ne garde que ses étapes ; plusieurs à la fois ; « Tout montrer » revient à tout
    toutes = page.locator(".etape").count()
    page.locator(".legende").get_by_role("button", name="Ensemble").click()
    qui = set(t.strip().title() for t in page.locator(".etape .qui").all_inner_texts())
    assert qui == {"Ensemble"} and 0 < page.locator(".etape").count() < toutes
    page.locator(".legende").get_by_role("button", name="Camille").click()
    assert set(t.strip().title() for t in page.locator(".etape .qui").all_inner_texts()) <= {"Ensemble", "Camille"}
    assert page.locator(".legende").get_by_role("button", name="Camille").get_attribute("aria-pressed") == "true"
    page.locator(".legende").get_by_role("button", name="Tout montrer").click()
    assert page.locator(".etape").count() == toutes
    page.goto(page.base + jetons["inconnu"])
    page.get_by_text("Pas encore de souvenirs ici").wait_for()
    page.goto(page.base + "/invite/jeton-inconnu")
    page.get_by_text("n'est plus valable").wait_for()
    sans_debordement(page)


def test_060_onglet_chambres_apercu_des_invites(page):
    invitations()
    page.goto(page.base + "/#/chambres")
    if page.locator("#mot-de-passe").count():                                        # les tests de l'invité ont vidé les cookies
        page.fill("#mot-de-passe", MDP)
        page.click("button[type=submit]")
    page.get_by_role("heading", name="Chambres", exact=True).wait_for()
    choix = page.locator("[aria-label=Chambre] button")
    assert sorted(choix.all_inner_texts()) == ["Chambre Couple", "Chambre Inconnu", "Chambre Seule"]
    page.get_by_role("button", name="Chambre Couple").click()
    page.get_by_text("Votre chemin ensemble").wait_for()
    assert "Camille ROUSSEL et Hugo MARCHAND" in page.locator(".fiche").inner_text()
    page.get_by_role("button", name="Chambre Inconnu").click()
    page.get_by_text("pas de personne de ce nom dans Immich").wait_for()
    page.get_by_text("Pas encore de souvenirs ici").wait_for()
    assert page.locator("main main").count() == 0                                    # l'aperçu n'ouvre pas une seconde page
    sans_debordement(page)
