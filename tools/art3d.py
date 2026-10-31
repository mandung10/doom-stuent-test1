"""CLASS BUSTER — 3D-primitive sprite models: school-subject monsters, the student player,
non-gore replacements for corpses/decorations.  Every original sprite lump name is kept,
so the Doom engine's state tables (info.c) work unchanged.  (GPLv2)"""
import math
import warnings
import numpy as np
from sprites3d import ell, box, cap, rot_x, rot_y, rot_z, transform, render, crop, P
from wadlib import picture_from_rgba

warnings.filterwarnings('ignore')
D = math.radians


def basis_to(n):
    n = np.asarray(n, float); n = n / np.linalg.norm(n)
    t = np.array([0, 1, 0.]) if abs(n[1]) < 0.9 else np.array([1, 0, 0.])
    u = np.cross(t, n); u /= np.linalg.norm(u); v = np.cross(n, u)
    return np.stack([u, v, n], 1)


def on_sphere(c, r, d, rad, color, emit=0.0, flat=2.5):
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    return ell(tuple(np.asarray(c) + d * (r - flat * 0.4)), (rad, rad * 0.75, flat), color, R=basis_to(d), emit=emit)


def leg(x, hip_y, L, r, a_deg, color, shoe, sr=None):
    a = D(a_deg)
    f = (x, hip_y - L * math.cos(a), L * math.sin(a))
    sr = sr or (r * 1.15, r * 0.85, r * 1.7)
    return [cap((x, hip_y, 0), f, r, color), ell((f[0], f[1] + sr[1] * 0.2, f[2] + sr[2] * 0.35), sr, shoe)]


def arm(x, sh_y, L, r, color, mode='swing', a=0.0, hand=None, hr=None):
    if mode == 'swing':
        A = D(a); h = (x * 1.08, sh_y - L * math.cos(A), -L * math.sin(A))
    elif mode == 'aim':
        h = (x * 0.4, sh_y - L * 0.22, L * 0.95)
    elif mode == 'up':
        h = (x * 1.15, sh_y + L * 0.85, -L * 0.2)
    elif mode == 'throw':
        h = (x * 0.9, sh_y + L * 0.25, L * 0.92)
    elif mode == 'out':
        h = (x * 1.7, sh_y + L * 0.2, L * 0.3)
    else:
        h = (x * 1.05, sh_y - L, 0)
    out = [cap((x, sh_y, 0), h, r, color)]
    if hand:
        out.append(ell(h, hr or r * 1.35, hand))
    return out, h


def flash(at, s=4.0, col='#fff2a0'):
    return [ell(at, (s, s, s * 0.8), col, emit=1.0), ell(at, (s * 1.6, s * 1.6, s * 0.5), '#ffb030', emit=1.0)]


def walkang(p, amp=28):
    return amp * math.sin(p['walk']) if p.get('walk') is not None else 0.0


def armmode(p, default='swing'):
    if p.get('pain'):
        return 'out'
    if p.get('atk') is not None:
        return 'aim'
    return default


# ======================================================================== monsters
def m_poss(p):  # 수학 계산기 로봇
    a = walkang(p); o = []
    o += leg(-5, 22, 18, 3, a, '#565c68', '#22242a'); o += leg(5, 22, 18, 3, -a, '#565c68', '#22242a')
    o += [box((0, 35, 0), (10, 13, 5), '#333844', tex=0.05),
          box((0, 41.5, 5.1), (7.5, 4, 0.6), '#b4dc96', emit=0.55),
          box((-2, 41.5, 5.6), (4, 1, 0.3), '#2a4020', emit=0.6)]
    for r in range(3):
        for c in range(3):
            o.append(box((-5 + 5 * c, 33.5 - 4.4 * r, 5.3), (1.6, 1.3, 0.6), '#ff7a20' if (r, c) == (2, 2) else '#e4e4e4'))
    o += [box((0, 52, 0), (6, 4, 4), '#454b58'),
          ell((-2.6, 52.5, 4.1), (1.5, 1.5, 0.8), '#40ffff', emit=0.95), ell((2.6, 52.5, 4.1), (1.5, 1.5, 0.8), '#40ffff', emit=0.95),
          cap((0, 56, 0), (0, 61, 0), 0.8, '#9a9a9a'), ell((0, 62, 0), 1.6, '#ff3030', emit=0.8)]
    md = armmode(p)
    al, hl = arm(12, 44, 15, 2.6, '#565c68', 'aim' if md == 'aim' else md, -a, '#22242a')
    ar, hr = arm(-12, 44, 15, 2.6, '#565c68', md, a, '#22242a')
    o += al + ar
    if md == 'aim':
        o.append(box((hr[0] + 1, hr[1] + 1.5, hr[2] + 7), (1.6, 2.4, 10), '#e8c840'))
        o += [box((hr[0] + 2.7, hr[1] + 2.5, hr[2] + 7 + k * 3 - 7.5), (0.3, 1.2, 0.35), '#3a3020') for k in range(6)]
        if p.get('flash'):
            o += flash((hr[0] + 1, hr[1] + 1.5, hr[2] + 20))
    else:
        o.append(box((hr[0], hr[1] - 4, hr[2]), (1.6, 9, 2.2), '#e8c840'))
    return o


