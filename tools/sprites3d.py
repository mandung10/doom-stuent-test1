"""Tiny analytic ray-caster for building Doom-style 8-rotation sprites from primitives.
Local model space: x = model's LEFT (screen-right when it faces us), y = up, z = forward. 1 unit = 1 output pixel.
"""
import math
import numpy as np

SS = 3  # supersampling


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def col(h):
    if isinstance(h, str):
        h = h.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
    return np.array(h, float)


class P:
    """primitive: kind in ell|cap|box. emit: 0..1 self-illumination."""
    def __init__(self, kind, color, emit=0.0, **kw):
        self.kind, self.color, self.emit = kind, col(color), emit
        self.c = np.array(kw.get('c', (0, 0, 0)), float)
        self.r = np.array(kw.get('r', (1, 1, 1)), float) if kind != 'cap' else kw.get('r', 1.0)
        self.R = np.array(kw.get('R', np.eye(3)), float)
        self.a = np.array(kw.get('a', (0, 0, 0)), float)
        self.b = np.array(kw.get('b', (0, 1, 0)), float)
        self.tex = kw.get('tex', 0.06)

    def xform(self, M, t=np.zeros(3)):
        q = P.__new__(P)
        q.__dict__.update(self.__dict__)
        q.c = M @ self.c + t
        q.a = M @ self.a + t
        q.b = M @ self.b + t
        q.R = M @ self.R
        return q

    def bound(self):
        if self.kind == 'cap':
            return np.minimum(self.a, self.b) - self.r, np.maximum(self.a, self.b) + self.r
        e = np.abs(self.R) @ self.r if self.kind == 'box' else np.sqrt((self.R ** 2) @ (self.r ** 2))
        return self.c - e, self.c + e


def ell(c, r, color, R=None, emit=0.0, tex=0.06):
    if np.isscalar(r):
        r = (r, r, r)
    return P('ell', color, emit, c=c, r=r, R=np.eye(3) if R is None else R, tex=tex)


def box(c, half, color, R=None, emit=0.0, tex=0.06):
    return P('box', color, emit, c=c, r=half, R=np.eye(3) if R is None else R, tex=tex)


def cap(a, b, r, color, emit=0.0, tex=0.06):
    return P('cap', color, emit, a=a, b=b, r=r, tex=tex)


def transform(prims, M, t=(0, 0, 0)):
    return [p.xform(M, np.array(t, float)) for p in prims]


# ----------------------------------------------------------------- intersection (rays along -z, orthographic)
def _hit_ell(p, X, Y, Z0):
    Rt = p.R.T
    o = np.stack([X - p.c[0], Y - p.c[1], np.full_like(X, Z0 - p.c[2])], -1) @ Rt.T / p.r
    d = (Rt @ np.array([0, 0, -1.0])) / p.r
    a = d @ d
    b = o @ d
    c = (o * o).sum(-1) - 1
    h = b * b - a * c
    ok = h >= 0
    t = np.where(ok, (-b - np.sqrt(np.maximum(h, 0))) / a, np.inf)
    lp = o + t[..., None] * d
    n = (lp / p.r) @ Rt  # gradient in world
    return t, n


def _hit_box(p, X, Y, Z0):
    Rt = p.R.T
    o = np.stack([X - p.c[0], Y - p.c[1], np.full_like(X, Z0 - p.c[2])], -1) @ Rt.T
    d = Rt @ np.array([0, 0, -1.0])
    with np.errstate(divide='ignore', invalid='ignore'):
        inv = 1.0 / np.where(np.abs(d) < 1e-9, 1e-9, d)
        t1 = (-p.r - o) * inv
        t2 = (p.r - o) * inv
    tn = np.minimum(t1, t2)
    tf = np.maximum(t1, t2)
    tnear = tn.max(-1)
    tfar = tf.min(-1)
    ok = (tnear <= tfar) & (tfar > 0)
    t = np.where(ok, tnear, np.inf)
    ax = tn.argmax(-1)
    nl = np.zeros(o.shape)
    sgn = -np.sign(np.take_along_axis(np.broadcast_to(d, o.shape), ax[..., None], -1))[..., 0]
    np.put_along_axis(nl, ax[..., None], sgn[..., None], -1)
    return t, nl @ Rt


def _hit_cap(p, X, Y, Z0):
    ro = np.stack([X, Y, np.full_like(X, Z0)], -1)
    rd = np.array([0, 0, -1.0])
    ba = p.b - p.a
    oa = ro - p.a
    baba = ba @ ba + 1e-9
    bard = ba @ rd
    baoa = oa @ ba
    rdoa = oa @ rd
    oaoa = (oa * oa).sum(-1)
    A = baba - bard * bard
    A = A if abs(A) > 1e-6 else 1e-6
    B = baba * rdoa - baoa * bard
    C = baba * oaoa - baoa * baoa - p.r * p.r * baba
    h = B * B - A * C
    t = np.full(X.shape, np.inf)
    ok = h >= 0
    tb = (-B - np.sqrt(np.maximum(h, 0))) / A
    yy = baoa + tb * bard
    body = ok & (yy > 0) & (yy < baba)
    t[body] = tb[body]
    # caps
    for end in (p.a, p.b):
        oc = ro - end
        bb = oc @ rd
        cc = (oc * oc).sum(-1) - p.r * p.r
        hh = bb * bb - cc
        tc = np.where(hh > 0, -bb - np.sqrt(np.maximum(hh, 0)), np.inf)
        t = np.minimum(t, tc)
    pt = ro + t[..., None] * rd
    pa = pt - p.a
    hh = np.clip((pa @ ba) / baba, 0, 1)
    n = pa - hh[..., None] * ba
    return t, n


