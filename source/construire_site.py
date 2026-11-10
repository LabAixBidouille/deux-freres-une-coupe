#!/usr/bin/env python3
"""Construit index.html de « Deux frères, une coupe » à partir de source/texte.md.

Le moteur Harlowe est conservé tel quel dans index.html : seules les pages et la feuille de style du livre
sont régénérées.

Mise en page propre au livre d'Aylan et d'Adam, tirée des images : un manga à l'encre noire sur papier
blanc, où seul le bleu des Bleus est en couleur, avec l'or des coups de pinceau de la couverture. Les cases
des images sont coupées en biais : les étiquettes, les séparateurs et les boutons le sont aussi.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import hashlib
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "Deux frères, une coupe"
AUTEURS = "Aylan et Adam"

SYNOPSIS = (
    "Dans une cour d’Aix-en-Provence, deux frères jouent au foot entre deux poubelles. Leur ballon est vieux "
    "et dégonflé, mais leurs rêves, eux, ne cessent de grandir.\n\n"
    "Adam rêve de soulever un jour la Coupe du monde. Aylan, qui préférait autrefois le dessin, découvre à "
    "son tour le plaisir de jouer. Ensemble, ils s’entraînent, progressent et s’encouragent. Mais sur le "
    "chemin qui mène aux grands stades, tout ne se passe pas toujours comme prévu…\n\n"
    "Une sélection, une rencontre, un geste : parfois, il suffit d’un instant pour changer une histoire."
)

AVERTISSEMENT_COURT = (
    "Cette histoire est une fiction librement inspirée de l’univers du football. Si certains clubs et "
    "certaines compétitions existent réellement, les personnages, leurs parcours, les événements et les "
    "dialogues ont été imaginés par Aylan et Adam lors de l’atelier « La quête du curry, une histoire dont tu "
    "es le héros », à la bibliothèque Li Campaneto d’Aix-en-Provence, en octobre 2026."
)
AVERTISSEMENT = (
    "Une fiction librement inspirée du monde du football. Les clubs et les compétitions cités existent, "
    "mais les personnages, les situations et les paroles sont entièrement imaginaires. Ce livre n’est "
    "ni approuvé ni soutenu par ces clubs, par leurs fédérations ni par les organisateurs de ces "
    "compétitions."
)

# Texte de Manon, modèle commun aux livres de l'atelier ; seule change la phrase sur le genre
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Aylan et Adam ont choisi d’écrire une histoire de sport, ancrée dans le monde réel, où deux frères "
    "poursuivent le même rêve. Un défi pour une histoire à embranchements, puisque les parcours des deux "
    "frères se croisent et que chaque combinaison doit conduire à une fin qui ait un sens.",
    "L’atelier ne durant que deux heures, nous tenions à offrir à chaque enfant un livre complet pour "
    "illustrer leur travail et les rendre fiers de leurs productions. Le L.A.B a donc prolongé et mis en "
    "forme leur récit à l’aide d’outils numériques (l’intelligence artificielle a notamment permis "
    "d’aboutir à une histoire achevée et à un ensemble de visuels correspondant à leurs descriptions mais "
    "uniformes tout au long de la lecture).\n\n<b>À son origine, il y a avant tout les idées, les "
    "personnages et les dessins d’Aylan et d’Adam.</b>",
]
# Une phrase de la fiche récit d'Aylan, à peine remise au propre
CITATION = "Aylan, grâce à son frère, a pu découvrir le foot et aimerait devenir footballeur professionnel."

CSS = """
@font-face { font-family: "Anton"; font-weight: 400; font-display: swap; src: url("fonts/Anton-400.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-weight: 400; font-display: swap; src: url("fonts/Barlow-400.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-weight: 500; font-display: swap; src: url("fonts/Barlow-500.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-weight: 600; font-display: swap; src: url("fonts/Barlow-600.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-weight: 700; font-display: swap; src: url("fonts/Barlow-700.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-style: italic; font-weight: 400; font-display: swap; src: url("fonts/Barlow-400i.woff2") format("woff2"); }
@font-face { font-family: "Barlow"; font-style: italic; font-weight: 500; font-display: swap; src: url("fonts/Barlow-500i.woff2") format("woff2"); }
@font-face { font-family: "Barlow Condensed"; font-weight: 500; font-display: swap; src: url("fonts/BarlowCondensed-500.woff2") format("woff2"); }
@font-face { font-family: "Barlow Condensed"; font-weight: 600; font-display: swap; src: url("fonts/BarlowCondensed-600.woff2") format("woff2"); }
@font-face { font-family: "Barlow Condensed"; font-weight: 700; font-display: swap; src: url("fonts/BarlowCondensed-700.woff2") format("woff2"); }

/* Couleurs prises aux images : l'encre du manga, le gris des sweats, le bleu des Bleus, l'or des coups de
   pinceau de la couverture. Le papier est blanc. */
:root {
  --encre: #16181d;
  --encre-douce: #555a63;
  --gris: #8c9099;
  --bleu: #1747d6;
  --bleu-fonce: #0f2f9a;
  --bleu-pale: #eaf0fd;
  --or: #e8b21a;
  --or-fonce: #b9850a;
  --papier: #ffffff;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); }

tw-story {
  font-family: "Barlow", "Helvetica Neue", Arial, sans-serif;
  font-size: 1.12em;
  line-height: 1.65;
  padding: 0.8em 1.2em 3em;
}
tw-passage { max-width: 1120px; margin: 0 auto; }
tw-passage:has(.garde) { max-width: 1340px; }
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Chapitres centrés : l'image en tête, entière, à la largeur du texte, avec le cadre noir des cases ; le
   numéro du chapitre sur une étiquette bleue en biais, à cheval sur le bas de l'image */
.page { max-width: 46em; margin: 0 auto; }
.cote { position: relative; margin: 0 auto; }
.cote img { display: block; width: 100%; height: auto; }
.texte { margin: 2.4em auto 0; }
.page:not(:has(.cote)) .texte { margin-top: 1.5em; }
.numero-image {
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translate(-50%, 50%) skewX(-12deg);
  padding: 0.25em 1.2em 0.2em;
  background: var(--bleu);
  box-shadow: 4px 4px 0 var(--encre);
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 1em;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  white-space: nowrap;
  color: #fff;
}
.numero-image span { display: inline-block; transform: skewX(12deg); }

.chapitre { text-align: center; margin: 0 0 1.1em; font-weight: 400; font-size: 1em; line-height: 1.1; }
.chapitre .numero {
  display: block;
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--bleu);
  margin-bottom: 0.4em;
}
.chapitre .titre {
  display: block;
  font-family: "Anton", Impact, sans-serif;
  font-weight: 400;
  font-size: 2.3em;
  line-height: 1.12;
  letter-spacing: 0.01em;
  color: var(--encre);
}

/* Séparateur : trois traits en biais, comme les bords des cases */
.separateur { display: flex; align-items: center; justify-content: center; gap: 0.32em; margin: 1.8em 0 1.3em; }
.separateur::before, .separateur::after { content: ""; width: 4em; height: 2px; background: var(--encre); }
.separateur .embleme { display: flex; gap: 0.28em; margin: 0 0.4em; }
.separateur .embleme i { display: block; width: 0.42em; height: 1.3em; transform: skewX(-20deg); background: var(--encre); }
.separateur .embleme i:nth-child(2) { background: var(--bleu); }
.separateur .embleme i:nth-child(3) { background: var(--or); }

/* Lien Couverture */
.retour { max-width: 1120px; margin: 0 auto 0.6em; text-align: left; }
.retour tw-link, .retour .enchantment-link, .lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 600;
  font-size: 0.95em;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--encre-douce);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--bleu); }

tw-link, .enchantment-link { color: var(--bleu-fonce); font-weight: 600; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--bleu); }