def m_spos(p):  # 영어 사전 병사
    a = walkang(p); o = []
    o += leg(-5, 22, 18, 3.2, a, '#26304a', '#111'); o += leg(5, 22, 18, 3.2, -a, '#26304a', '#111')
    o += [box((0, 34, 0), (10, 12, 6), '#a62828', tex=0.05), box((0, 34, 0), (10.7, 11, 5.2), '#f4efe0', tex=0.02),
          box((0, 38, 6.2), (6, 1.6, 0.5), '#f0c840', emit=0.3), box((0, 33, 6.2), (4, 1.0, 0.5), '#f0c840', emit=0.3),
          ell((0, 51, 0), (6, 6.5, 6), '#f0c8a0'), ell((0, 55.5, -0.5), (6.5, 3.6, 6.6), '#1f2c62'),
          box((0, 54.5, 5.2), (6.5, 0.8, 2.6), '#1f2c62'),
          ell((-2.7, 51.5, 5.4), (2.2, 2.0, 0.8), '#1a1a1a'), ell((2.7, 51.5, 5.4), (2.2, 2.0, 0.8), '#1a1a1a'),
          ell((-2.7, 51.5, 5.9), (1.3, 1.1, 0.6), '#cfe8ff', emit=0.3), ell((2.7, 51.5, 5.9), (1.3, 1.1, 0.6), '#cfe8ff', emit=0.3),
          box((0, 47.5, 5.6), (1.8, 0.5, 0.5), '#802020')]
    md = armmode(p)
    al, hl = arm(12, 42, 15, 2.8, '#a62828', md, -a, '#f0c8a0')
    ar, hr = arm(-12, 42, 15, 2.8, '#a62828', md, a, '#f0c8a0')
    o += al + ar
    if md == 'aim':
        for dx in (-1.6, 1.6):
            b = (hr[0] + 3 + dx, hr[1] + 1.5, hr[2] - 3)
            o += [cap(b, (b[0], b[1], b[2] + 16), 1.4, '#f0c020'), ell((b[0], b[1], b[2] + 18), (1.3, 1.3, 2.2), '#f2d2a6'),
                  ell((b[0], b[1], b[2] + 20), (0.6, 0.6, 0.9), '#2a2a2a'), cap((b[0], b[1], b[2] - 1), (b[0], b[1], b[2] - 3), 1.45, '#f08aa0')]
        if p.get('flash'):
            o += flash((hr[0] + 3, hr[1] + 1.5, hr[2] + 22), 5)
    return o


def m_troo(p):  # 과학 플라스크 괴물
    a = walkang(p, 22); o = []
    o += leg(-6, 10, 6, 3, a, '#38a040', '#245a24'); o += leg(6, 10, 6, 3, -a, '#38a040', '#245a24')
    atk = p.get('atk'); m = 0.15 if atk is None else 0.6
    if p.get('pain'): m = 0.9
    o += [ell((0, 21, 0), (14, 13, 12), '#3cc83c', emit=0.25, tex=0.04),
          ell((0, 31, 0), (10.5, 8, 9.5), '#bde8f0', tex=0.01), cap((0, 34, 0), (0, 46, 0), 4.5, '#bde8f0', tex=0.01),
          ell((0, 46.5, 0), (5.5, 1.6, 5.5), '#d8f4ff'), box((0, 49, 0), (3.8, 3, 3.8), '#9a6a3a', tex=0.12),
          ell((-4, 28, 9), 1.4, '#f0fff0', emit=0.5), ell((3, 30.5, 8.6), 1.0, '#f0fff0', emit=0.5),
          ell((-5, 22, 11.2), (3.6, 4.2, 2), '#ffffff'), ell((5, 22, 11.2), (3.6, 4.2, 2), '#ffffff'),
          ell((-4.6, 21.4, 12.9), (1.7, 2.1, 1), '#101010'), ell((4.6, 21.4, 12.9), (1.7, 2.1, 1), '#101010'),
          box((-5, 27.2, 11.6), (3.6, 0.8, 0.8), '#145014', R=rot_z(D(-18))), box((5, 27.2, 11.6), (3.6, 0.8, 0.8), '#145014', R=rot_z(D(18))),
          ell((0, 13.5, 11.2), (5, 1.4 + 3.2 * m, 1.6), '#0e300e')]
    if atk is None:
        md = 'out' if p.get('pain') else 'swing'
        al, hl = arm(13, 26, 12, 2.2, '#bde8f0', md, -a, '#3cc83c', 3.2)
        ar, hr = arm(-13, 26, 12, 2.2, '#bde8f0', md, a, '#3cc83c', 3.2)
        o += al + ar
    else:
        mode = ['up', 'up', 'throw'][min(atk, 2)]
        al, hl = arm(13, 26, 12, 2.2, '#bde8f0', 'swing', 0, '#3cc83c', 3.2)
        ar, hr = arm(-13, 26, 12, 2.2, '#bde8f0', mode, 0, '#3cc83c', 3.2)
        o += al + ar
        if atk < 2:
            o += [ell((hr[0], hr[1] + 4, hr[2]), 3.8 + atk, '#a8ff50', emit=1.0), ell((hr[0], hr[1] + 4, hr[2]), 5.5 + atk, '#40e040', emit=0.8)]
    return o


def m_sarg(p):  # 체육 농구공 괴물
    a = walkang(p, 30); o = []
    o += leg(-9, 12, 8, 3.2, a, '#f4f4f4', '#d82020', (4.5, 3, 6.5)); o += leg(9, 12, 8, 3.2, -a, '#f4f4f4', '#d82020', (4.5, 3, 6.5))
    atk = p.get('atk')
    m = [0.35, 1.0, 0.55][atk] if atk is not None else 0.12
    if p.get('pain'): m = 0.8
    body = [ell((0, 32, 0), 21, '#e0681a', tex=0.12),
            ell((0, 32, 0), (0.8, 21.5, 21.5), '#1a1210'), ell((0, 32, 0), (21.5, 0.8, 21.5), '#1a1210'),
            ell((0, 32, 0), (21.4, 21.4, 21.4), '#1a1210', R=rot_y(D(45)) @ np.diag([1, 1, 1])) if False else None]
    o += [b for b in body if b is not None]
    o += [ell((-7.5, 39, 18.2), (4.2, 4.6, 2.6), '#ffffff'), ell((7.5, 39, 18.2), (4.2, 4.6, 2.6), '#ffffff'),
          ell((-7, 38.4, 20.3), (1.9, 2.3, 1), '#111'), ell((7, 38.4, 20.3), (1.9, 2.3, 1), '#111'),
          box((-7.5, 45, 18.8), (4.5, 0.9, 1), '#3a1a08', R=rot_z(D(-20))), box((7.5, 45, 18.8), (4.5, 0.9, 1), '#3a1a08', R=rot_z(D(20)))]
    mh = 1.6 + 6.5 * m
    o += [ell((0, 25, 18.0), (11, mh, 4.2), '#2a0606')]
    for k in range(-2, 3):
        o.append(box((k * 3.8, 25 + mh * 0.72, 21.0), (1.4, 1.3, 0.9), '#ffffff'))
        o.append(box((k * 3.8, 25 - mh * 0.72, 21.0), (1.4, 1.3, 0.9), '#ffffff'))
    o += [cap((19, 32, 0), (25, 22 + 6 * m, 6 + 4 * m), 2.6, '#e0681a'), ell((25, 22 + 6 * m, 6 + 4 * m), 3.4, '#ffffff'),
          cap((-19, 32, 0), (-25, 22 + 6 * m, 6 + 4 * m), 2.6, '#e0681a'), ell((-25, 22 + 6 * m, 6 + 4 * m), 3.4, '#ffffff')]
    if atk is not None:
        o = transform(o, rot_x(D(10 * m)))
    return o


