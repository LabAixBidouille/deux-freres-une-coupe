#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de « Deux frères, une coupe », et vérifie les renvois de texte.md.

Chaque chapitre est un maillot numéroté : gris pour le parcours d'Aylan (le gris de son sweat), bleu pour
celui d'Adam, or pour les quatre fins. Le prologue est le ballon. Les flèches sont tracées à angle droit,
pointe pleine.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"

ENCRE, BLEU, GRIS, OR = "#16181d", "#1747d6", "#6b6f78", "#e8b21a"

# Colonnes de gauche à droite ; chaque colonne est centrée verticalement
COLONNES = [["Prologue"], ["1"], ["2", "3", "4"], ["5"], ["6"], ["7", "8", "9"], ["10"], ["11", "12", "13", "14"]]
LARGEUR, HAUTEUR = 1120, 540
X0, PAS_X, MILIEU, PAS_Y = 70, 140, 300, 116
LIGNE = 8  # les flèches arrivent sous les manches


def lire_renvois():
    texte = TEXTE.read_text(encoding="utf-8")
    renvois = {}
    for bloc in re.split(r"^## ", texte, flags=re.M)[1:]:
        tete = bloc.split("\n", 1)[0]
        nom = "Prologue" if tete.startswith("Prologue") else re.match(r"Chapitre (\d+)", tete)[1]
        renvois[nom] = re.findall(r"chapitre (\d+)\.?$", bloc, flags=re.M)
    return renvois


def couleur(nom):
    if nom == "Prologue":
        return None
    n = int(nom)
    return GRIS if n <= 4 else OR if n >= 11 else BLEU


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
    return (f'<image x="{x - 32}" y="{y - 32 + LIGNE}" width="64" height="64" '
            f'href="data:image/png;base64,{code}"/>')


def construire():
    renvois = lire_renvois()
    pos = {}
    for i, col in enumerate(COLONNES):
        for j, nom in enumerate(col):
            pos[nom] = (X0 + i * PAS_X, MILIEU + (j - (len(col) - 1) / 2) * PAS_Y)
    assert set(pos) == set(renvois), f"Chapitres absents de l'arbre : {set(renvois) ^ set(pos)}"

    traits, pointes = [], set()
    for a, cibles in renvois.items():
        for b in cibles:
            assert b in pos, f"Renvoi vers un chapitre inconnu : {a} -> {b}"
            (x1, y1), (x2, y2) = pos[a], pos[b]
            assert x2 > x1, f"Renvoi en arrière non prévu : {a} -> {b}"
            x1 += 32 if a == "Prologue" else 24
            y1 += LIGNE
            y2 += LIGNE
            pointe = x2 - 25
            xm = x1 + (pointe - x1) / 2
            chemin = f"M{x1} {y1} H{xm} V{y2} H{pointe - 9}" if y1 != y2 else f"M{x1} {y1} H{pointe - 9}"
            traits.append(f'<path d="{chemin}"/>')
            pointes.add((pointe, y2))
    fleches = "".join(f'<path d="M{x} {y} l-11 -6.5 v13 z"/>' for x, y in sorted(pointes))

    def bandeau(debut, fin, texte, coul):
        xa, xb = X0 + debut * PAS_X - 50, X0 + fin * PAS_X + 50
        return (f'<path d="M{xa + 8} 12 H{xb} l-8 26 H{xa} z" fill="{coul}"/>'
                f'<text x="{(xa + xb) / 2}" y="32" text-anchor="middle" font-family="Anton" font-size="19" '
                f'letter-spacing="1.5" fill="{"#fff" if coul != OR else ENCRE}">{texte}</text>')

    police = base64.b64encode((RACINE / "fonts" / "Anton-400.woff2").read_bytes()).decode()
    noeuds = "".join(ballon(*pos[n]) if n == "Prologue" else maillot(*pos[n], n) for n in pos)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}">'
        f'<style>@font-face {{ font-family: "Anton"; src: url(data:font/woff2;base64,{police}) format("woff2"); }}</style>'
        + bandeau(1, 2, "LE PARCOURS D’AYLAN", GRIS)
        + bandeau(3, 5, "LE PARCOURS D’ADAM", BLEU)
        + bandeau(7, 7, "LES FINS", OR)
        + f'<g fill="none" stroke="{BLEU}" stroke-width="3" stroke-linejoin="miter">{"".join(traits)}</g>'
        + f'<g fill="{BLEU}">{fleches}</g>'
        + noeuds
        + "</svg>"
    )
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {sum(len(c) for c in renvois.values())} renvois")


if __name__ == "__main__":
    construire()