/* Poursuis : en capitales condensées bleues, la flèche avance au survol */
.elan { text-align: center; margin-top: 0.4em; }
.elan tw-link, .elan .enchantment-link {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 1.3em;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--bleu);
  text-decoration: none;
  transition: color 0.2s ease;
}
.elan tw-link::after, .elan .enchantment-link::after { content: "→"; color: var(--or); display: inline-block; margin-left: 0.35em; transition: transform 0.2s ease; }
.elan tw-link:hover::after, .elan .enchantment-link:hover::after { transform: translateX(5px); }
.elan tw-link:hover, .elan .enchantment-link:hover { color: var(--bleu-fonce); }

/* Le tirage : une case au trait noir, les choix à gauche, le ballon à droite ; la même case sans ballon
   pour les fins qui dépendent du parcours des deux frères */
.de {
  display: flex;
  align-items: center;
  gap: 1.2em;
  margin-top: 1.6em;
  padding: 0.75em 1.1em;
  border: 2px solid var(--encre);
  box-shadow: 5px 5px 0 var(--bleu);
  font-size: 0.95em;
  line-height: 1.45;
  background: #fff;
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne {
  display: block;
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 1.05em;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--encre);
  margin-bottom: 0.45em;
}
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.35em; }
.tirage { display: inline-flex; align-items: baseline; gap: 0.7em; }
.tirage b {
  flex: none;
  display: inline-block;
  min-width: 4.6em;
  box-sizing: border-box;
  padding: 0.02em 0.6em;
  transform: skewX(-12deg);
  background: var(--bleu-pale);
  color: var(--bleu-fonce);
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
  text-align: center;
  white-space: nowrap;
}
.de .choix tw-link, .de .choix .enchantment-link {
  display: inline;
  white-space: nowrap;
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 1.05em;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--bleu);
  text-decoration: none;
  transition: color 0.2s ease;
}
.de .choix tw-link:hover, .de .choix .enchantment-link:hover { color: var(--bleu-fonce); }
/* Les fins au choix : la condition en entier, le renvoi dessous */
.conditions .choix { align-items: stretch; }
.conditions .consigne { font-family: "Barlow", sans-serif; font-weight: 600; font-size: 1em; letter-spacing: 0; text-transform: none; }
.conditions .tirage { display: block; }
.conditions .tirage + .tirage { margin-top: 0.5em; padding-top: 0.5em; border-top: 1px solid #dfe2e8; }
.conditions .condition { display: block; }

/* Le ballon sert de dé : il rebondit tant qu'on ne l'a pas touché, roule puis laisse voir le nombre tiré.
   Le résultat écrit n'est lu que par les lecteurs d'écran. */
.lancer { flex: none; display: flex; flex-direction: column; align-items: center; gap: 0.3em; }
.ballon {
  position: relative;
  width: 4.4em;
  height: 4.4em;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
}
.ballon .cuir { position: absolute; inset: 0; background: url("images/ballon.png") no-repeat center / contain; transition: opacity 0.4s ease; }
.ballon:not(.touche) .cuir { animation: rebond 1.6s cubic-bezier(.5, 0, .5, 1) infinite; }
@keyframes rebond { 0%, 100% { transform: translateY(0); } 45% { transform: translateY(-9px) rotate(-8deg); } 60% { transform: translateY(0) scaleY(0.94); } }
.ballon:hover .cuir { transform: rotate(-20deg); }
.ballon.roule .cuir { animation: roule 0.9s cubic-bezier(.4, 0, .2, 1); }
@keyframes roule { from { transform: rotate(0); } to { transform: rotate(720deg); } }
.ballon.montre .cuir { opacity: 0.18; }
.ballon .face {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Anton", Impact, sans-serif;
  font-size: 2.9em;
  line-height: 1;
  color: var(--bleu);
  opacity: 0;
  transition: opacity 0.4s ease 0.1s;
}
.ballon.montre .face { opacity: 1; }
.lancer .aide { font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 500; font-size: 0.85em; letter-spacing: 0.05em; text-transform: uppercase; color: var(--encre-douce); }
.resultat { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

/* Fin */
.fin { text-align: center; margin-top: 0.4em; }
.fin .mot-fin {
  display: inline-block;
  font-family: "Anton", Impact, sans-serif;
  font-size: 3.4em;
  line-height: 1;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--bleu);
  text-shadow: 3px 3px 0 var(--or);
  margin-bottom: 0.4em;
}
.secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5em 1.6em; }
.secondaires tw-link, .secondaires .enchantment-link {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 1.05em;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--bleu-fonce);
  text-decoration: none;
  border-bottom: 3px solid var(--or);
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover { color: var(--bleu); }