def m_skul(p):  # 음악 음표 (날아다님)
    o = []
    hot = p.get('atk') is not None
    o += [ell((0, 12, 0), (9, 6.5, 6), '#161616', R=rot_z(D(25)), tex=0.02),
          cap((7.5, 14, 0), (7.5, 40, 0), 1.7, '#161616'),
          box((11, 36, 0), (4.5, 2.2, 1.5), '#161616', R=rot_z(D(-35))), box((11, 30, 0), (4.5, 2.2, 1.5), '#161616', R=rot_z(D(-35))),
          ell((-3.5, 13, 5.2), (2.1, 2.4, 1), '#ffffff'), ell((2, 14.5, 5.2), (2.1, 2.4, 1), '#ffffff'),
          ell((-3.2, 12.6, 6.0), (0.9, 1.2, 0.6), '#ff2020' if hot else '#2050ff', emit=0.8),
          ell((2.3, 14.1, 6.0), (0.9, 1.2, 0.6), '#ff2020' if hot else '#2050ff', emit=0.8)]
    ph = (p.get('walk') or 0) + (p.get('atk') or 0) * 0.7
    for k in range(7):
        t = ph + k * 2 * math.pi / 7
        col = '#ff9a30' if hot else '#ffe860'
        o.append(ell((14 * math.cos(t), 18 + 12 * math.sin(t), 3 * math.sin(t * 2)), 1.6 if k % 2 else 2.2, col, emit=1.0))
    return o


def m_head(p):  # 지리 지구본 (외눈, 날아다님)
    c = (0, 32, 0); o = []
    atk = p.get('atk'); m = [0.2, 0.6, 1.0][atk] if atk is not None else 0.1
    o.append(ell(c, 27, '#2a64c8', tex=0.05))
    for d, s in [((-0.8, 0.5, 0.35), 9), ((0.85, 0.2, 0.4), 7), ((0.5, -0.6, 0.6), 6), ((-0.6, -0.4, 0.7), 5), ((0, 0.6, -0.8), 12),
                 ((0.9, 0.3, -0.4), 10), ((-0.9, 0, -0.4), 9), ((0.1, -0.7, -0.7), 8), ((0.3, 0.95, 0.1), 5), ((-0.3, 0.85, 0.55), 4)]:
        o.append(on_sphere(c, 27, d, s, '#3aa83a'))
    o += [cap((0, 58, 0), (-3, 64, 0), 1.6, '#c8a040'), ell((-3, 64, 0), 2.6, '#e0b850'),
          cap((0, 6, 0), (3, 1, 0), 1.6, '#c8a040'), ell((3, 1, 0), 2.6, '#e0b850')]
    if p.get('pain'):
        o += [ell((0, 35, 23.5), (10, 10, 5.4), '#2a64c8'), box((0, 35, 28.4), (8, 0.9, 0.6), '#0a1840')]
    else:
        iris = '#ff3020' if (atk is not None and atk == 2) else '#30a050'
        o += [ell((0, 35, 23.5), (9.5, 9.5, 5.4), '#fafafa'), ell((0, 35, 28.1), (4.6, 4.6, 1.6), iris, emit=0.8 if iris == '#ff3020' else 0),
              ell((0, 35, 29.3), (2.2, 2.2, 1), '#050505'), box((0, 45.5, 25), (9, 1.2, 1.2), '#0a1840', R=rot_z(D(5)))]
    mh = 1.6 + 6.5 * m
    o.append(ell((0, 17, 22), (11, mh, 4), '#2a0808'))
    for k in range(-2, 3):
        o.append(box((k * 3.8, 17 + mh * 0.7, 25.2), (1.4, 1.2, 0.8), '#ffffff'))
    if atk == 2:
        o += flash((0, 17, 30), 4, '#ff80ff')
    return o


