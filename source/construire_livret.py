#!/usr/bin/env python3
"""Construit le livret imprimable de « Deux frères, une coupe » à partir de source/texte.md.

Même chaîne que les autres livres de l'atelier (pages de 124 × 186 mm, renvois avec le numéro de page,
imposition sur A4), avec la mise en forme du site d'Aylan et d'Adam : titres en Anton, texte en Barlow,
encre noire et bleu des Bleus, or de la couverture. Chaque chapitre s'ouvre sur son image entière, le
numéro sur une étiquette bleue en biais à cheval sur son bord bas ; les tirages sont dans une case au trait
noir, les faces du dé sur des hachures bleues ; les quatre fins du chapitre 10 forment un tableau à double
entrée.

Produit trois PDF dans le dossier Impression du livre :
- DeuxFreresUneCoupe_Livret_lecture.pdf : les pages dans l'ordre de lecture ;
- DeuxFreresUneCoupe_Livret_A4_bord_court.pdf et _bord_long.pdf : les pages imposées deux par deux sur
  A4 paysage, avec lignes de coupe et de pliure, pour une impression recto verso pliée en cahier.

Nécessite Google Chrome, pdftotext (poppler) et le module Python pypdf.
Usage, depuis la racine du dépôt : python3 source/construire_livret.py
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import (AUTEURS, AVERTISSEMENT, CITATION, CONTEXTE, SYNOPSIS, TITRE,  # noqa: E402
                             illustration, lire_chapitres, lire_choix)

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "DeuxFreresUneCoupe"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM                  # A4 paysage, en points
ENCRE, DOUCE, GRIS, BLEU, BLEU_FONCE, BLEU_PALE, OR = (
    "#16181d", "#555a63", "#8c9099", "#1747d6", "#0f2f9a", "#eaf0fd", "#e8b21a")
HACHURES = "repeating-linear-gradient(-60deg, rgba(23, 71, 214, 0.30) 0 0.35mm, transparent 0.35mm 0.95mm)"
MENTION_COURTE = "Fiction librement inspirée de l’univers du football"


def police(nom, fichier, graisse=400, italique=False):
    return (f'@font-face {{ font-family: "{nom}"; font-weight: {graisse}; {"font-style: italic; " if italique else ""}'
            f'src: url("{(RACINE / "fonts" / fichier).as_uri()}"); }}')


CSS = "\n".join([
    police("Anton", "Anton-400.woff2"),
    police("Barlow", "Barlow-400.woff2"), police("Barlow", "Barlow-500.woff2", 500),
    police("Barlow", "Barlow-600.woff2", 600), police("Barlow", "Barlow-700.woff2", 700),
    police("Barlow", "Barlow-400i.woff2", 400, True), police("Barlow", "Barlow-500i.woff2", 500, True),
    police("Barlow Condensed", "BarlowCondensed-600.woff2", 600),
    police("Barlow Condensed", "BarlowCondensed-700.woff2", 700),
]) + f"""
@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 12mm 12mm 15mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "Barlow Condensed"; font-weight: 600; font-size: 9pt; color: {DOUCE}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
html {{ font-family: "Barlow", sans-serif; font-size: 11pt; line-height: 1.45; color: {ENCRE}; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture : le titre dans le blanc du haut, l'image entière jusqu'au bas de la page */
@page couverture {{ margin: 0; @bottom-center {{ content: none; }} }}
.couverture {{ page: couverture; position: relative; height: 185.5mm; overflow: hidden; background: #fff; }}
.couverture img {{ position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: auto; }}
.couverture .entete {{ position: absolute; top: 12mm; left: 0; right: 0; text-align: center; padding: 0 8mm; }}
.couverture .surtitre {{ font-family: "Barlow Condensed"; font-weight: 700; font-size: 7.5pt; letter-spacing: 1.8pt;
  text-transform: uppercase; color: {BLEU}; }}
.couverture .titre-livre {{ font-family: "Anton"; font-size: 30pt; line-height: 1.02; text-transform: uppercase;
  color: {ENCRE}; margin: 2.5mm 0 2mm; }}
.couverture .titre-livre span {{ display: block; color: {BLEU}; }}
.couverture .auteurs {{ font-style: italic; font-size: 12pt; color: {DOUCE}; }}
.couverture .mention {{ font-style: italic; font-size: 7pt; color: {GRIS}; margin-top: 2mm; }}

/* Le résumé, en page 2 */
.resume {{ display: flex; flex-direction: column; justify-content: center; height: 155mm; text-align: center; }}
.resume p {{ font-size: 11pt; line-height: 1.55; }}

/* Chapitres : l'image entière, jamais recadrée, le numéro sur une étiquette bleue en biais à cheval sur son bas */
.illus {{ position: relative; margin: 0 0 8mm; }}
.illus img {{ display: block; width: 100%; height: auto; }}
.pastille {{ position: absolute; left: 50%; bottom: 0; transform: translate(-50%, 50%) skewX(-12deg);
  background: {BLEU}; box-shadow: 0.8mm 0.8mm 0 {ENCRE}; padding: 0.8mm 4mm 0.6mm;
  font-family: "Barlow Condensed"; font-weight: 700; font-size: 8.5pt; letter-spacing: 1.4pt;
  text-transform: uppercase; color: #fff; white-space: nowrap; }}
.pastille span {{ display: inline-block; transform: skewX(12deg); }}
h1 {{ font-family: "Anton"; font-weight: 400; font-size: 19pt; line-height: 1.12; text-align: center; color: {ENCRE};
  margin: 0 0 4mm; }}
/* Chapitres resserrés, pour qu'une fin de quelques lignes ne reste pas seule sur sa page */
.serre {{ font-size: 10.3pt; line-height: 1.38; }}
.serre .illus {{ margin-bottom: 6.5mm; }}
.serre h1 {{ font-size: 17pt; margin-bottom: 3mm; }}
.serre2 {{ font-size: 9.8pt; line-height: 1.33; }}
.serre2 p {{ margin-bottom: 0.45em; }}
/* Une page qui commence par un titre, sans image, garde un grand blanc en haut */
.ouvre-titre::before {{ content: ""; display: block; height: 20mm; }}

/* Séparateur : trois traits en biais, comme les bords des cases */
.separateur {{ display: flex; align-items: center; justify-content: center; gap: 1.2mm; margin: 3mm 0 3mm; break-after: avoid; }}
.separateur::before, .separateur::after {{ content: ""; width: 14mm; height: 0.45mm; background: {ENCRE}; }}
.separateur i {{ display: block; width: 1.5mm; height: 4.5mm; transform: skewX(-20deg); background: {ENCRE}; }}
.separateur i:first-of-type {{ margin-left: 1.5mm; }}
.separateur i:last-of-type {{ margin-right: 1.5mm; }}
.separateur i:nth-of-type(2) {{ background: {BLEU}; }}
.separateur i:nth-of-type(3) {{ background: {OR}; }}

.suite {{ break-inside: avoid; break-before: avoid; }}
.elan {{ text-align: center; font-family: "Barlow Condensed"; font-weight: 700; font-size: 12pt; letter-spacing: 0.5pt;
  text-transform: uppercase; color: {BLEU}; }}
.elan::after {{ content: " →"; color: {OR}; }}

/* La case du dé : trait noir, ombre bleue, faces du dé sur des hachures bleues */
.de {{ margin-top: 4mm; padding: 3mm 4mm 2.5mm; border: 0.5mm solid {ENCRE}; box-shadow: 1.2mm 1.2mm 0 {BLEU};
  font-size: 10pt; line-height: 1.35; break-inside: avoid; }}
.consigne {{ font-family: "Barlow Condensed"; font-weight: 700; font-size: 10.5pt; letter-spacing: 0.4pt;
  text-transform: uppercase; margin: 0 0 2mm; }}
.tirage {{ display: grid; grid-template-columns: 15mm 1fr; gap: 3mm; align-items: center; margin: 0 0 1.6mm; }}
.tirage b {{ text-align: center; background: {HACHURES}; padding: 0.4mm 0;
  font-family: "Barlow Condensed"; font-weight: 700; font-size: 9.5pt; color: {BLEU_FONCE}; }}
.renvoi {{ font-family: "Barlow Condensed"; font-weight: 700; font-size: 10.5pt; letter-spacing: 0.3pt;
  text-transform: uppercase; color: {BLEU}; }}
/* Les fins en tableau à double entrée */
.conditions .consigne {{ font-family: "Barlow"; font-weight: 600; font-size: 10pt; letter-spacing: 0; text-transform: none; }}
.tableau-fins {{ display: grid; grid-template-columns: 24mm 1fr 1fr; gap: 1.5mm; margin-top: 2mm; }}
.tableau-fins .entete {{ font-family: "Barlow Condensed"; font-weight: 600; font-size: 8.5pt; line-height: 1.2; color: {DOUCE}; }}
.tableau-fins .col {{ text-align: center; align-self: end; }}
.tableau-fins .ligne {{ align-self: center; }}
.tableau-fins .croisement {{ display: flex; flex-direction: column; justify-content: center; text-align: center;
  min-height: 12mm; background: repeating-linear-gradient(-60deg, rgba(23, 71, 214, 0.16) 0 0.35mm, transparent 0.35mm 0.95mm); }}
.tableau-fins .croisement .renvoi {{ font-size: 9.5pt; line-height: 1.15; }}
.fin {{ text-align: center; font-family: "Anton"; font-size: 28pt; text-transform: uppercase; letter-spacing: 1pt;
  color: {BLEU}; text-shadow: 0.7mm 0.7mm 0 {OR}; margin-top: 1mm; }}

/* Pages de contexte, de l'arbre et dos */
.contexte h2 {{ font-family: "Anton"; font-weight: 400; font-size: 15pt; text-transform: uppercase; text-align: center;
  color: {ENCRE}; margin: 0 0 4mm; }}
.contexte p {{ font-size: 9.8pt; line-height: 1.4; }}
.dessins {{ display: flex; justify-content: space-around; align-items: flex-end; margin: 0 0 4mm; }}
.dessins figure {{ margin: 0; text-align: center; }}
.dessins img {{ display: block; height: 15mm; margin: 0 auto; }}
.dessins figcaption {{ font-family: "Barlow Condensed"; font-weight: 600; font-size: 7pt; letter-spacing: 0.4pt;
  text-transform: uppercase; color: {BLEU_FONCE}; margin-top: 0.8mm; }}
.citation {{ font-style: italic; font-weight: 500; font-size: 11.5pt; line-height: 1.3; text-align: center;
  color: {BLEU_FONCE}; margin: 3mm 4mm 4mm; }}
.contexte .credits {{ font-size: 9pt; color: {DOUCE}; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; border: 0.3mm solid {ENCRE}; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
@page arbre {{ margin: 8mm 6mm 9mm; @bottom-center {{ content: none; }} }}
.arbre {{ page: arbre; height: 168mm; display: flex; flex-direction: column; align-items: center; }}
.arbre img {{ flex: 1; min-height: 0; width: 100%; object-fit: contain; }}
.dos {{ display: flex; flex-direction: column; justify-content: flex-end; height: 156mm; text-align: center;
  font-size: 9pt; color: {DOUCE}; }}
.dos .avertissement {{ font-style: italic; font-size: 8.5pt; margin-bottom: 4mm; }}
"""

SEPARATEUR = '<div class="separateur"><i></i><i></i><i></i></div>'


def e(texte):
    return html.escape(texte, quote=False)


def cle_de(nom):
    """Clé numérique de chaque partie : 0 pour le prologue, le numéro pour un chapitre."""
    return 0 if nom == "Prologue" else int(nom.split()[-1])


def renvoi(cible, pages):
    return f"Poursuis au chapitre {cible}, page {pages.get(int(cible), '00')}"


def tableau_des_fins(consigne, conditions, pages):
    """Les quatre fins : le parcours d'Aylan en ligne, celui d'Adam en colonne, le renvoi au croisement."""
    cases = {}
    for condition, chapitre in conditions:
        c = condition.replace("’", "'")
        cases[("quitté" not in c, "mais pas Adam" not in c and "n'est pas devenu" not in c)] = chapitre
    assert len(cases) == 4, conditions
    corps = ('<div></div><div class="entete col">Adam est devenu footballeur professionnel</div>'
             '<div class="entete col">Adam n’est pas devenu footballeur professionnel</div>')
    for aylan, libelle in ((True, "Aylan est devenu footballeur professionnel"),
                           (False, "Aylan a quitté le football en club")):
        corps += f'<div class="entete ligne">{libelle}</div>'
        for adam in (True, False):
            n = cases[(aylan, adam)]
            corps += (f'<div class="croisement"><span class="renvoi">Chapitre {n}</span>'
                      f'<span class="renvoi">page {pages.get(int(n), "00")}</span></div>')
    return (f'<div class="de conditions"><p class="consigne">{e(consigne)}</p>'
            f'<div class="tableau-fins">{corps}</div></div>')


def chapitre(ch, suivant, pages):
    cle = cle_de(ch["nom"])
    serre = (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    morceaux = []
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    if image.exists():
        largeur, hauteur = Image.open(image).size
        assert largeur > hauteur, f"Image en hauteur non prévue : {image.name}"
        pastille = "" if ch["nom"] == "Prologue" else f'<span class="pastille"><span>{e(ch["numero"])}</span></span>'
        morceaux.append(f'<section class="page-seule{serre}"><span class="marque">@@CH{cle}@@</span>'
                        f'<div class="illus"><img src="{image.as_uri()}" alt="">{pastille}</div>')
    else:
        morceaux.append(f'<section class="page-seule ouvre-titre{serre}"><span class="marque">@@CH{cle}@@</span>')
    morceaux.append(f'<h1>{e(ch["titre"])}</h1>')

    corps, consigne, tirages, conditions, cible, fin = lire_choix(ch)
    morceaux += [f"<p>{e(p)}</p>" for p in corps]

    suite = []
    if tirages:
        suite.append(f'<div class="de"><p class="consigne">{e(consigne)}</p>' + "".join(
            f'<div class="tirage"><b>{e(faces)}</b><span class="renvoi">{e(renvoi(n, pages))}</span></div>'
            for faces, n in tirages) + "</div>")
    elif conditions:
        suite.append(tableau_des_fins(consigne, conditions, pages))
    # Dans un livre, inutile d'écrire « Poursuis au chapitre suivant » : on tourne simplement la page
    elif cible and not (suivant is not None and int(cible) == suivant):
        suite += [SEPARATEUR, f'<p class="elan">{e(renvoi(cible, pages))}</p>']
    if fin:
        suite += [SEPARATEUR, '<div class="fin">Fin</div>']
    if suite:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def dessin(fichier, nom):
    return (f'<figure><img src="{(RACINE / "images" / "dessins" / fichier).as_uri()}" alt="">'
            f'<figcaption>{e(nom)}</figcaption></figure>')


def document(pages, blanches=0):
    couverture = (
        '<section class="couverture sans-numero">'
        f'<img src="{(RACINE / "images/couverture.jpg").as_uri()}" alt="">'
        '<div class="entete"><div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        '<div class="titre-livre">Deux frères,<span>une coupe</span></div>'
        f'<div class="auteurs">une histoire par {e(AUTEURS)}</div>'
        f'<div class="mention">{MENTION_COURTE}</div></div></section>'
        '<section class="page-seule sans-numero"><div class="resume">'
        + "".join(f"<p>{e(p)}</p>" for p in SYNOPSIS.split("\n\n")) + SEPARATEUR + "</div></section>"
    )
    chapitres_lus = lire_chapitres()
    cles = [cle_de(ch["nom"]) for ch in chapitres_lus]
    chapitres = "".join(chapitre(ch, cles[i + 1] if i + 1 < len(cles) else None, pages)
                        for i, ch in enumerate(chapitres_lus))

    paragraphes = [q for p in CONTEXTE for q in p.split("\n\n")]

    def para(p):
        return f"<p>{e(p).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')}</p>"
    fiches = RACINE / "images" / "fiches"
    contexte = (
        '<section class="page-seule contexte"><div class="dessins">'
        + dessin("aylan.png", "Aylan") + dessin("coupe.png", "La coupe du monde")
        + dessin("adam.png", "Adam") + dessin("but.png", "Le but")
        + '</div><h2>Comment est née cette histoire</h2>'
        + "".join(para(p) for p in paragraphes[:4])
        + f'<p class="citation">« {e(CITATION)} »</p>'
        + "".join(para(p) for p in paragraphes[4:])
        + f'<p class="credits">Une histoire librement inspirée du récit d’Aylan et d’Adam.<br>Réalisation du livre : '
          "Laboratoire d’Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches de l’atelier</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit_adam.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_aylan.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_adam.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    arbre = ('<section class="page-seule contexte arbre sans-numero"><h2>L’arbre de l’histoire</h2>'
             f'<img src="{(RACINE / "images/arbre.svg").as_uri()}" alt=""></section>')
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    dos = ('<section class="page-seule sans-numero"><div class="dos">'
           f'<p class="avertissement">{e(AVERTISSEMENT)}</p>'
           f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par Aylan et Adam pendant l’atelier "
           "« La quête du curry, une histoire dont tu es le héros », à la bibliothèque Li Campaneto "
           "(bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.</p><p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{chapitres}{contexte}{arbre}{vides}{dos}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def reperer_pages(pdf):
    """Numéro de page où commence chaque partie, d'après les marques invisibles."""
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        texte = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        for cle in re.findall(r"@@CH(\d+)@@", texte):
            pages[int(cle)] = n
    return pages, total


def stabiliser(source, pdf, pages):
    for _ in range(5):
        source.write_text(document(pages), encoding="utf-8")
        imprimer(source, pdf)
        nouvelles, total = reperer_pages(pdf)
        if nouvelles == pages:
            return pages, total
        pages = nouvelles
    raise SystemExit("Les numéros de page ne se stabilisent pas.")


def queues_courtes(pdf, pages, seuil=6):
    """Chapitres dont la dernière page ne porte que quelques lignes (à surveiller à la relecture)."""
    debuts = sorted((page, cle) for cle, page in pages.items())
    courtes = []
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        fin = suivant - 1
        if fin <= debut:
            continue
        texte = subprocess.run(["pdftotext", "-f", str(fin), "-l", str(fin), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        lignes = [l for l in texte.splitlines() if l.strip() and not l.strip().isdigit()]
        if len(lignes) <= seuil:
            courtes.append(cle)
    return courtes


def remplissage(pdf, n):
    """Part de la hauteur utile de la page n occupée par le contenu (0 à 1)."""
    ppm = subprocess.run(["pdftoppm", "-r", "30", "-gray", "-f", str(n), "-l", str(n), str(pdf)],
                         capture_output=True, check=True).stdout
    entete = ppm.split(b"\n", 3)
    largeur, hauteur = map(int, entete[1].split())
    pixels = entete[3]
    bas_utile = int(hauteur * (1 - 15 / HAUTEUR_PAGE)) - 2      # au-dessus du numéro de page
    lignes = [y for y in range(bas_utile) if min(pixels[y * largeur:(y + 1) * largeur]) < 200]
    return (lignes[-1] / bas_utile) if lignes else 0


def pages_trouees(pdf, pages, seuil=0.8):
    """Chapitres dont une page intermédiaire est restée à moitié vide (le dernier paragraphe est parti avec
    la case du dé sur la page suivante)."""
    debuts = sorted((page, cle) for cle, page in pages.items())
    trouees = []
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        if any(remplissage(pdf, n) < seuil for n in range(debut, suivant - 1)):
            trouees.append(cle)
    return trouees


SERRES, SERRES2 = set(), set()


def composer(dossier):
    """Compose le livret ; les chapitres dont la fin tient en quelques lignes sont resserrés (un cran, puis
    deux), et un resserrement qui ne sert à rien est retiré."""
    source = Path(dossier) / "livret.html"
    pdf = Path(dossier) / "livret.pdf"
    pages, total = stabiliser(source, pdf, {})
    for _ in range(4):
        courtes = set(queues_courtes(pdf, pages)) | set(pages_trouees(pdf, pages))
        nouvelles = (courtes - SERRES) | {c for c in courtes & SERRES if c not in SERRES2}
        if not nouvelles:
            break
        SERRES2.update(courtes & SERRES)
        SERRES.update(courtes)
        pages, total = stabiliser(source, pdf, {})
    blanches = (-total) % 4
    if blanches:
        source.write_text(document(pages, blanches), encoding="utf-8")
        imprimer(source, pdf)
        assert reperer_pages(pdf)[0] == pages
    return pdf, pages


def traits_de_coupe(dossier):
    x0, y0 = (297 - 2 * LARGEUR_PAGE) / 2, (210 - HAUTEUR_PAGE) / 2
    gauche, droite, haut, bas = x0, x0 + 2 * LARGEUR_PAGE, y0, y0 + HAUTEUR_PAGE
    coupe = [f'<line x1="0" y1="{y}" x2="297" y2="{y}"/>' for y in (haut, bas)]
    coupe += [f'<line x1="{x}" y1="0" x2="{x}" y2="210"/>' for x in (gauche, droite)]
    pli = x0 + LARGEUR_PAGE
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#c9c9c9" stroke-width="0.2">{"".join(coupe)}</g>'
        f'<line x1="{pli}" y1="0" x2="{pli}" y2="210" stroke="#c4d2f5" stroke-width="0.2"/>'
        '</svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def imposer(lecture, traits, sortie, bord_long):
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()

    def face(gauche, droite, retournee):
        feuille = PageObject.create_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            feuille.merge_transformed_page(pages[indice - 1], Transformation().translate(x, y0))
        if retournee:
            feuille.rotate(180)
        ecrivain.add_page(feuille)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Chapitres resserrés :", ", ".join(str(c) + ("+" if c in SERRES2 else "") for c in sorted(SERRES)) or "aucun")
    print("Pages à moitié vides :", ", ".join(str(c) for c in pages_trouees(lecture, pages)) or "aucune")
    print("Fins de chapitre de quelques lignes :", ", ".join(str(c) for c in queues_courtes(lecture, pages)) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