/* Couverture sur deux colonnes, tout visible sans défiler : l'image entière à gauche, à droite le titre, le
   résumé et les boutons */
tw-story:has(.garde) { padding-top: 0; padding-bottom: 0; }
.garde {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(20em, 27em);
  gap: 3.2em;
  align-items: center;
  justify-content: center;
  padding: 3vh 0;
  box-sizing: border-box;
}
.garde-image { display: flex; justify-content: center; }
.garde-image img { display: block; width: auto; max-width: 100%; height: min(88vh, 46em); object-fit: contain; }
.garde-texte { display: flex; flex-direction: column; align-items: center; text-align: center; gap: clamp(0.7em, 2.2vh, 1.2em); }
.garde-entete { display: flex; flex-direction: column; align-items: center; }
.garde .surtitre {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700;
  font-size: 0.9em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--bleu);
}
.garde .grand-titre {
  margin: 0.2em 0 0.25em;
  font-family: "Anton", Impact, sans-serif;
  font-size: clamp(2.6em, 8vh, 3.9em);
  line-height: 1.02;
  text-transform: uppercase;
  color: var(--encre);
}
.garde .grand-titre .ligne2 { display: block; color: var(--bleu); }
.garde .nom-auteur { font-family: "Barlow", sans-serif; font-style: italic; font-size: 1.15em; color: var(--encre-douce); }
.garde .separateur { margin: 0; }
.garde .synopsis { font-size: clamp(0.88em, 2.1vh, 0.98em); line-height: 1.6; }
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-flex;
  align-items: center;
  gap: 0.55em;
  font-family: "Anton", Impact, sans-serif;
  font-weight: 400;
  font-size: 1.75em;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--bleu);
  text-decoration: none;
  transition: color 0.2s ease;
}
.garde .commencer tw-link::before, .garde .commencer .enchantment-link::before,
.garde .commencer tw-link::after, .garde .commencer .enchantment-link::after {
  content: "";
  width: 0.95em;
  height: 0.95em;
  background: url("images/ballon.png") no-repeat center / contain;
  transition: transform 0.4s ease;
}
.garde .commencer tw-link:hover { color: var(--bleu-fonce); }
.garde .commencer tw-link:hover::before { transform: rotate(-180deg); }
.garde .commencer tw-link:hover::after { transform: rotate(180deg); }
/* Les deux liens secondaires, séparés par un trait en biais */
.garde .secondaires { gap: 0; font-size: 0.95em; }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link { border: none; font-weight: 600; color: var(--encre-douce); transition: color 0.2s ease; }
.garde .secondaires tw-link:hover { color: var(--bleu); }
.garde .secondaires .point { display: inline-block; width: 2px; height: 1em; margin: 0.15em 0.9em 0; transform: skewX(-20deg); background: var(--or); }
/* La mention, dans une bande de bas de page sur toute la largeur de la couverture */
.garde { position: relative; }
.garde .mention {
  display: block;
  padding: 0.7em 1.5em;
  background: #f1f3f7;
  border-top: 2px solid var(--bleu);
  font-size: 0.8em;
  line-height: 1.45;
  font-style: italic;
  color: var(--encre-douce);
  text-align: center;
}
@media (min-width: 861px) {
  .garde .mention { position: absolute; bottom: 0; left: calc(50% - 50vw); width: 100vw; box-sizing: border-box;
                    padding: 1.1vh max(1.5em, calc(50vw - 40em)); font-size: clamp(11px, 1.55vh, 15px); }
}
@media (max-width: 860px) { .garde .mention { display: block; margin-top: 1em; } }
@media (max-width: 860px) {
  .garde { min-height: 0; grid-template-columns: minmax(0, 1fr); gap: 1.2em; padding-top: 1em; }
  .garde-image img { height: auto; width: 100%; }
}

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin: 0.5em 0 1.5em; }
.arbre h1 { margin: 0; font-family: "Anton", Impact, sans-serif; font-weight: 400; font-size: 2.3em; text-transform: uppercase; color: var(--encre); }
.arbre .arbre-sous-titre { display: block; font-style: italic; color: var(--encre-douce); margin-top: 0.3em; }
.arbre img { display: block; width: 100%; max-width: 960px; height: auto; margin: 0 auto; }