def m_boss(p):  # 역사 돌하르방
    a = walkang(p, 18); o = []
    st, st2, dk = '#86837a', '#77746c', '#5b5852'
    o += leg(-7, 10, 7, 5, a, '#6e6b64', dk, (6, 3.5, 7)); o += leg(7, 10, 7, 5, -a, '#6e6b64', dk, (6, 3.5, 7))
    o += [ell((0, 31, 0), (16, 24, 13), st2, tex=0.2),
          ell((0, 57, 1), (11, 12, 10), st, tex=0.2), ell((0, 63.5, 0), (13.5, 1.6, 12.5), dk, tex=0.15),
          ell((0, 68, 0), (11.5, 6, 10.5), dk, tex=0.15), ell((0, 72, 0), (6.5, 4, 6.5), dk, tex=0.15)]
    atk = p.get('atk')
    eye = '#ff4020' if atk is not None else '#2a2a28'
    o += [ell((-4.6, 59, 8.6), (3.9, 3.5, 3), '#9a968c', tex=0.15), ell((4.6, 59, 8.6), (3.9, 3.5, 3), '#9a968c', tex=0.15),
          ell((-4.6, 59, 11.3), (1.6, 1.6, 0.8), eye, emit=0.9 if atk is not None else 0), ell((4.6, 59, 11.3), (1.6, 1.6, 0.8), eye, emit=0.9 if atk is not None else 0),
          ell((0, 53.5, 10.4), (3.4, 4.2, 3), '#8e8a80', tex=0.15), box((0, 48.6, 9.6), (4.2, 0.8, 1), '#3a3834')]
    if atk is None and not p.get('pain'):
        o += [cap((15, 42, 2), (6, 31, 12.5), 4, st2), ell((5.5, 31, 12.5), (5.2, 3.6, 3.6), st, tex=0.2),
              cap((-15, 42, 2), (-6, 25, 12.5), 4, st2), ell((-5.5, 25, 12.5), (5.2, 3.6, 3.6), st, tex=0.2)]
    else:
        o += [cap((15, 42, 2), (6, 31, 12.5), 4, st2), ell((5.5, 31, 12.5), (5.2, 3.6, 3.6), st, tex=0.2)]
        k = 0 if p.get('pain') else atk
        hp = [(-20, 66, -4), (-19, 60, 6), (-12, 46, 18)][min(k, 2)]
        o += [cap((-15, 42, 2), hp, 4, st2), ell(hp, 5, st, tex=0.2)]
        if atk is not None and atk < 2:
            o += [ell((hp[0], hp[1] + 6, hp[2]), 4.5, '#a8ff60', emit=1.0), ell((hp[0], hp[1] + 6, hp[2]), 6.5, '#30c830', emit=0.8)]
    return o


def m_cybr(p):  # 기말고사 시험지 거인
    a = walkang(p, 22); o = []
    o += leg(-10, 50, 43, 7, a, '#253250', '#121212', (8, 5, 11)); o += leg(10, 50, 43, 7, -a, '#253250', '#121212', (8, 5, 11))
    o += [box((0, 73, 0), (19, 24, 8), '#f4f2ea', tex=0.02), box((0, 49.5, 0), (18, 2, 8.5), '#3a2a1a')]
    for k in range(7):
        o.append(box((-4, 88 - k * 5.2, 8.25), (12 - (k % 3) * 2, 0.65, 0.35), '#3050a0'))
    o += [ell((11, 89, 8.4), (6.5, 6.5, 0.5), '#e02020'), ell((11, 89, 8.7), (5, 5, 0.5), '#f4f2ea'),
          box((10, 89, 9), (3.5, 0.7, 0.3), '#e02020', R=rot_z(D(40))),
          ell((0, 104, 0), (10.5, 10.5, 6.5), '#d02828'), ell((0, 104, 5.2), (8.3, 8.3, 2), '#fbfbf0'),
          box((0.6, 106.8, 7.1), (0.7, 3.3, 0.4), '#111'), box((2.6, 104, 7.1), (2.8, 0.7, 0.4), '#111'),
          ell((-7, 114.5, 0), (4.8, 3.8, 3.8), '#d0d0d0'), ell((7, 114.5, 0), (4.8, 3.8, 3.8), '#d0d0d0'),
          cap((-7, 114.5, 0), (7, 114.5, 0), 0.9, '#888'),
          ell((-3.5, 103.5, 7.4), (1.3, 1.6, 0.6), '#d02020', emit=0.7), ell((3.5, 103.5, 7.4), (1.3, 1.6, 0.6), '#d02020', emit=0.7)]
    md = armmode(p)
    al, hl = arm(23, 92, 26, 5, '#253250', md, -a, '#f4f2ea', 6)
    o += al
    gx, gy, gz = -24, 72, 2
    if md == 'aim':
        gy, gz = 76, 8
    elif md == 'out':
        gy, gz = 80, 0
    o += [cap((-23, 94, 0), (gx, gy + 4, gz - 2), 6, '#253250'),
          cap((gx, gy, gz - 6), (gx, gy, gz + 26), 5.2, '#f0c020', tex=0.03),
          cap((gx, gy, gz - 8), (gx, gy, gz - 6), 5.4, '#b8b8c0'), ell((gx, gy, gz - 10), (5, 5, 3), '#f08aa0'),
          ell((gx, gy, gz + 29), (4, 4, 5), '#f2d2a6'), ell((gx, gy, gz + 33), (1.5, 1.5, 2), '#333')]
    if p.get('flash'):
        o += flash((gx, gy, gz + 38), 6)
    return o


