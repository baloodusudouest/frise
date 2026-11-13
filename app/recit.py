"""« Raconter » : le récit d'un chemin, écrit par gabarit. Rien n'est inventé : chaque phrase reprend une étape
visible (sa date, l'âge, son nom). Le texte proposé se relit et se corrige avant d'être gardé."""
from __future__ import annotations

from datetime import date

MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre")


def _jour(d: date) -> str:
    return "1er" if d.day == 1 else str(d.day)


def date_longue(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{_jour(d)} {MOIS[d.month - 1]} {d.year}"


def periode(debut: str, fin: str) -> str:
    a, b = date.fromisoformat(debut), date.fromisoformat(fin)
    if a == b:
        return "Le " + date_longue(debut)
    if a.year != b.year:
        return f"Du {date_longue(debut)} au {date_longue(fin)}"
    if a.month != b.month:
        return f"Du {_jour(a)} {MOIS[a.month - 1]} au {date_longue(fin)}"
    return f"Du {_jour(a)} au {date_longue(fin)}"


def age_dit(age: int | None) -> str:
    return "" if age is None else ", avant un an" if age == 0 else ", à un an" if age == 1 else f", à {age} ans"


def proposer(chemin: dict) -> str:
    """Un paragraphe par chapitre. Les étapes nommées ont leur phrase ; les autres sont comptées."""
    p = chemin["personne"]
    lignes = [p["nom"], ""]
    if p.get("naissance"):
        lignes += [f"Naissance le {date_longue(p['naissance'])}.", ""]
    for c in chemin["chapitres"]:
        visibles = [e for e in c["etapes"] if not e["masquee"]]
        nommees = [e for e in visibles if e["nom"]]
        if not visibles:
            continue
        lignes.append(c["titre"])
        for e in nommees:
            lignes.append(f"{periode(e['debut'], e['fin'])}{age_dit(e['age'])} : {e['nom']}.")
        autres = len(visibles) - len(nommees)
        if autres:
            debut = "Et " if nommees else ""
            lignes.append(f"{debut}{autres} autre{'s' if autres > 1 else ''} moment{'s' if autres > 1 else ''} en photos."
                          if nommees else f"{autres} moment{'s' if autres > 1 else ''} en photos, sans nom.")
        lignes.append("")
    return "\n".join(lignes).rstrip() + "\n"
