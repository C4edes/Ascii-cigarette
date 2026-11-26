# Ascii-cigarette
🚬 Une cigarette en art ASCII qui se consume dans le terminal : ombrage 3D, braise qui scintille, cendre qui tombe et fumée animée, en couleurs 24 bits. Python pur, sans dépendance.

# 🚬 cigarette.py

Une cigarette en art ASCII qui se consume en temps réel dans ton terminal.

Le rendu utilise le style ASCII classique, où la densité des caractères fait l'ombre
(`$ d S J I j 7 ? i ! ~ ; : , .`), avec des couleurs 24 bits par-dessus.

## Ce que tu verras

- Une cigarette inclinée, ombrée en 3D et éclairée d'en haut à gauche, avec un reflet
- Un filtre en liège tacheté, une bague dorée et du papier qui roussit près du feu
- Une braise en cône, du rouge au jaune, qui scintille et éclaire autour d'elle
- Une cendre striée qui s'allonge, se fissure puis tombe en morceaux
- De la fumée en volutes, portée par un vent qui change
- Quelques étincelles, et une dernière fumée quand la cigarette s'éteint

## Lancer

Il faut Python 3.7 ou plus récent. Aucune bibliothèque à installer.

```bash
python cigarette.py        # vitesse normale
python cigarette.py 3      # 3x plus vite
```

`Ctrl+C` pour arrêter.

## Conseils

- **Agrandis la fenêtre avant de lancer** : le dessin s'adapte à la taille du terminal,
  donc plus la fenêtre est grande, plus il y a de détails (idéal : 120×35 ou plus).
- Il faut un terminal qui gère les couleurs 24 bits : Windows Terminal, iTerm2, la
  plupart des terminaux Linux, ou celui de VS Code.

## Comment ça marche

Chaque case du terminal est projetée sur l'axe de la cigarette, qui est vue comme un cylindre.
La normale à la surface donne l'éclairage. Cette lumière choisit à la fois le caractère
(plus ou moins dense) et sa couleur. Du bruit procédural ajoute les textures (liège,
craquelures de la cendre, scintillement de la braise). La fumée est un nuage de
particules qu'on étale sur une grille de densité.