def m_spid(p):  # 모의고사 채점기 거미
    cl = p.get('collapse')
    if cl is not None:
        body = m_spid({})
        body = [q for q in body if not (q.kind == 'cap' and q.r in (4.8, 4))]
        body = [q for q in body if not (q.kind == 'ell' and np.allclose(q.r, 6.5))]
        body = [q for q in body if not (q.kind == 'ell' and np.allclose(q.r, (6, 3, 6)))]
        body = transform(body, rot_z(D(8 * cl)), (0, -40 * cl, 0))
        for i, (sx, sz) in enumerate([(1, 1), (-1, 1), (1, -1), (-1, -1)]):
            hip = (sx * 36, 58 - 40 * cl, sz * 22)
            knee = (sx * (72 + 18 * cl), 92 - 80 * cl, sz * 40)
            foot = (sx * (88 + 22 * cl), 2, sz * (48 + 8 * cl))
            body += [cap(hip, knee, 4.8, '#6a6a72'), ell(knee, 6.5, '#3a3a40'), cap(knee, foot, 4, '#6a6a72'), ell(foot, (6, 3, 6), '#2a2a30')]
        if cl > 0.3:
            for k in range(int(8 * cl)):
                body.append(ell((-30 + k * 9, 50 - 30 * cl + 25 * cl * math.sin(k * 1.7), 10 * math.cos(k)), 5 + 3 * cl, '#d8d8d8' if k % 2 else '#b0b0b0', tex=0.03))
        if cl >= 1:
            body += stars_at(0, 52, 4, 0.5)
        return body
    o = []
    ph = p.get('walk') or 0
    o += [box((0, 64, 0), (42, 20, 30), '#d8d0b8', tex=0.03), box((0, 84.6, 0), (32, 0.8, 6), '#333'),
          box((0, 88, -4), (25, 4, 0.8), '#ffffff'), box((0, 66, 30.3), (22, 9, 0.6), '#1e2630'),
          box((-9, 66, 30.9), (8, 4, 0.4), '#ff3030', emit=0.9), box((10, 68, 30.9), (6, 1, 0.4), '#50ff70', emit=0.8),
          box((10, 64, 30.9), (6, 1, 0.4), '#50ff70', emit=0.8),
          ell((-30, 74, 30), (5.5, 5.5, 2.2), '#80e0ff', emit=0.6), ell((30, 74, 30), (5.5, 5.5, 2.2), '#80e0ff', emit=0.6),
          box((0, 52, 24), (14, 4, 8), '#444')]
    for k in range(4):
        x = -6 + 4 * k
        o += [cap((x, 51, 30), (x, 51, 52), 1.9, '#d82020'), ell((x, 51, 53.5), (1.7, 1.7, 2.4), '#f2d2a6')]
    if p.get('flash'):
        o += flash((0, 51, 60), 7)
    for i, (sx, sz) in enumerate([(1, 1), (-1, 1), (1, -1), (-1, -1)]):
        lift = max(0.0, math.sin(ph + (0 if i in (0, 3) else math.pi))) if p.get('walk') is not None else 0
        hip = (sx * 36, 58, sz * 22)
        knee = (sx * 72, 92 + 6 * lift, sz * 40)
        foot = (sx * 88, 2 + 14 * lift, sz * 48 + 6 * lift)
        o += [cap(hip, knee, 4.8, '#6a6a72'), ell(knee, 6.5, '#3a3a40'), cap(knee, foot, 4, '#6a6a72'), ell(foot, (6, 3, 6), '#2a2a30')]
    return o


def m_play(p):  # 학생 (플레이어)
    a = walkang(p); o = []
    o += leg(-4.5, 23, 19, 3.2, a, '#5a5a62', '#141414'); o += leg(4.5, 23, 19, 3.2, -a, '#5a5a62', '#141414')
    o += [box((0, 35, 0), (9, 12, 5.5), '#1f2c62', tex=0.03), box((0, 44, 5.3), (3.5, 2.5, 0.5), '#ffffff'),
          box((0, 40, 5.7), (0.9, 4, 0.4), '#c02020'), box((0, 37, -7.5), (7, 9, 3), '#d06020'),
          ell((0, 51, 0), (5.6, 6.2, 5.6), '#f0c8a0'), ell((0, 54.5, -0.8), (6.0, 3.8, 6.0), '#1a1a1a'),
          ell((-2.2, 51.5, 5.0), (1.0, 1.2, 0.6), '#111'), ell((2.2, 51.5, 5.0), (1.0, 1.2, 0.6), '#111')]
    md = armmode(p)
    al, hl = arm(11, 44, 15, 2.8, '#1f2c62', md, -a, '#f0c8a0')
    ar, hr = arm(-11, 44, 15, 2.8, '#1f2c62', md, a, '#f0c8a0')
    o += al + ar
    if md == 'aim':
        o += [box((hr[0] + 2, hr[1] + 1.5, hr[2] + 5), (2, 2.6, 7), '#4a5060'), box((hr[0] + 2, hr[1] + 4, hr[2] + 4), (1, 1, 4), '#40ffff', emit=0.8)]
        if p.get('flash'):
            o += flash((hr[0] + 2, hr[1] + 1.5, hr[2] + 14))
    return o


def scaled(p, s, off):
    q = p.xform(np.eye(3), np.asarray(off, float))
    if q.kind == 'cap':
        mid = (q.a + q.b) / 2
        q.a = mid + (q.a - mid) * s; q.b = mid + (q.b - mid) * s; q.r = q.r * s
    else:
        q.r = q.r * s
    return q


def center_floor(prims, cx=True):
    lo = np.min([p.bound()[0] for p in prims], 0); hi = np.max([p.bound()[1] for p in prims], 0)
    return transform(prims, np.eye(3), (-(lo[0] + hi[0]) / 2 if cx else 0, -lo[1], -(lo[2] + hi[2]) / 2 if cx else 0)), hi - lo


def stars_at(x, y, n=3, ph=0.0):
    o = []
    for k in range(n):
        t = ph + k * 2 * math.pi / n
        o += [ell((x + 7 * math.cos(t), y + 1.5 * math.sin(t), 4 * math.sin(t)), (2.2, 2.2, 1.2), '#ffe040', emit=1.0),
              ell((x + 7 * math.cos(t), y + 1.5 * math.sin(t), 4 * math.sin(t) + 0.8), (0.9, 0.9, 0.6), '#ffffff', emit=1.0)]
    return o


def die(model, k, n, stars=True):
    """Fall sideways (fainted) — the last two frames lie on the floor with circling stars."""
    t = min(1.0, (k + 1) / max(1, n - 1))
    base = model({'pain': True} if k < n - 1 else {})
    P1 = transform(base, rot_z(D(88 * t)))
    P1, size = center_floor(P1)
    if t >= 1 and stars:
        lo = np.min([p.bound()[0] for p in P1], 0); hi = np.max([p.bound()[1] for p in P1], 0)
        P1 = P1 + stars_at(lo[0] + min(10, size[0] * 0.2), hi[1] + 5, 3, k * 0.9)
    elif k >= 1:
        lo = np.min([p.bound()[0] for p in P1], 0); hi = np.max([p.bound()[1] for p in P1], 0)
        P1 = P1 + stars_at(lo[0] + 8, hi[1] + 4, 2, k)
    return P1


PAPER = '#f6f4ea'
CONF = ['#ff4060', '#40c0ff', '#ffd040', '#60e060', '#c060ff']


