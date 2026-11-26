"""Cigarette en art ASCII (style "$SIi:." ombré) qui se consume, en couleurs.

Usage : python cigarette.py [vitesse]
  vitesse : multiplicateur (défaut 1.0)

Agrandis la fenêtre AVANT de lancer : le dessin s'adapte à la taille du terminal
(idéal : 120 x 35 ou plus, Windows Terminal pour les couleurs 24 bits).
Ctrl+C pour arrêter.
"""
import math
import os
import random
import shutil
import sys
import time

os.system("")  # active les séquences ANSI sous Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ------------------------------------------------------------------ réglages
VITESSE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
IMAGE = 0.05                 # secondes par image
BRULE = 0.035                # unités de tabac brûlées par image

RAMPE = " .'`,:;~-!i?7jIJSd$"       # du plus clair au plus dense
RAMPE_FUMEE = " .`',:;~-!i?7j"

cols, lines = shutil.get_terminal_size((100, 30))
W = max(70, min(cols, 200))
H = max(22, min(lines - 1, 70))

# géométrie (unités : 1 colonne en x, 1/2 ligne en y, pour compenser la forme des cases)
L_TOT = W * 0.80
ANGLE = min(0.45, math.asin(min(0.9, (0.44 * 2 * H) / L_TOT)))
UX, UY = math.cos(ANGLE), -math.sin(ANGLE)        # axe de la cigarette
NX, NY = math.sin(ANGLE), math.cos(ANGLE)         # perpendiculaire (vers le bas)
R = min(H * 2 * 0.14, L_TOT * 0.075)              # rayon
AX = (W - L_TOT * UX) / 2 - 1
AY = 2 * H * 0.86
FILTRE = L_TOT * 0.26
BAGUE = max(1.2, R * 0.22)
FIN_MIN = FILTRE + BAGUE + 2.0                    # la braise s'arrête là

# lumière (vient d'en haut à gauche, un peu de face)
LX, LY, LZ = -0.35, -0.75, 0.55
N_L = NX * LX + NY * LY


# ------------------------------------------------------------------ bruit
def _h(x, y):
    h = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


def bruit(x, y):
    xi, yi = math.floor(x), math.floor(y)
    fx, fy = x - xi, y - yi
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _h(xi, yi), _h(xi + 1, yi)
    c, d = _h(xi, yi + 1), _h(xi + 1, yi + 1)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def melange(c1, c2, k):
    return (c1[0] + (c2[0] - c1[0]) * k, c1[1] + (c2[1] - c1[1]) * k, c1[2] + (c2[2] - c1[2]) * k)