/* Page « Comment est née cette histoire » */
.contexte { max-width: 40em; margin: 1em auto 0; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1 { font-family: "Anton", Impact, sans-serif; font-weight: 400; font-size: 2.3em; line-height: 1.15; text-transform: uppercase; color: var(--encre); margin: 1.2em 0 0; }
.contexte-texte { text-align: left; }
.citation {
  margin: 1.8em auto;
  max-width: 28em;
  text-align: center;
  font-family: "Barlow", sans-serif;
  font-style: italic;
  font-weight: 500;
  font-size: 1.3em;
  line-height: 1.4;
  color: var(--bleu-fonce);
}
.citation .source { display: block; margin-top: 0.6em; font-family: "Barlow Condensed", sans-serif; font-style: normal; font-weight: 600; font-size: 0.6em; letter-spacing: 0.14em; text-transform: uppercase; color: var(--encre-douce); }
.dessins { display: flex; flex-wrap: wrap; justify-content: space-around; align-items: flex-end; gap: 1em 0.8em; margin: 0.6em auto 0.4em; }
.dessins figure { margin: 0; }
.dessins img { display: block; height: 7.5em; width: auto; margin: 0 auto; }
.dessins img.large { height: 8.2em; }
.dessins figcaption { margin-top: 0.4em; font-family: "Barlow Condensed", sans-serif; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.85em; color: var(--bleu-fonce); }
.table-fiches { margin: 2.6em auto 0; }
.table-fiches .titre-table { display: block; font-family: "Anton", Impact, sans-serif; font-size: 1.4em; text-transform: uppercase; color: var(--encre); margin-bottom: 1.2em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 1.6em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.7em; font-style: italic; color: var(--encre-douce); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 13em; width: auto; border: 2px solid var(--encre); box-shadow: 4px 4px 0 var(--bleu); transition: transform 0.2s ease; }
.miniature:hover img { transform: scale(1.04); }
.contexte .credits { display: block; margin-top: 2em; font-size: 0.9em; color: var(--encre-douce); }
.contexte .avertissement { display: block; margin-top: 0.8em; font-size: 0.82em; font-style: italic; color: var(--gris); }
.contexte .secondaires { margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(22, 24, 29, 0.88); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; }

/* Case du dé : les faces du dé passées en hachures bleues de crayon de couleur, au
   trait un peu tremblé comme les images ; les fins au choix de la même façon */
.tirage b { position: relative; isolation: isolate; transform: none; padding: 0.05em 0.6em; background: none; }
.tirage b::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background: repeating-linear-gradient(-60deg, rgba(23, 71, 214, 0.26) 0 1.5px, transparent 1.5px 4px);
  filter: url(#tremble);
}
.conditions .tirage + .tirage { border-top: none; }
/* Le ballon et sa légende au bout de la case, centrés dans une zone fixe, à égale distance du bord */
.de:not(.conditions) .lancer { flex: none; width: 8.5em; align-self: center; padding-top: 0.9em; }
@media (max-width: 600px) { .de:not(.conditions) .lancer { width: auto; padding-top: 0; } }

/* La couverture tient toujours dans l'écran, sans défiler : la page fait la hauteur de la fenêtre, l'image ne
   la dépasse jamais, et le texte de droite prend une taille proportionnelle à cette hauteur */
@media (min-width: 861px) {
  tw-story:has(.garde) { height: 100vh; overflow: hidden; }
  .garde { height: 100vh; min-height: 0; }
  tw-passage:has(.garde) { max-width: 1440px; }
  .garde { grid-template-columns: auto auto; gap: 2.6em; padding: 1vh 0 9vh; }
  .garde-image img { height: 68vh; max-height: 68vh; }
  .garde-texte { width: 31em; font-size: clamp(14px, 2.3vh, 24px); gap: 0.75em; }
  .garde .grand-titre { font-size: 3.7em; }
  .garde .synopsis { font-size: 0.95em; }
}

@media (max-width: 600px) {
  tw-story { font-size: 1.05em; padding: 0.8em 1em 3em; }
  .chapitre .titre { font-size: 1.9em; }
  .de { flex-direction: column-reverse; align-items: stretch; }
  .lancer { align-self: center; }
  .tirage { flex-wrap: wrap; }
  .miniature img { height: 10em; }
}
"""


def e(texte):
    return html.escape(texte, quote=True)


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        numero, titre = lignes[0].strip().split(". ", 1)
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": numero, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


SEPARATEUR = '<div class="separateur"><span class="embleme"><i></i><i></i><i></i></span></div>'

DE_VIRTUEL = (
    '<div class="lancer"><button class="ballon" type="button" aria-label="Toucher le ballon pour lancer le dé">'
    '<span class="cuir"></span><span class="face"></span></button>'
    '<span class="aide">touche le ballon</span>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

SCRIPT = """

// Filtre du trait de crayon, utilisé par la feuille de style
document.body.insertAdjacentHTML('beforeend', '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><filter id="tremble" x="-6%" y="-20%" width="112%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="2.4" xChannelSelector="R" yChannelSelector="G"/></filter></defs></svg>');
// Le ballon roule puis montre le nombre tiré ; il ne choisit jamais à la place du lecteur
document.addEventListener('click', function (evenement) {
  var ballon = evenement.target.closest('.ballon');
  if (!ballon || ballon.classList.contains('roule')) return;
  var resultat = ballon.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  ballon.classList.add('touche');
  ballon.classList.remove('montre');
  ballon.classList.add('roule');
  resultat.textContent = '';
  setTimeout(function () {
    ballon.classList.remove('roule');
    ballon.querySelector('.face').textContent = face;
    ballon.classList.add('montre');
    resultat.textContent = 'Le ballon montre ' + face + '.';
  }, 900);
});

// Page de contexte : une miniature s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
"""


def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


# Renvois du texte de Manon, tous affichés « Poursuis au chapitre X » sur le site
TIRAGE = re.compile(r"^(\d(?:, \d)*(?: ou \d)?) : découvre la suite au chapitre (\d+)\.?$")
CONDITION = re.compile(r"^(Si .*?), découvre leur histoire au chapitre (\d+)\.?$")
RENVOI = re.compile(r"^Découvre .*?(?:au|dès le) chapitre (\d+)\.?$")


def nom_passage(numero):
    return f"Chapitre {numero}"


def lire_choix(ch):
    """Rend (corps, consigne, tirages, conditions, renvoi, fin) pour un chapitre."""
    corps, consigne, tirages, conditions, renvoi, fin = [], None, [], [], None, False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                ligne = ligne[2:].strip()
                if m := TIRAGE.match(ligne):
                    tirages.append((m[1], m[2]))
                elif m := CONDITION.match(ligne):
                    conditions.append((m[1], m[2]))
                elif m := RENVOI.match(ligne):
                    renvoi = m[1]
                else:
                    raise ValueError(f"Choix illisible dans {ch['nom']} : {ligne}")
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            consigne = p[2:-2].strip()
        elif p.startswith("*") and p.endswith("*"):
            continue
        else:
            corps.append(p)
    # La phrase qui annonce les fins au choix devient la consigne de leur case
    if conditions and corps and corps[-1].endswith(":"):
        consigne = corps.pop()
    return corps, consigne, tirages, conditions, renvoi, fin


def passage_chapitre(ch):
    corps, consigne, tirages, conditions, renvoi, fin = lire_choix(ch)
    poursuis = lambda n: lien(f"Poursuis au chapitre {n}", nom_passage(n))

    image = RACINE / f"images/chapitres/{illustration(ch['nom'])}.jpg"
    cote = ""
    if image.exists():
        numero = ("" if ch["nom"] == "Prologue"
                  else f'<span class="numero-image"><span>{ch["numero"]}</span></span>')
        cote = (f'<div class="cote"><img src="images/chapitres/{image.name}" alt="{ch["titre"]}">'
                f"{numero}</div>")

    suite = []
    if tirages:
        lignes = "".join(f'<span class="tirage"><b>{d}</b><span>{poursuis(n)}</span></span>' for d, n in tirages)
        suite.append(f'<div class="de"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{lignes}</div></div>{DE_VIRTUEL}</div>')
    elif conditions:
        lignes = "".join(f'<span class="tirage"><span class="condition">{c}.</span>{poursuis(n)}</span>'
                         for c, n in conditions)
        suite.append(f'<div class="de conditions"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{lignes}</div></div></div>')
    else:
        suite.append(SEPARATEUR)
        if renvoi:
            suite.append(f'<div class="elan">{poursuis(renvoi)}</div>')
    if fin:
        suite.append('<div class="fin"><span class="mot-fin">Fin</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
                     f'{lien("Relire depuis le début", "Prologue")}</div></div>')
    entete = ('<h1 class="chapitre">' if ch["nom"] == "Prologue" or cote
              else f'<h1 class="chapitre"><span class="numero">{ch["numero"]}</span>')
    texte = (f'<div class="texte">{entete}<span class="titre">{ch["titre"]}</span></h1>'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    return f'<div class="page">{cote}{texte}</div>'


def illustration(nom):
    """prologue, chapitre-01…"""
    if nom == "Prologue":
        return "prologue"
    return f"chapitre-{int(nom.split()[-1]):02d}"


def passage_garde():
    return (
        '<div class="garde"><div class="garde-image"><img src="images/couverture.jpg" '
        'alt="Aylan et Adam dos à dos, entre la cour où ils ont commencé à jouer et un grand stade"></div>'
        '<div class="garde-texte"><div class="garde-entete">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        '<span class="grand-titre">Deux frères,<span class="ligne2">une coupe</span></span>'
        f'<span class="nom-auteur">une histoire par {AUTEURS}</span></div>'
        f'<div class="synopsis">{SYNOPSIS}</div>'
        f'<div class="commencer">{lien("Commencer l’histoire", "Prologue")}</div>{SEPARATEUR}'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
        f'<span class="point"></span>{lien("L’arbre de l’histoire", "L’arbre de l’histoire")}</div>'
        "</div>"
        f'<span class="mention">{AVERTISSEMENT_COURT}</span></div>'
    )


def version_arbre():
    chemin = RACINE / "images" / "arbre.svg"
    return hashlib.md5(chemin.read_bytes()).hexdigest()[:8] if chemin.exists() else "0"


def passage_arbre():
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Couverture", "Page de garde")}</span>'
        f'<div class="arbre-tete"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l’histoire imaginée par {AUTEURS}</span></div>'
        # Le numéro de version force le navigateur à recharger l'arbre quand il change
        f'<img src="images/arbre.svg?v={version_arbre()}" alt="L’arbre de toutes les branches de l’histoire"></div>'
    )


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def dessin(fichier, legende, auteur, classe=""):
    return (f'<figure><img class="{classe}" src="images/dessins/{fichier}" alt="{legende}, dessiné par {auteur}">'
            f'<figcaption>{legende}</figcaption></figure>')


def passage_contexte():
    return (
        '<div class="contexte"><span class="lien-retour">[[Couverture->Page de garde]]</span>\n'
        # Les dessins d'Aylan et d'Adam sur leurs fiches, détourés
        '<div class="dessins">'
        + dessin("aylan.png", "Aylan", "Aylan") + dessin("coupe.png", "La coupe du monde", "Aylan", "large")
        + dessin("adam.png", "Adam", "Adam") + dessin("but.png", "Le but", "Aylan")
        + '</div>'
        f'<h1>Comment est née cette histoire</h1>{SEPARATEUR}'
        '<div class="contexte-texte">'
        + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Aylan, sur sa fiche récit</span></div>'
        + CONTEXTE[4]
        + '</div><div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span>'
        '<div class="miniatures">'
        + miniature("fiche_recit_adam.jpg", "Le récit d’Adam", "la fiche récit d’Adam")
        + miniature("fiche_personnage_aylan.jpg", "Une fiche personnage", "la fiche personnage d’Aylan")
        + miniature("fiche_situation_adam.jpg", "Une fiche à embranchement", "la fiche situation d’Adam, avec ses choix au dé")
        + '</div></div>'
        + '<span class="credits">Une histoire librement inspirée du récit d’Aylan et d’Adam.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        + f'<span class="avertissement">{AVERTISSEMENT}</span>'
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div>\n</div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = re.sub(r"<title>[^<]*</title>", f"<title>{TITRE}</title>", debut)
    lire = re.compile(r"JavaScript (?:needs to be enabled to play|doit être activé pour lire) [^<.]*\.")
    debut = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", debut)
    moteur = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", moteur)

    passages = [
        ("Bouton couverture", "header",
         '(unless: (a: "Page de garde", "Comment est née cette histoire", "L’arbre de l’histoire") contains (passage:)\'s name)'
         '[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L’arbre de l’histoire", "", passage_arbre()),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch)))

    # Espaces insécables de la typographie française
    insecables = [("« ", "«\u00a0"), (" »", "\u00a0»"), (" :", "\u00a0:"), (" ?", "\u202f?"),
                  (" !", "\u202f!"), (" ;", "\u202f;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        if tags != "header":
            contenu = contenu.replace("'", "’")  # apostrophe typographique
            for avant, apres in insecables:
                contenu = contenu.replace(avant, apres)
            passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