def burst(model, k, n, seed, keep=None):
    """'Paper explosion': the monster pops into exam sheets and confetti, leaving a paper pile."""
    rng = np.random.default_rng(seed)
    t = (k + 1) / n
    base = model({})
    out = []
    dirs = rng.normal(size=(len(base), 3)); dirs[:, 1] = np.abs(dirs[:, 1]) + 0.3
    if t < 0.5:
        for p, d in zip(base, dirs):
            out.append(scaled(p, max(0.15, 1 - t * 1.7), d * t * 26))
    ns = int(10 + 14 * t)
    for i in range(ns):
        r = rng.random(5)
        if t < 0.75:
            pos = ((r[0] - 0.5) * 60 * t + (r[0] - 0.5) * 8, 30 + (r[1] - 0.3) * 50 * t - 30 * max(0, t - 0.4), (r[2] - 0.5) * 20)
        else:
            pos = ((r[0] - 0.5) * 30, 0.6 + (i % 6) * 0.9, (r[2] - 0.5) * 14)
        R = rot_y(D(r[3] * 360)) @ rot_x(D((r[4] - 0.5) * (120 if t < 0.75 else 14)))
        out.append(box(pos, (4.5, 0.35, 6), PAPER, R=R, tex=0.01))
        if i % 3 == 0:
            out.append(box((pos[0] + 1, pos[1] + 0.5, pos[2]), (2.5, 0.4, 0.4), '#7080b0', R=R))
    for i in range(int(14 * (1 - t * 0.6))):
        r = rng.random(4)
        pos = ((r[0] - 0.5) * 70 * t, 20 + 40 * t * r[1] - 25 * t * t, (r[2] - 0.5) * 30)
        out.append(box(pos, (1.2, 1.2, 0.4), CONF[i % 5], R=rot_z(D(r[3] * 180)), emit=0.5))
    if keep and t >= 0.75:
        out += keep
    if t >= 0.75:
        out += stars_at(0, 16, 3, k)
    return out


def popfx(model, k, n):
    """Lost-soul style: note shrinks, sparkles expand and fade (no remains)."""
    t = (k + 1) / n
    o = []
    if t < 0.6:
        o += [scaled(p, 1 - t * 1.2, (0, 0, 0)) for p in model({})]
    for i in range(10):
        a = i * 2 * math.pi / 10
        rr = 6 + 30 * t
        o.append(ell((rr * math.cos(a), 20 + rr * math.sin(a), 0), max(0.6, 2.4 * (1 - t)), CONF[i % 5] if i % 2 else '#ffe860', emit=1.0))
    return o


TAB = {
    'POSS': (m_poss, dict(walk='ABCD', atk='EF', flash='F', pain='G', die='HIJKL', xdie='MNOPQRSTU')),
    'SPOS': (m_spos, dict(walk='ABCD', atk='EF', flash='F', pain='G', die='HIJKL', xdie='MNOPQRSTU')),
    'TROO': (m_troo, dict(walk='ABCD', atk='EFG', pain='H', die='IJKLM', xdie='NOPQRSTU')),
    'SARG': (m_sarg, dict(walk='ABCD', atk='EFG', pain='H', die='IJKLMN')),
    'SKUL': (m_skul, dict(walk='AB', atk='CD', pain='E', pop='FGHIJK')),
    'HEAD': (m_head, dict(walk='A', atk='BCD', pain='EF', die='GHIJKL')),
    'BOSS': (m_boss, dict(walk='ABCD', atk='EFG', pain='H', die='IJKLMNO')),
    'CYBR': (m_cybr, dict(walk='ABCD', atk='EF', flash='F', pain='G', die='HIJKLMNOP')),
    'SPID': (m_spid, dict(walk='ABCDEF', atk='GH', flash='GH', pain='I', die='JKLMNOPQRS')),
    'PLAY': (m_play, dict(walk='ABCD', atk='EF', flash='F', pain='G', die='HIJKLMN', xdie='OPQRSTUVW')),
}


def play_leftovers():
    return [box((-6, 2.5, 3), (5, 2.5, 4), '#d06020'), ell((6, 1, 4), (2, 1.2, 0.6), '#1a1a1a'), ell((10, 1, 4), (2, 1.2, 0.6), '#1a1a1a'),
            cap((8, 1, 4), (8, 1, 4.2), 0.4, '#1a1a1a')]


def monster_prims(prefix, letter):
    model, tab = TAB[prefix]
    seed = sum(map(ord, prefix))
    for key in ('walk', 'atk', 'pain', 'die', 'xdie', 'pop'):
        s = tab.get(key, '')
        if letter in s:
            i, n = s.index(letter), len(s)
            if key == 'walk':
                return model({'walk': i * 2 * math.pi / n}), 6
            if key == 'atk':
                return model({'atk': i, 'flash': letter in tab.get('flash', s[-1:])}), 6
            if key == 'pain':
                return model({'pain': True}), 6
            if key == 'die':
                if prefix == 'SPID':
                    return model({'collapse': min(1.0, (i + 1) / (n - 1))}), 6
                return die(model, i, n), (6 if i < n - 2 else 22)
            if key == 'xdie':
                return burst(model, i, n, seed, play_leftovers() if prefix == 'PLAY' else None), (6 if i < n - 3 else 24)
            if key == 'pop':
                return popfx(model, i, n), 6
    return model({'walk': 0}), 6


# ======================================================================== decorations (rot 0)
def d_flagpole(ph=0.0, color='#2050c0'):
    o = [cap((0, 0, 0), (0, 70, 0), 1.3, '#c0c0c8'), ell((0, 71, 0), 2.2, '#f0c840'), box((0, 1.5, 0), (5, 1.5, 5), '#55555c')]
    for i in range(4):
        w = math.sin(ph + i * 1.2) * 2.5
        o.append(box((3.5 + i * 4.2, 60, w), (2.2, 8, 0.6), color, R=rot_y(D(math.sin(ph + i) * 20))))
    o.append(ell((10, 60, 3.2), (3.5, 3.5, 1.2), '#ffffff'))
    o.append(ell((10, 60, 3.9), (2, 2, 1), '#f0c840', emit=0.3))
    return o


