#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de « Deux frères, une coupe », et vérifie les renvois de texte.md.

L'arbre se lit de haut en bas. Chaque chapitre est un maillot numéroté, avec son titre dessous : gris pour le
parcours d'Aylan (le gris de son sweat), bleu pour celui d'Adam, or pour les quatre fins. Le prologue est le
ballon. Sur chaque branche, les faces du dé qui y mènent ; avant chaque fin, la condition qui l'ouvre. Les
parcours sont nommés dans la marge de gauche. Flèches à angle droit, pointe pleine.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"

ENCRE, BLEU, BLEU_FONCE, BLEU_PALE, GRIS, OR, OR_PALE = (
    "#16181d", "#1747d6", "#0f2f9a", "#e3eafc", "#6b6f78", "#e8b21a", "#fbf0cc")

LARGEUR, HAUTEUR = 1180, 1880
CENTRE = 640
# Rangées de haut en bas : (ordonnée du maillot, chapitres, écart entre maillots)
RANGEES = [(50, ["Prologue"], 0), (265, ["1"], 0), (520, ["2", "3", "4"], 300), (770, ["5"], 0),
           (965, ["6"], 0), (1220, ["7", "8", "9"], 300), (1470, ["10"], 0), (1725, ["11", "12", "13", "14"], 270)]
# Ce qui ouvre chaque fin, en quelques mots (les conditions du chapitre 10)
FINS = {"11": "Les deux sont pros", "12": "Seul Aylan est pro", "13": "Seul Adam est pro", "14": "Aucun n’est pro"}
# Les parcours, nommés dans la marge : (premier chapitre, dernier chapitre, texte, couleur)
PARCOURS = [("1", "4", "LE PARCOURS D’AYLAN", GRIS), ("5", "9", "LE PARCOURS D’ADAM", BLEU),
            ("10", "14", "LES FINS", OR)]
SOUS_TITRE = 78   # le titre du chapitre occupe jusqu'à cette distance sous le centre du maillot
HAUT = 36         # haut du col du maillot


def lire_texte():
    texte = TEXTE.read_text(encoding="utf-8")
    titres, renvois, des = {}, {}, {}
    for bloc in re.split(r"^## ", texte, flags=re.M)[1:]:
        tete = bloc.split("\n", 1)[0]
        nom = "Prologue" if tete.startswith("Prologue") else re.match(r"Chapitre (\d+)", tete)[1]
        titres[nom] = tete.split(". ", 1)[1].strip()
        renvois[nom] = re.findall(r"chapitre (\d+)\.?$", bloc, flags=re.M)
        for faces, cible in re.findall(r"^- (\d(?:, \d)*(?: ou \d)?) : .*?chapitre (\d+)", bloc, flags=re.M):
            des[(nom, cible)] = faces
    return titres, renvois, des


def couleur(nom):
    n = int(nom)
    return GRIS if n <= 4 else OR if n >= 11 else BLEU


def lignes(titre, largeur=27):
    sortie, ligne = [], ""
    for mot in titre.replace("'", "’").split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            sortie.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return sortie + [ligne]


def titre_svg(x, y, titre):
    tspans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 19}">{l}</tspan>' for i, l in enumerate(lignes(titre)))
    return (f'<text x="{x}" y="{y + 54}" text-anchor="middle" font-family="Barlow" font-weight="600" '
            f'font-size="16" fill="{ENCRE}">{tspans}</text>')


def maillot(x, y, nom):
    c = couleur(nom)
    forme = ("M-13 -30 L-31 -23 L-41 -5 L-29 1 L-24 -6 L-24 30 L24 30 L24 -6 L29 1 L41 -5 L31 -23 "
             "L13 -30 Q0 -19 -13 -30 Z")
    chiffre = "#fff" if c != OR else ENCRE
    return (f'<g transform="translate({x},{y})"><path d="{forme}" fill="{c}" stroke="{ENCRE}" stroke-width="2.6" '
            f'stroke-linejoin="round"/>'
            f'<text x="0" y="22" text-anchor="middle" font-family="Anton" font-size="{30 if len(nom) == 1 else 27}" '
            f'fill="{chiffre}">{nom}</text></g>')


def ballon(x, y):
    from io import BytesIO
    try:
        from PIL import Image
        image = Image.open(RACINE / "images" / "ballon.png")
        image.thumbnail((120, 120))
        tampon = BytesIO()
        image.save(tampon, "PNG", optimize=True)
        donnees = tampon.getvalue()
    except ImportError:
        donnees = (RACINE / "images" / "ballon.png").read_bytes()
    code = base64.b64encode(donnees).decode()
    return f'<image x="{x - 32}" y="{y - 32}" width="64" height="64" href="data:image/png;base64,{code}"/>'


