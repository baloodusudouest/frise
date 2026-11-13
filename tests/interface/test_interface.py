"""Tests d'écran de Sillage, sur PC et sur iPhone, contre un faux Immich."""
from __future__ import annotations

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


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "tests.interface.serveur", str(tmp_path_factory.mktemp("ui")), str(port)], cwd=RACINE)
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
        pg.base = base
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
    sans_debordement(page)
    page.keyboard.press("Escape")
    assert page.locator(".plein").count() == 0 and page.locator(".galerie").is_visible()
    page.keyboard.press("Escape")
    assert page.locator(".galerie").count() == 0


def test_connexion_et_reglages(page):
    page.goto(page.base + "/#/connexion")
    page.get_by_text("Répond, version 3.4.1. 2 personnes nommées.").wait_for()
    page.goto(page.base + "/#/reglages")
    page.get_by_text("Sillage 0.2.0").wait_for()
    sans_debordement(page)