def cup(x, y, s=1.0):
    return [cap((x, y, 0), (x, y + 4 * s, 0), 1.0 * s, '#d4a630'), box((x, y - 1, 0), (3 * s, 1, 3 * s), '#704020'),
            ell((x, y + 8 * s, 0), (4.5 * s, 4.5 * s, 4.5 * s), '#f0c040', tex=0.02),
            cap((x - 4.5 * s, y + 9 * s, 0), (x - 6.5 * s, y + 7 * s, 0), 0.8 * s, '#f0c040'),
            cap((x + 4.5 * s, y + 9 * s, 0), (x + 6.5 * s, y + 7 * s, 0), 0.8 * s, '#f0c040')]


def d_books(fl=0):
    o = []
    cols = ['#b02828', '#2850b0', '#28a050', '#d0a020', '#8040a0', '#e07020']
    y = 0
    for i in range(6):
        h = 2.6 + (i % 3) * 0.7
        o.append(box(((i % 2) * 2 - 1, y + h / 2 + 0.01, 0), (10 - i * 0.8, h / 2, 7 - i * 0.4), cols[i], R=rot_y(D(i * 17)), tex=0.04))
        o.append(box(((i % 2) * 2 - 1, y + h / 2 + 0.01, 0), (10.3 - i * 0.8, h / 2 - 0.5, 6.4 - i * 0.4), '#f4efe0', R=rot_y(D(i * 17))))
        y += h
    for x in (-8, 8):
        o += [cap((x, 0, 9), (x, 14, 9), 1.6, '#f4f0e0'), ell((x, 16.5 + fl * 0.8, 9), (1.4, 2.6 + fl * 0.6, 1.4), '#ffb030', emit=1.0)]
    return o


def d_paint():
    return [ell((0, 0.3, 0), (22, 0.6, 14), '#e040a0'), ell((-8, 0.6, 3), (9, 0.6, 7), '#40a0f0'), ell((9, 0.8, -2), (7, 0.6, 6), '#f0d040'),
            box((12, 4, 6), (3.5, 4, 3.5), '#c0c0c8', R=rot_z(D(80))), ell((12.5, 4, 9.6), (3, 3, 0.4), '#e040a0')]


def d_lantern(sw=0.0, col='#e03030'):
    o = [cap((0, 72, 0), (0, 50, 0), 0.5, '#5a4a3a'), cap((0, 48, 0), (0, 49.5, 0), 3, '#d0a030'),
         ell((0, 40, 0), (8, 9, 8), col, emit=0.45, tex=0.02), cap((0, 30, 0), (0, 31.5, 0), 3, '#d0a030')]
    for k in range(5):
        o.append(cap((-2 + k, 29, 0), (-2 + k, 22, 0), 0.4, '#f0c840'))
    T = rot_z(D(sw))
    return transform(transform(o, np.eye(3), (0, -72, 0)), T, (0, 72, 0))


def d_mobile(kind, sw=0.0):
    o = [cap((0, 72, 0), (0, 58, 0), 0.5, '#5a4a3a'), cap((-18, 58, 0), (18, 58, 0), 0.7, '#a07040')]
    if kind == 'stars':
        for i, x in enumerate((-18, -6, 6, 18)):
            L = 8 + (i % 2) * 8
            o += [cap((x, 58, 0), (x, 58 - L, 0), 0.35, '#888'), ell((x, 55 - L, 0), (4, 4, 1.2), '#ffd840', emit=0.6, R=rot_z(D(45))),
                  box((x, 55 - L, 0), (3, 3, 1.0), '#ffd840', R=rot_z(D(45)), emit=0.6)]
    elif kind == 'planets':
        for i, (x, c, r) in enumerate([(-18, '#e09040', 4), (-6, '#3070e0', 5), (6, '#d04030', 3.5), (18, '#e0c070', 6)]):
            L = 10 + (i % 2) * 9
            o += [cap((x, 58, 0), (x, 58 - L, 0), 0.35, '#888'), ell((x, 58 - L - r, 0), r, c, tex=0.05)]
        o.append(ell((18, 58 - 10 - 6, 0), (10, 0.8, 10), '#c0a060', R=rot_x(D(70))))
    elif kind == 'banner':
        o = [cap((0, 72, 0), (0, 66, 0), 0.5, '#5a4a3a'), cap((-14, 66, 0), (14, 66, 0), 1.0, '#a07040'),
             box((0, 52, 0), (13, 13, 0.6), '#2050c0'), box((0, 56, 0.7), (9, 1.6, 0.3), '#ffffff', emit=0.3),
             box((0, 50, 0.7), (9, 1.6, 0.3), '#ffffff', emit=0.3), ell((0, 43, 0.6), (4, 4, 0.5), '#f0c840', emit=0.4)]
    else:  # pennants
        o = [cap((-20, 72, 0), (20, 66, 0), 0.4, '#5a4a3a')]
        for i in range(6):
            x = -17 + i * 7; y = 71.3 - (x + 20) * 0.15
            o.append(box((x, y - 5, 0), (2.8, 5, 0.4), CONF[i % 5], R=rot_z(D(0))))
    return transform(transform(o, np.eye(3), (0, -72, 0)), rot_z(D(sw)), (0, 72, 0))


def d_apple(s=1.0):
    return [cap((0, 0, 0), (0, 34, 0), 7, '#2a7a3a', tex=0.08), ell((0, 34, 0), (9, 2.5, 9), '#2a7a3a'),
            ell((0, 43, 0), (7 * s, 6.5 * s, 7 * s), '#d82020', tex=0.03), cap((0, 48 * s + 1, 0), (1, 52, 0), 0.6, '#5a3a1a'),
            ell((3, 51, 0), (3, 1, 1.5), '#40c040')]