HIT = {'ell': _hit_ell, 'box': _hit_box, 'cap': _hit_cap}
LIGHT = np.array([-0.45, 0.55, 0.70])
LIGHT /= np.linalg.norm(LIGHT)


def _hash3(P3):
    v = np.sin(P3[..., 0] * 12.9898 + P3[..., 1] * 78.233 + P3[..., 2] * 37.719) * 43758.5453
    return v - np.floor(v)


def render(prims, yaw_deg=0.0, pitch_deg=6.0, ground=None, outline=True, desat=0.0, ambient=0.38):
    """Render primitives seen by an orthographic camera.  Returns (rgba uint8 HxWx4, origin_x, origin_y)
    where origin is the screen position of model point (0,0,0)."""
    M = rot_x(math.radians(pitch_deg)) @ rot_y(math.radians(yaw_deg))
    W = transform(prims, M)
    lo = np.min([p.bound()[0] for p in W], 0) - 2
    hi = np.max([p.bound()[1] for p in W], 0) + 2
    x0, x1 = math.floor(lo[0]), math.ceil(hi[0])
    y0, y1 = math.floor(lo[1]), math.ceil(hi[1])
    w, h = x1 - x0, y1 - y0
    xs = x0 + (np.arange(w * SS) + 0.5) / SS
    ys = y1 - (np.arange(h * SS) + 0.5) / SS
    X, Y = np.meshgrid(xs, ys)
    Z0 = hi[2] + 5
    tbest = np.full(X.shape, np.inf)
    nbest = np.zeros(X.shape + (3,))
    cbest = np.zeros(X.shape + (3,))
    ebest = np.zeros(X.shape)
    tx = np.zeros(X.shape)
    for p in W:
        bl, bh = p.bound()
        # restrict to bbox for speed
        cx0 = max(0, int((bl[0] - x0) * SS) - 1); cx1 = min(w * SS, int((bh[0] - x0) * SS) + 2)
        cy0 = max(0, int((y1 - bh[1]) * SS) - 1); cy1 = min(h * SS, int((y1 - bl[1]) * SS) + 2)
        if cx1 <= cx0 or cy1 <= cy0:
            continue
        sl = (slice(cy0, cy1), slice(cx0, cx1))
        t, n = HIT[p.kind](p, X[sl], Y[sl], Z0)
        better = t < tbest[sl]
        if not better.any():
            continue
        tb = tbest[sl]; tb[better] = t[better]
        nb = nbest[sl]; nb[better] = n[better]
        cb = cbest[sl]; cb[better] = p.color
        eb = ebest[sl]; eb[better] = p.emit
        tt = tx[sl]; tt[better] = p.tex
    hit = np.isfinite(tbest)
    n = nbest / (np.linalg.norm(nbest, axis=-1, keepdims=True) + 1e-9)
    diff = np.clip(n @ LIGHT, 0, 1)
    rim = np.clip(n[..., 2], 0, 1)
    spec = np.clip(n @ (LIGHT + np.array([0, 0, 1.0])) / np.linalg.norm(LIGHT + np.array([0, 0, 1.0])), 0, 1) ** 24
    pts = np.stack([X, Y, Z0 - tbest], -1)
    grain = (_hash3(np.floor(np.where(np.isfinite(pts), pts, 0) * 1.0)) - 0.5) * 2 * tx
    shade = ambient + (1 - ambient) * diff * (0.75 + 0.25 * rim)
    rgb = cbest * (shade * (1 + grain))[..., None] + 90 * spec[..., None]
    rgb = rgb * (1 - ebest[..., None]) + cbest * ebest[..., None] * (1 + 0.15 * grain[..., None])
    if desat:
        g = rgb.mean(-1, keepdims=True)
        rgb = rgb * (1 - desat) + g * desat
    rgb[~hit] = 0
    # downsample
    rgbs = rgb.reshape(h, SS, w, SS, 3)
    hs = hit.reshape(h, SS, w, SS)
    cov = hs.mean((1, 3))
    csum = (rgbs * hs[..., None]).sum((1, 3))
    out = csum / np.maximum(hs.sum((1, 3)), 1)[..., None]
    alpha = (cov >= 0.45)
    if outline:
        # darken silhouette edge pixels (Doom sprites have dark rims)
        a = alpha
        edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
        out[edge] *= 0.55
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = np.clip(out, 0, 255)
    rgba[..., 3] = alpha * 255
    # origin screen position of (0,0,0)
    ox, oy = -x0, y1
    return rgba, ox, oy


def crop(rgba, ox, oy):
    a = rgba[..., 3] > 0
    if not a.any():
        return np.zeros((1, 1, 4), np.uint8), 0, 0
    ys, xs = np.nonzero(a)
    yy0, yy1, xx0, xx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgba[yy0:yy1, xx0:xx1], ox - xx0, oy - yy0