def teinte(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


def car(rampe, i):
    return rampe[int(clamp(i) * (len(rampe) - 1))]


BRAISE = [(40, 0, 0), (120, 8, 0), (200, 30, 0), (255, 85, 0), (255, 160, 30), (255, 225, 120), (255, 250, 220)]


def couleur_braise(h):
    h = clamp(h) * (len(BRAISE) - 1)
    i = min(int(h), len(BRAISE) - 2)
    return melange(BRAISE[i], BRAISE[i + 1], h - i)


# ------------------------------------------------------------------ état
class Etat:
    def __init__(self):
        self.t = 0
        self.brule = L_TOT - 2.0          # position du front de combustion le long de l'axe
        self.cendre = 0.0                 # longueur de cendre au-delà de la braise
        self.cendre_max = random.uniform(8, 14)
        self.graine = random.random() * 100
        self.chaleur = 1.0
        self.fumee = []                   # [x, y, vx, vy, age, vie, phase]
        self.chutes = []                  # [x, y, vx, vy, ch, rgb]
        self.etincelles = []              # [x, y, vx, vy, age, vie]
        self.cellules_cendre = []
        self.fini_depuis = 0
        self.eteinte = 0                  # images depuis l'extinction

    def point(self, t, d):
        return AX + UX * t + NX * d, AY + UY * t + NY * d


# ------------------------------------------------------------------ physique
def etape(e):
    e.t += 1
    T = e.t
    if e.brule > FIN_MIN:
        v = BRULE * VITESSE
        e.brule -= v
        e.cendre += v * 0.95
        if e.cendre > e.cendre_max:
            casse(e)
        elif random.random() < 0.04 and e.cendre > 2:
            x, y = e.point(e.brule + 4.6 + e.cendre, random.uniform(-R, R) * 0.8)
            e.chutes.append([x, y, random.uniform(-0.1, 0.2), 0, ".", (150, 150, 150)])
    else:
        e.chaleur = max(0.0, e.chaleur - 0.02)
        if e.chaleur == 0:
            e.eteinte += 1
            if e.cendre > 0:
                casse(e, tout=True)

    # fumée qui monte du dessus de la braise
    n = (2 + (random.random() < 0.6)) * e.chaleur + (0.5 if e.chaleur == 0 and T % 4 == 0 and e.eteinte < 80 else 0)
    for _ in range(int(n + random.random())):
        x, y = e.point(e.brule + random.uniform(1.0, 4.5), -R * random.uniform(0.6, 1.0))
        e.fumee.append([x, y, random.uniform(-0.1, 0.15), -random.uniform(0.35, 0.6),
                        0, random.randint(70, 110), random.uniform(0, 6.28)])
    # étincelles
    if e.chaleur > 0.3 and random.random() < 0.05:
        x, y = e.point(e.brule + random.uniform(1.5, 4.5), random.uniform(-R, R) * 0.9)
        e.etincelles.append([x, y, random.uniform(0.1, 0.8), random.uniform(-1.2, -0.3), 0, random.randint(8, 16)])

    vent = 0.10 * math.sin(T * 0.013) + 0.05
    for p in e.fumee:
        a = p[4] / p[5]
        tourb = 0.35 * math.sin(p[1] * 0.08 + p[6] + T * 0.04) * min(1.0, p[4] / 12)
        p[2] += (vent + tourb - p[2]) * 0.08 + random.uniform(-0.04, 0.04) * a
        p[0] += p[2]
        p[1] += p[3]
        p[3] *= 0.996
        p[4] += 1
    e.fumee = [p for p in e.fumee if p[4] < p[5] and p[1] > -6]

    for s in e.etincelles:
        s[0] += s[2]
        s[1] += s[3]
        s[3] += 0.09
        s[4] += 1
    e.etincelles = [s for s in e.etincelles if s[4] < s[5]]

    for c in e.chutes:
        c[3] += 0.12
        c[0] += c[2]
        c[1] += c[3]
        if random.random() < 0.08:
            c[4] = random.choice(".:;'`,")
            c[5] = teinte(c[5], 0.95)
    e.chutes = [c for c in e.chutes if c[1] < 2 * H + 2]

    if e.eteinte >= 80 and not e.fumee and not e.chutes:
        e.fini_depuis += 1


def casse(e, tout=False):
    coupe = -1e9 if tout else e.brule + 4.6 + 1.0
    for (x, y, ch, rgb, t) in e.cellules_cendre:
        if t > coupe:
            e.chutes.append([x, y, random.uniform(-0.15, 0.25) + 0.02 * (t - coupe),
                             random.uniform(-0.1, 0.15), ch, rgb])
    e.cendre = 0.0 if tout else 1.0
    e.cendre_max = random.uniform(8, 14)
    e.graine = random.random() * 100


# ------------------------------------------------------------------ rendu
def ombre(s):
    nz = math.sqrt(max(0.0, 1 - s * s))
    return max(0.0, s * N_L + nz * LZ)


def pixel_cigarette(e, t, d, T):
    """Renvoie (caractère, rgb, est_cendre) ou None si la case est vide."""
    s = d / R
    as_ = abs(s)
    if t < -0.5 or as_ > 1.6:
        return None
    s2 = s * s
    b = e.brule
    front = b + 0.8 * s2 - 0.4 + 0.35 * (bruit(s * 3 + 7, T * 0.05) - 0.5)
    fin_carbone = front + 0.8
    fin_braise = b + 2.4 + 2.2 * (1 - min(1.0, s2))
    fin_braise_c = b + 4.6

    if as_ <= 1 and t >= 0 and t < fin_braise:
        dif = ombre(s)
        spec = 0.35 * math.exp(-((s + 0.5) / 0.15) ** 2)
        I = 0.38 + 0.62 * dif + spec
        if as_ > 0.93:
            I *= 0.7
        if t < front:
            if t < 0.8:                                  # tranche du filtre
                n = bruit(t * 6, s * 9)
                rgb = (240, 232, 205)
                I = (0.25 + 0.75 * dif) * (0.75 + 0.35 * n)
            elif t < FILTRE:                             # liège
                n = bruit(t * 1.8, s * 5)
                rgb = (205, 135, 62)
                if bruit(t * 4.3 + 11, s * 9) > 0.68:
                    rgb = (130, 72, 28)
                I = I * (0.78 + 0.35 * n)
            elif t < FILTRE + BAGUE:                     # bague dorée
                rgb = (228, 182, 70)
                I = 0.15 + 0.85 * dif + 0.6 * math.exp(-((s + 0.45) / 0.12) ** 2)
                u = (t - FILTRE) / BAGUE
                if 0.28 < u < 0.36 or 0.64 < u < 0.72:
                    I *= 0.55
            else:                                        # papier
                rgb = (238, 233, 222)
                I *= 0.96 + 0.08 * bruit(t * 2, s * 6)
                if abs(s - 0.35) < 0.06:
                    I *= 0.88
                if FILTRE + BAGUE + 0.8 < t < FILTRE + BAGUE + 1.2:
                    rgb = (215, 170, 70)
                k = math.exp(-(front - t) * 1.1) * 0.85  # papier roussi près du feu
                rgb = melange(rgb, (150, 95, 40), k)
            c = teinte(rgb, clamp(0.18 + 0.9 * I, 0, 1.15))
            return car(RAMPE, 0.42 + 0.58 * I), c, False
        if t < fin_carbone:                              # papier carbonisé
            rgb = (70, 42, 25)
            if t > fin_carbone - 0.35 and e.chaleur > 0:
                rgb = melange(rgb, (180, 50, 0), 0.6 * e.chaleur)
            return car(RAMPE, 0.55 + 0.3 * dif), teinte(rgb, 0.5 + 0.6 * dif), False
        # braise
        if e.chaleur <= 0:
            return car(RAMPE, 0.3 + 0.4 * dif), teinte((60, 50, 45), 0.5 + 0.6 * dif), False
        n = bruit(t * 1.1 + T * 0.15, s * 2.5 - T * 0.1)
        h = 0.3 + 0.45 * n + 0.22 * (1 - s2) * (t - fin_carbone) / max(0.5, fin_braise - fin_carbone)
        if bruit(t * 2 + 3, s * 6 + T * 0.02) > 0.8:   # pellicule de cendre
            g = 100 + 60 * dif
            return car(RAMPE, 0.35 + 0.3 * dif), (g, g * 0.95, g * 0.9), False
        h *= e.chaleur
        return car(RAMPE, 0.55 + 0.45 * h), couleur_braise(h), False

    # cendre (un peu plus fine, bout arrondi et irrégulier)
    if e.cendre <= 0:
        return None
    fin_cendre = fin_braise_c + e.cendre
    if t < fin_braise_c - 1.5 or t > fin_cendre + 1:
        return None
    rel = (t - fin_braise_c) / max(1.0, e.cendre)
    ra = R * (0.95 - 0.06 * clamp(rel)) + 0.6 * (bruit(t * 0.7 + e.graine, 1 if s > 0 else 2) - 0.5)
    sa = d / ra
    if abs(sa) > 1:
        return None
    bout = fin_cendre - 1.2 * sa * sa + 0.9 * (bruit(sa * 4, e.graine) - 0.5)
    if t > bout or t < fin_braise:
        return None
    dif = ombre(sa)
    I = 0.4 + 0.6 * dif
    I *= 0.82 + 0.18 * math.sin(t * 2.6 + 3 * bruit(t * 0.5, sa * 2))
    if bruit(t * 1.7, sa * 5 + e.graine) > 0.76:
        I *= 0.45
    if abs(sa) > 0.92:
        I *= 0.6
    rgb = (178, 176, 172)
    k = math.exp(-(t - fin_braise) * 1.4) * e.chaleur * 0.6
    if k > 0.05 and bruit(t * 3 + T * 0.2, sa * 4) > 0.45:
        rgb = melange(rgb, (220, 70, 10), k)
    return car(RAMPE, 0.35 + 0.6 * I), teinte(rgb, 0.3 + 0.8 * I), True


def image(e):
    T = e.t

    # densité de fumée
    dens = [[0.0] * W for _ in range(H)]
    for p in e.fumee:
        a = p[4] / p[5]
        r = 0.7 + p[4] * 0.045
        w = 0.5 * (1 - a) ** 1.3
        rr = r * r
        x0, x1 = int(p[0] - r), int(p[0] + r) + 1
        y0, y1 = int((p[1] - r) / 2), int((p[1] + r) / 2) + 1
        for j in range(max(0, y0), min(H, y1 + 1)):
            dy = (j + 0.5) * 2 - p[1]
            ligne = dens[j]
            for i in range(max(0, x0), min(W, x1 + 1)):
                dx = i + 0.5 - p[0]
                q = (dx * dx + dy * dy) / rr
                if q < 1:
                    ligne[i] += w * (1 - q)

    ex, ey = e.point(e.brule + 3.0, 0)
    glow_k = e.chaleur * 0.55
    gr2 = (R * 1.1) ** 2

    cellules_cendre = []
    out = ["\033[H"]
    for j in range(H):
        y = (j + 0.5) * 2
        cur = None
        for i in range(W):
            x = i + 0.5
            dx, dy = x - AX, y - AY
            t = dx * UX + dy * UY
            d = dx * NX + dy * NY
            px = pixel_cigarette(e, t, d, T)
            if px:
                ch, rgb, cendre = px
                if cendre:
                    cellules_cendre.append((x, y, ch, rgb, t))
            else:
                g = glow_k * math.exp(-((x - ex) ** 2 + (y - ey) ** 2) / gr2)
                dn = min(1.0, dens[j][i] * 0.9)
                if dn > 0.03:
                    v = 70 + 170 * dn
                    rgb = (v - 6 + 200 * g, v - 3 + 70 * g, v + 8)
                    ch = car(RAMPE_FUMEE, dn)
                elif g > 0.3:
                    rgb = (220 * g, 60 * g, 0)
                    ch = "." if g < 0.6 else ":"
                else:
                    ch, rgb = " ", None
            if ch == " ":
                out.append(" ")
                continue
            q = (int(clamp(rgb[0], 0, 255)) & 0xF8, int(clamp(rgb[1], 0, 255)) & 0xF8,
                 int(clamp(rgb[2], 0, 255)) & 0xF8)
            if q != cur:
                out.append("\033[38;2;%d;%d;%dm" % q)
                cur = q
            out.append(ch)
        out.append("\033[0m")
        if j < H - 1:
            out.append("\n")
    e.cellules_cendre = cellules_cendre

    # particules par-dessus
    extra = []
    for c in e.chutes:
        extra.append((c[0], c[1], c[4], c[5]))
    for s in e.etincelles:
        a = s[4] / s[5]
        extra.append((s[0], s[1], "*" if a < 0.3 else ("'" if a < 0.6 else "."),
                      couleur_braise(1 - a)))
    for (x, y, ch, rgb) in extra:
        i, j = int(x), int(y / 2)
        if 0 <= i < W and 0 <= j < H:
            q = tuple(int(clamp(v, 0, 255)) for v in rgb)
            out.append("\033[%d;%dH\033[38;2;%d;%d;%dm%s\033[0m" % (j + 1, i + 1, q[0], q[1], q[2], ch))
    return "".join(out)


# ------------------------------------------------------------------ boucle
def main():
    print("\033[?25l\033[2J", end="")
    e = Etat()
    try:
        while e.fini_depuis < 20:
            debut = time.time()
            etape(e)
            sys.stdout.write(image(e))
            sys.stdout.flush()
            time.sleep(max(0.0, IMAGE - (time.time() - debut)))
        print("\033[%d;1H\n  Cigarette terminée." % H)
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[0m\033[?25h")


if __name__ == "__main__":
    main()
