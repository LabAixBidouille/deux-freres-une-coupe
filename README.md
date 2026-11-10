# Deux frères, une coupe

Une histoire dont le lecteur est le héros, librement inspirée du récit imaginé par Aylan et Adam pendant l'atelier « La quête du curry, une histoire dont tu es le héros » du L.A.B, à la bibliothèque Li Campaneto (bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.

Fiction librement inspirée du monde du football : les clubs et les compétitions cités existent, mais les personnages, les situations et les paroles sont imaginaires. Ce livre n'est ni approuvé ni soutenu par ces clubs, leurs fédérations ou les organisateurs de ces compétitions.

## Modifier le livre

Le texte se trouve dans `source/texte.md`, recopié de la page Notion de référence. Chaque partie commence par `## Chapitre n. Titre` (ou `## Prologue. Titre`). Les renvois s'écrivent comme dans Notion (« Découvre la suite au chapitre n. », « 1 ou 2 : découvre la suite au chapitre n. », « Si …, découvre leur histoire au chapitre n. ») et s'affichent tous « Poursuis au chapitre n » sur le site. Une fin se termine par `FIN`.

Les illustrations vont dans `images/chapitres/` (`prologue.jpg`, `chapitre-01.jpg`…). Le ballon (`images/ballon.png`) sert de dé.

```
python3 source/construire_arbre.py
python3 source/construire_site.py
```

Réalisation du livre : Laboratoire d'Aix-périmentation et de Bidouille.
