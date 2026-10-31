"""Minimal WAD reader/writer + Doom picture codec + palette quantizer (GPLv2, CLASS BUSTER)."""
import struct
import numpy as np


class Wad:
    def __init__(self, path):
        d = open(path, 'rb').read()
        self.kind = d[:4]
        n, off = struct.unpack('<ii', d[4:12])
        self.lumps = []  # [name, bytes]
        for i in range(n):
            o, s, nm = struct.unpack('<ii8s', d[off + i * 16: off + i * 16 + 16])
            self.lumps.append([nm.rstrip(b'\0').decode('latin-1').upper(), d[o:o + s]])

    def names(self):
        return [l[0] for l in self.lumps]

    def index(self, name, start=0):
        for i in range(start, len(self.lumps)):
            if self.lumps[i][0] == name:
                return i
        return -1

    def get(self, name):
        i = self.index(name)
        return self.lumps[i][1] if i >= 0 else None

    def set(self, name, data, before=None):
        """Replace every lump with this name (or insert before marker if absent)."""
        hit = False
        for l in self.lumps:
            if l[0] == name:
                l[1] = data
                hit = True
        if not hit:
            pos = self.index(before) if before else len(self.lumps)
            self.lumps.insert(pos if pos >= 0 else len(self.lumps), [name, data])

    def between(self, a, b):
        i, j = self.index(a), self.index(b)
        return [l for l in self.lumps[i + 1:j]]

    def save(self, path):
        body = bytearray()
        dirs = []
        pos = 12
        for nm, data in self.lumps:
            dirs.append((pos, len(data), nm))
            body += data
            pos += len(data)
        out = bytearray(self.kind + struct.pack('<ii', len(self.lumps), pos))
        out += body
        for o, s, nm in dirs:
            out += struct.pack('<ii8s', o if s else 0, s, nm.encode('latin-1')[:8])
        open(path, 'wb').write(out)


# ------------------------------------------------------------------ palette
class Palette:
    def __init__(self, playpal):
        self.rgb = np.frombuffer(playpal[:768], dtype=np.uint8).reshape(256, 3).astype(np.int32)
        # avoid index 247 (often used as transparency elsewhere) and pure cyan
        self.allowed = np.ones(256, bool)
        self.allowed[247] = False
        self._cache = {}

    def quantize(self, rgb):
        """rgb: HxWx3 uint8/float -> HxW uint8 palette indices (nearest, perceptual-ish weights)."""
        a = np.asarray(rgb, dtype=np.int32)
        flat = a.reshape(-1, 3)
        key = flat[:, 0] * 65536 + flat[:, 1] * 256 + flat[:, 2]
        uniq, inv = np.unique(key, return_inverse=True)
        u = np.stack([uniq >> 16, (uniq >> 8) & 255, uniq & 255], 1)
        pal = self.rgb[self.allowed]
        idx = np.nonzero(self.allowed)[0]
        w = np.array([3, 4, 2])
        res = np.empty(len(u), np.int32)
        for s in range(0, len(u), 4096):
            d = (((u[s:s + 4096, None, :] - pal[None, :, :]) ** 2) * w).sum(-1)
            res[s:s + 4096] = idx[d.argmin(1)]
        return res[inv].reshape(a.shape[:2]).astype(np.uint8)


# ------------------------------------------------------------------ picture format
def encode_picture(idx, mask, leftoff, topoff):
    """idx: HxW palette indices, mask: HxW bool opaque. Returns Doom patch bytes."""
    h, w = idx.shape
    cols = []
    for x in range(w):
        col = bytearray()
        y = 0
        while y < h:
            if not mask[y, x]:
                y += 1
                continue
            y0 = y
            while y < h and mask[y, x] and y - y0 < 128:
                y += 1
            run = idx[y0:y, x]
            # topdelta must be < 255 (no tall-patch tricks needed for our sizes)
            col += bytes([y0, len(run), run[0]]) + bytes(run.tolist()) + bytes([run[-1]])
        col += b'\xff'
        cols.append(bytes(col))
    head = struct.pack('<hhhh', w, h, leftoff, topoff)
    offs = []
    pos = 8 + 4 * w
    for c in cols:
        offs.append(pos)
        pos += len(c)
    return head + b''.join(struct.pack('<I', o) for o in offs) + b''.join(cols)


def decode_picture(data, pal_rgb=None):
    w, h, lo, to = struct.unpack('<hhhh', data[:8])
    idx = np.zeros((h, w), np.uint8)
    mask = np.zeros((h, w), bool)
    for x in range(w):
        p = struct.unpack('<I', data[8 + 4 * x: 12 + 4 * x])[0]
        top = -1
        while data[p] != 0xff:
            td = data[p]
            top = td if td > top else top + td
            n = data[p + 1]
            seg = np.frombuffer(data[p + 3:p + 3 + n], np.uint8)
            yy = top + np.arange(n)
            ok = yy < h
            idx[yy[ok], x] = seg[ok]
            mask[yy[ok], x] = True
            p += n + 4
    return idx, mask, lo, to


def picture_from_rgba(pal, rgba, leftoff, topoff, alpha_thresh=128):
    rgba = np.asarray(rgba)
    mask = rgba[..., 3] >= alpha_thresh
    idx = pal.quantize(rgba[..., :3])
    return encode_picture(idx, mask, leftoff, topoff)


def dmx_sound(samples, rate=11025):
    """samples: float array -1..1 -> DMX format 3 lump with 16-byte pads."""
    s = np.clip(np.asarray(samples, np.float64), -1, 1)
    b = (s * 127 + 128).round().clip(0, 255).astype(np.uint8)
    pad0 = bytes([b[0]]) * 16
    pad1 = bytes([b[-1]]) * 16
    body = pad0 + b.tobytes() + pad1
    return struct.pack('<HHI', 3, rate, len(body)) + body