def d_fire(fl=0):
    o = []
    for i in range(8):
        a = i * math.pi / 4
        o.append(ell((9 * math.cos(a), 3, 9 * math.sin(a)), (4, 3.5, 4), '#6a6862', tex=0.2))
    for i in range(5):
        a = i * 1.3 + fl
        o.append(ell((3 * math.cos(a), 9 + i * 2.5 + fl, 3 * math.sin(a)), (5 - i * 0.8, 6 - i * 0.6, 5 - i * 0.8), ['#ff6010', '#ff9020', '#ffc040', '#fff080', '#ffffff'][i], emit=1.0))
    return o


def d_medal(color, lit):
    return [box((-3, 14, 0), (2, 6, 0.4), '#d02030', R=rot_z(D(-15))), box((3, 14, 0), (2, 6, 0.4), '#2040c0', R=rot_z(D(15))),
            ell((0, 6, 0), (6, 6, 1.6), color, emit=0.6 if lit else 0.15), ell((0, 6, 1.5), (3, 3, 0.6), '#ffffff', emit=0.6 if lit else 0.2)]


def d_chalk(s):
    o = []
    for i in range(5):
        a = i * 1.26
        o.append(ell((s * 3 * math.cos(a), 4 + s * 3 * math.sin(a), 0), 1.2 + s * 0.9, '#f0f0ff' if i % 2 else '#c8d8ff', emit=0.6))
    return o


DECOR = {
    'POL1': lambda L: d_flagpole(0, '#2050c0'),
    'POL6': lambda L: d_flagpole(0 if L == 'A' else 1.6, '#c03030'),
    'POL2': lambda L: [cap((0, 0, 0), (0, 62, 0), 1.3, '#c0c0c8'), box((0, 1.5, 0), (5, 1.5, 5), '#55555c')] + cup(0, 62, 1.0) + cup(-9, 44, 0.8) + cup(9, 30, 0.8)
                      + [cap((0, 46, 0), (-9, 44, 0), 0.7, '#c0c0c8'), cap((0, 32, 0), (9, 30, 0), 0.7, '#c0c0c8')],
    'POL3': lambda L: d_books(0 if L == 'A' else 1),
    'POL4': lambda L: [cap((0, 0, 0), (0, 44, 0), 1.3, '#c0c0c8'), box((0, 1.5, 0), (5, 1.5, 5), '#55555c')] + cup(0, 44, 1.4),
    'POL5': lambda L: d_paint(),
    'GOR1': lambda L: d_lantern({'A': -8, 'B': 0, 'C': 8}.get(L, 0)),
    'GOR2': lambda L: d_mobile('banner'),
    'GOR3': lambda L: d_mobile('stars'),
    'GOR4': lambda L: d_mobile('planets'),
    'GOR5': lambda L: d_mobile('pennants'),
    'COL5': lambda L: d_apple(1.0 if L == 'A' else 1.08),
    'FSKU': lambda L: d_fire({'A': 0, 'B': 1, 'C': 2}.get(L, 0)),
    'BSKU': lambda L: d_medal('#3070ff', L == 'B'),
    'RSKU': lambda L: d_medal('#ff3030', L == 'B'),
    'YSKU': lambda L: d_medal('#ffd030', L == 'B'),
    'POB1': lambda L: [ell((0, 0.3, 0), (14, 0.5, 9), '#3060e0'), ell((5, 0.6, 3), (6, 0.5, 4), '#6090ff')],
    'POB2': lambda L: [ell((0, 0.3, 0), (8, 0.5, 6), '#40b040'), ell((-2, 0.6, 1), (3, 0.5, 2), '#80e080')],
    'BRS1': lambda L: [ell((-3, 3, 0), 4, '#f4f2ea', tex=0.15), ell((3, 2.5, 2), 3.5, '#e8e6dc', tex=0.15), ell((0, 2, -3), 3, '#fafafa', tex=0.15)],
    'COL6': lambda L: [cap((0, 0, 0), (0, 32, 0), 7, '#a03030', tex=0.08), ell((0, 32, 0), (9, 2.5, 9), '#a03030'),
                       ell((0, 42, 0), 7, '#2a64c8', tex=0.05), on_sphere((0, 42, 0), 7, (-0.5, 0.4, 0.8), 3, '#3aa83a'), on_sphere((0, 42, 0), 7, (0.6, -0.2, 0.8), 2.5, '#3aa83a')],
    'BLUD': lambda L: d_chalk({'A': 0.6, 'B': 1.2, 'C': 2.0}.get(L, 1)),
}
PITCH = {'POL5': 55, 'POB1': 60, 'POB2': 60, 'BRS1': 30}


def sprite_lumps(wad):
    i, j = wad.index('S_START'), wad.index('S_END')
    return range(i + 1, j)


def build_sprites(wad, pal, log=print, only=None):
    cache = {}
    n = 0
    for li in sprite_lumps(wad):
        name = wad.lumps[li][0]
        pre = name[:4]
        if only and pre not in only:
            continue
        if pre not in TAB and pre not in DECOR:
            continue
        L, rot = name[4], int(name[5])
        key = (pre, L, rot)
        if key not in cache:
            if pre in TAB:
                prims, sink = monster_prims(pre, L)
                pitch = 6 if sink < 10 else 18
            else:
                prims, sink = DECOR[pre](L), 2
                pitch = PITCH.get(pre, 6)
            yaw = -(max(rot, 1) - 1) * 45
            rgba, ox, oy = render(prims, yaw_deg=yaw, pitch_deg=pitch)
            rgba, ox, oy = crop(rgba, ox, oy)
            top = oy + (3 if pre in TAB else 1)
            if pre in ('GOR1', 'GOR2', 'GOR3', 'GOR4', 'GOR5'):
                top = oy
            if pre in ('POL5', 'POB1', 'POB2', 'BRS1'):
                top = rgba.shape[0] - 2
            if pre == 'BLUD':
                ox, top = rgba.shape[1] // 2, rgba.shape[0] // 2 + 4
            cache[key] = picture_from_rgba(pal, rgba, int(ox), int(top))
        wad.lumps[li][1] = cache[key]
        n += 1
    log(f'sprites replaced: {n} lumps ({len(cache)} unique renders)')
    return n