def pastille(x, y, texte, fond, encre):
    largeur = 18 + len(texte) * 8.4
    return (f'<g transform="translate({x},{y}) skewX(-12)"><rect x="{-largeur / 2}" y="-13" width="{largeur}" '
            f'height="26" fill="{fond}"/></g>'
            f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-family="Barlow Condensed" font-weight="700" '
            f'font-size="17" letter-spacing="0.5" fill="{encre}">{texte}</text>')


def police(fichier, nom, graisse=400):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{nom}"; font-weight: {graisse}; '
            f'src: url(data:font/woff2;base64,{code}) format("woff2"); }}')


def construire():
    titres, renvois, des = lire_texte()
    pos = {}
    for y, noms, ecart in RANGEES:
        for j, nom in enumerate(noms):
            pos[nom] = (CENTRE + (j - (len(noms) - 1) / 2) * ecart, y)
    assert set(pos) == set(renvois), f"Chapitres absents de l'arbre : {set(renvois) ^ set(pos)}"

    traits, pointes, etiquettes = [], set(), []
    for a, cibles in renvois.items():
        for b in cibles:
            assert b in pos, f"Renvoi vers un chapitre inconnu : {a} -> {b}"
            (x1, y1), (x2, y2) = pos[a], pos[b]
            assert y2 > y1, f"Renvoi en arrière non prévu : {a} -> {b}"
            depart = y1 + SOUS_TITRE + 10
            arrivee = y2 - HAUT - 4
            if x1 == x2:
                traits.append(f'<path d="M{x1} {depart} V{arrivee - 9}"/>')
            else:
                # Plusieurs enfants : le palier est juste sous le parent ; plusieurs parents : juste au-dessus
                palier = depart + 30 if len(cibles) > 1 else arrivee - 40
                traits.append(f'<path d="M{x1} {depart} V{palier} H{x2} V{arrivee - 9}"/>')
            pointes.add((x2, arrivee))
            if (a, b) in des:
                etiquettes.append(pastille(x2, arrivee - 42, des[(a, b)], BLEU_PALE, BLEU_FONCE))
            elif b in FINS:
                etiquettes.append(pastille(x2, arrivee - 42, FINS[b], OR_PALE, ENCRE))
    fleches = "".join(f'<path d="M{x} {y} l-6.5 -11 h13 z"/>' for x, y in sorted(pointes))

    # Les bandes de la marge se suivent : chacune couvre son bloc entier, de l'entrée de son premier chapitre
    # jusqu'au début du bloc suivant (la dernière jusqu'au bas des titres des fins), avec son texte au milieu
    marge = []
    debuts = [pos[premier][1] - 60 for premier, _, _, _ in PARCOURS]
    for i, (premier, dernier, texte, coul) in enumerate(PARCOURS):
        haut = debuts[i]
        bas = debuts[i + 1] - 16 if i + 1 < len(PARCOURS) else pos[dernier][1] + 92
        milieu = (haut + bas) / 2
        marge.append(f'<rect x="34" y="{haut}" width="32" height="{bas - haut}" fill="{coul}"/>'
                     f'<text transform="translate(57,{milieu}) rotate(-90)" text-anchor="middle" font-family="Anton" '
                     f'font-size="19" letter-spacing="2" fill="{"#fff" if coul != OR else ENCRE}">{texte}</text>')

    noeuds = "".join((ballon(*pos[n]) if n == "Prologue" else maillot(*pos[n], n)) + titre_svg(*pos[n], titres[n])
                     for n in pos)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}">'
        "<style>" + police("Anton-400.woff2", "Anton") + police("Barlow-600.woff2", "Barlow", 600)
        + police("BarlowCondensed-700.woff2", "Barlow Condensed", 700) + "</style>"
        + "".join(marge)
        + f'<g fill="none" stroke="{BLEU}" stroke-width="3" stroke-linejoin="miter">{"".join(traits)}</g>'
        + f'<g fill="{BLEU}">{fleches}</g>'
        + "".join(etiquettes)
        + noeuds
        + "</svg>"
    )
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {sum(len(c) for c in renvois.values())} renvois, "
          f"{len(des)} branches au dé")


if __name__ == "__main__":
    construire()
