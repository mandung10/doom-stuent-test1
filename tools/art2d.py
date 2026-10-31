"""CLASS BUSTER — 2D art & sound: Korean menu graphics, title/help/credit/ending screens,
intermission labels, the student status-bar face, non-gore wall/flat replacements, sound effects.  (GPLv2)"""
import glob
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from wadlib import picture_from_rgba, decode_picture, encode_picture, dmx_sound


def _font(pref):
    for p in pref:
        g = glob.glob('/usr/share/fonts/**/' + p, recursive=True)
        if g:
            return g[0]
    raise SystemExit('Korean font not found (install fonts-nanum): ' + str(pref))


FONT_HEAVY = _font(['NanumSquareEB.ttf', 'NanumSquare_acEB.ttf', 'NanumGothicExtraBold.ttf'])
FONT_BOLD = _font(['NanumSquareB.ttf', 'NanumGothicBold.ttf'])
FONT_BRUSH = _font(['NanumBrush.ttf', 'NanumGothicExtraBold.ttf'])
SS = 4


def F(path, size):
    return ImageFont.truetype(path, size)


def _grad(w, h, stops):
    """vertical gradient, stops = [(pos0..1, '#rrggbb'), ...]"""
    ys = np.linspace(0, 1, h)[:, None]
    cols = [(p, np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)) for p, c in stops]
    out = np.zeros((h, 3))
    for (p0, c0), (p1, c1) in zip(cols, cols[1:]):
        m = (ys[:, 0] >= p0) & (ys[:, 0] <= p1)
        t = ((ys[m, 0] - p0) / max(p1 - p0, 1e-6))[:, None]
        out[m] = c0 * (1 - t) + c1 * t
    return np.repeat(out[:, None, :], w, 1).astype(np.uint8)


DOOM_RED = [(0, '#ff8a6a'), (0.45, '#e01a10'), (1, '#7a0000')]
GOLD = [(0, '#fff6b0'), (0.4, '#ffc020'), (0.75, '#d06000'), (1, '#801800')]


def text_rgba(text, size, stops=DOOM_RED, font=FONT_HEAVY, stroke=1.0, outline='#2a0000', shadow=1, extrude=0, tracking=0):
    """Supersampled, outlined, gradient-filled text -> RGBA ndarray at 1x."""
    f = F(font, size * SS)
    sw = max(1, int(stroke * SS))
    bb = f.getbbox(text, stroke_width=sw)
    w = bb[2] - bb[0] + (shadow + extrude) * SS + 2 * SS + tracking * SS * len(text)
    h = bb[3] - bb[1] + (shadow + extrude) * SS + 2 * SS
    ox, oy = -bb[0] + SS, -bb[1] + SS
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)

    def draw(dx, dy, fill, strokecol=None):
        if tracking:
            x = ox + dx
            for ch in text:
                d.text((x, oy + dy), ch, font=f, fill=fill, stroke_width=sw if strokecol else 0, stroke_fill=strokecol)
                x += f.getlength(ch) + tracking * SS
        else:
            d.text((ox + dx, oy + dy), text, font=f, fill=fill, stroke_width=sw if strokecol else 0, stroke_fill=strokecol)
    for e in range(extrude * SS, 0, -SS // 2):
        draw(e, e, (40, 0, 0, 255), (20, 0, 0, 255))
    if shadow:
        draw((shadow + extrude) * SS, (shadow + extrude) * SS, (0, 0, 0, 220), (0, 0, 0, 220))
    draw(0, 0, outline, outline)
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    if tracking:
        x = ox
        for ch in text:
            md.text((x, oy), ch, font=f, fill=255); x += f.getlength(ch) + tracking * SS
    else:
        md.text((ox, oy), text, font=f, fill=255)
    tb = mask.getbbox() or (0, 0, w, h)
    g = np.zeros((h, w, 3), np.uint8)
    g[tb[1]:tb[3]] = _grad(w, tb[3] - tb[1], stops)
    base.paste(Image.fromarray(g), (0, 0), mask)
    small = base.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    return np.array(small)


def patch_text(pal, text, size=15, stops=DOOM_RED, lo=0, to=0, **kw):
    a = text_rgba(text, size, stops, **kw)
    return picture_from_rgba(pal, a, lo, to, alpha_thresh=110), a.shape[1], a.shape[0]


# ---------------------------------------------------------------- full screens
def _noise(h, w, s, amp, seed=1):
    r = np.random.default_rng(seed)
    n = r.random((h // s + 2, w // s + 2))
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((w + 2 * s, h + 2 * s), Image.BICUBIC)
    return (np.array(im)[:h, :w] / 255.0 - 0.5) * amp


def school_scene(w=320, h=200, sky='night', seed=3):
    """Painted school silhouette background (RGB ndarray)."""
    if sky == 'night':
        img = _grad(w, h, [(0, '#12040a'), (0.45, '#5a0c10'), (0.75, '#c03a10'), (1, '#ff9a30')]).astype(float)
    else:
        img = _grad(w, h, [(0, '#3a7ad8'), (0.6, '#9ad0ff'), (1, '#fff0c0')]).astype(float)
    img += _noise(h, w, 12, 18, seed)[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    rnd = np.random.default_rng(seed)
    if sky == 'night':
        for _ in range(40):
            x, y = rnd.integers(0, w), rnd.integers(0, h // 3)
            d.point((int(x), int(y)), fill=(255, 220, 200))
        d.ellipse((w - 70, 14, w - 38, 46), fill=(255, 236, 190))
        d.ellipse((w - 62, 10, w - 32, 40), fill=tuple(int(v) for v in img[25, w - 47]))
    else:
        d.ellipse((w - 70, 14, w - 34, 50), fill=(255, 250, 200))
        for cx, cy in [(60, 30), (180, 22), (250, 60)]:
            for k in range(4):
                d.ellipse((cx + k * 12 - 14, cy - 8 + (k % 2) * 3, cx + k * 12 + 14, cy + 10), fill=(255, 255, 255))
    by = int(h * 0.48)
    dark = (24, 8, 14) if sky == 'night' else (120, 90, 80)
    face = (40, 14, 22) if sky == 'night' else (210, 170, 140)
    d.rectangle((20, by, w - 20, h), fill=dark)
    d.rectangle((24, by + 4, w - 24, h), fill=face)
    d.rectangle((w // 2 - 26, by - 30, w // 2 + 26, h), fill=dark)
    d.rectangle((w // 2 - 22, by - 26, w // 2 + 22, h), fill=face)
    d.ellipse((w // 2 - 11, by - 22, w // 2 + 11, by), fill=(240, 240, 230), outline=dark)
    d.line((w // 2, by - 11, w // 2, by - 18), fill=dark, width=2)
    d.line((w // 2, by - 11, w // 2 + 6, by - 11), fill=dark, width=2)
    d.polygon([(w // 2 - 30, by - 30), (w // 2, by - 48), (w // 2 + 30, by - 30)], fill=dark)
    for row in range(4):
        for c in range(14):
            x = 32 + c * 19
            if abs(x + 6 - w // 2) < 30:
                continue
            y = by + 10 + row * 22
            lit = rnd.random() < (0.55 if sky == 'night' else 0.0)
            col = (255, 210, 90) if lit else ((60, 20, 30) if sky == 'night' else (120, 170, 220))
            d.rectangle((x, y, x + 11, y + 13), fill=col)
            d.line((x + 6, y, x + 6, y + 13), fill=dark)
    d.rectangle((0, h - 14, w, h), fill=(16, 6, 10) if sky == 'night' else (90, 150, 70))
    return np.array(im)


def paste_rgba(dst, src, x, y):
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(float)
    a = s[..., 3:4] / 255
    dst[y0:y1, x0:x1] = (dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a).astype(np.uint8)


def centered(dst, src, y):
    paste_rgba(dst, src, (dst.shape[1] - src.shape[1]) // 2, y)


def logo_rgba(scale=1.0):
    big = text_rgba('교실 대소동', int(46 * scale), GOLD, FONT_HEAVY, stroke=1.4, outline='#3a0800', shadow=0, extrude=3)
    sub = text_rgba('C L A S S   B U S T E R', int(13 * scale), DOOM_RED, FONT_HEAVY, stroke=1, outline='#200000', shadow=1)
    w = max(big.shape[1], sub.shape[1])
    out = np.zeros((big.shape[0] + sub.shape[0] - 2, w, 4), np.uint8)
    out[:big.shape[0], (w - big.shape[1]) // 2:(w - big.shape[1]) // 2 + big.shape[1]] = big
    y = big.shape[0] - 2
    sl = out[y:y + sub.shape[0], (w - sub.shape[1]) // 2:(w - sub.shape[1]) // 2 + sub.shape[1]]
    m = sub[..., 3:4] > 0
    sl[:] = np.where(m, sub, sl)
    return out


def full_rgb_to_pic(pal, rgb):
    a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    return picture_from_rgba(pal, a, 0, 0)


def titlepic():
    bg = school_scene(320, 200, 'night', 7)
    lg = logo_rgba(1.0)
    centered(bg, lg, 22)
    tag = text_rgba('과목 몬스터가 학교를 점령했다!', 11, [(0, '#ffffff'), (1, '#ffd0a0')], FONT_BOLD, stroke=1, outline='#000000', shadow=1)
    centered(bg, tag, 92)
    return bg


def text_screen(title, lines, bgkind='board', seed=5, title_stops=GOLD):
    if bgkind == 'board':
        bg = np.zeros((200, 320, 3), float) + np.array([28, 64, 44])
        bg += _noise(200, 320, 6, 22, seed)[..., None]
        bg = np.clip(bg, 0, 255).astype(np.uint8)
        im = Image.fromarray(bg); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 319, 199), outline=(120, 80, 40), width=6)
        d.rectangle((6, 6, 313, 193), outline=(70, 46, 22), width=1)
        d.rectangle((40, 186, 120, 190), fill=(240, 240, 240))
        bg = np.array(im)
    else:
        bg = school_scene(320, 200, bgkind, seed)
        bg = (bg * 0.45).astype(np.uint8)
    t = text_rgba(title, 18, title_stops, FONT_HEAVY, stroke=1.2, outline='#200000', shadow=1)
    centered(bg, t, 12)
    y = 12 + t.shape[0] + 6
    for ln in lines:
        if not ln:
            y += 6; continue
        col = [(0, '#ffffff'), (1, '#e8e8e8')]
        if ln.startswith('*'):
            ln = ln[1:]; col = [(0, '#fff2a0'), (1, '#ffc040')]
        r = text_rgba(ln, 10, col, FONT_BOLD, stroke=0.8, outline='#000000', shadow=1)
        paste_rgba(bg, r, 22, y)
        y += r.shape[0] - 1
    return bg


def help_screen():
    return text_screen('도움말 · 조작법', [
        '*이동', 'W A S D  앞·뒤·옆걸음   /   ↑ ↓  전진·후진   /   Shift  달리기',
        '*시점', '마우스(화면 클릭 시 고정) 또는 ← →   ·   Alt + ← →  옆걸음',
        '*공격 · 행동', '클릭 / Ctrl  발사   ·   Space / E  문 · 스위치 · 리프트',
        '*무기', '1 자·분필   2 분필총   3 지우개 산탄총   4 형광펜 개틀링',
        '5 종이비행기 런처   6 레이저 캐논   7 BFG(최종 과제)',
        '*기타', 'Tab  지도   ·   F2 저장   F3 불러오기   ·   Esc  메뉴',
        '', '*목표: 열쇠 메달(파랑·노랑·빨강)을 모아 문을 열고 EXIT 스위치로!',
    ])


def credit_screen():
    return text_screen('만든 사람들', [
        '*교실 대소동 : CLASS BUSTER', '학생을 위한 비잔혹 Doom 개조판',
        '', '*게임 엔진', 'DOOM  ©1993 id Software — GPL v2 공개 소스',
        'Chocolate Doom — Simon Howard 외   ·   doomgeneric — ozkl',
        '', '*게임 데이터', 'Freedoom 프로젝트 (BSD) 의 맵·텍스처·음악·효과음 기반',
        '과목 몬스터 · 학생 얼굴 · 한글 메뉴 · 비잔혹 그래픽 새로 제작',
    ], 'night', 9)


def ending_screen(kind):
    if kind == 'VICTORY2':
        bg = school_scene(320, 200, 'day', 11)
        t = text_rgba('1학기 클리어!', 26, GOLD, FONT_HEAVY, stroke=1.3, outline='#3a0800', extrude=2)
        centered(bg, t, 20)
        s = text_rgba('하지만 과학관에서 수상한 소리가…', 11, [(0, '#ffffff'), (1, '#ffffff')], FONT_BOLD, outline='#000000')
        centered(bg, s, 20 + t.shape[0] + 4)
        return bg
    bg = school_scene(320, 200, 'day', 13)
    t = text_rgba('방학이다!!', 34, GOLD, FONT_HEAVY, stroke=1.4, outline='#3a0800', extrude=3)
    centered(bg, t, 18)
    s = text_rgba('모든 과목 몬스터를 물리쳤습니다. 수고했어요!', 11, [(0, '#ffffff'), (1, '#ffffff')], FONT_BOLD, outline='#000000')
    centered(bg, s, 18 + t.shape[0] + 4)
    return bg


def panorama(i):
    bg = school_scene(320, 200, 'day', 20 + i)
    if i == 0:
        t = text_rgba('시험 끝!', 30, GOLD, FONT_HEAVY, stroke=1.3, outline='#3a0800', extrude=2)
        centered(bg, t, 24)
    return bg


# ---------------------------------------------------------------- status-bar face
def face_rgba(w, h, pain, look=0, mood='normal', turn=0):
    S = 8
    W, H = w * S, h * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W // 2 + turn * 2 * S
    skin = (242, 200, 160) if mood != 'god' else (255, 220, 120)
    if pain >= 3:
        skin = (226, 186, 150)
    d.ellipse((cx - 10 * S, 3 * S, cx + 10 * S, H - 1 * S), fill=skin, outline=(60, 30, 20), width=S)
    d.ellipse((cx - 12 * S + turn * S, 11 * S, cx - 8 * S + turn * S, 18 * S), fill=skin, outline=(60, 30, 20), width=S // 2)
    d.ellipse((cx + 8 * S + turn * S, 11 * S, cx + 12 * S + turn * S, 18 * S), fill=skin, outline=(60, 30, 20), width=S // 2)
    hair = (30, 26, 30)
    d.chord((cx - 11 * S, 1 * S, cx + 11 * S, 17 * S), 180, 360, fill=hair)
    d.polygon([(cx - 10 * S, 9 * S), (cx - 4 * S, 6 * S), (cx + 2 * S, 9 * S), (cx + 8 * S, 6 * S), (cx + 10 * S, 9 * S), (cx + 10 * S, 6 * S), (cx - 10 * S, 6 * S)], fill=hair)
    if pain >= 2:
        for k in range(3):
            x = cx - 8 * S + k * 7 * S
            d.polygon([(x, 3 * S), (x + 2 * S, -1 * S + k * S), (x + 4 * S, 3 * S)], fill=hair)
    ey = 14 * S
    ex = [cx - 5 * S + turn * S, cx + 5 * S + turn * S]
    if mood == 'dead':
        for x in ex:
            d.line((x - 3 * S, ey, x + 3 * S, ey), fill=(20, 20, 20), width=S)
        d.arc((cx - 3 * S, 19 * S, cx + 3 * S, 24 * S), 200, 340, fill=(90, 40, 30), width=S)
        f = F(FONT_HEAVY, 7 * S)
        d.text((cx + 5 * S, 0), 'z', font=f, fill=(120, 180, 255, 255))
        d.text((cx + 8 * S, -4 * S), 'Z', font=f, fill=(160, 210, 255, 255))
    elif mood == 'god':
        d.rounded_rectangle((cx - 10 * S, ey - 3 * S, cx + 10 * S, ey + 3 * S), radius=2 * S, fill=(15, 15, 25))
        d.line((cx - 7 * S, ey - 2 * S, cx - 4 * S, ey - 2 * S), fill=(200, 220, 255), width=S)
        d.arc((cx - 5 * S, 18 * S, cx + 5 * S, 25 * S), 20, 160, fill=(90, 30, 20), width=S)
    else:
        er = 3 * S if mood != 'ouch' else 4 * S
        for i, x in enumerate(ex):
            d.ellipse((x - er, ey - er, x + er, ey + er), fill=(255, 255, 255), outline=(40, 30, 30), width=S // 2)
            if pain >= 4 and mood == 'normal':
                d.arc((x - 2 * S, ey - 2 * S, x + 2 * S, ey + 2 * S), 0, 300, fill=(40, 40, 120), width=S // 2 + 1)
            else:
                px = x + look * S + turn * S
                pr = S + S // 2 if mood != 'ouch' else S
                d.ellipse((px - pr, ey - pr, px + pr, ey + pr), fill=(30, 24, 20))
            if pain >= 3:
                d.arc((x - 3 * S, ey + 1 * S, x + 3 * S, ey + 5 * S), 20, 160, fill=(150, 110, 120), width=S // 2)
        if mood == 'kill':
            d.line((ex[0] - 4 * S, ey - 6 * S, ex[0] + 3 * S, ey - 3 * S), fill=hair, width=S + S // 2)
            d.line((ex[1] + 4 * S, ey - 6 * S, ex[1] - 3 * S, ey - 3 * S), fill=hair, width=S + S // 2)
        else:
            dy = 1 if pain >= 2 else 0
            d.line((ex[0] - 3 * S, ey - 5 * S + dy * S, ex[0] + 3 * S, ey - 5 * S - dy * S), fill=hair, width=S)
            d.line((ex[1] - 3 * S, ey - 5 * S - dy * S, ex[1] + 3 * S, ey - 5 * S + dy * S), fill=hair, width=S)
        my = 22 * S
        mx = cx + turn * S
        if mood == 'ouch':
            d.ellipse((mx - 3 * S, my - 3 * S, mx + 3 * S, my + 3 * S), fill=(110, 20, 20), outline=(60, 10, 10), width=S // 2)
        elif mood == 'evil':
            d.chord((mx - 6 * S, my - 5 * S, mx + 6 * S, my + 3 * S), 0, 180, fill=(110, 20, 20))
            d.rectangle((mx - 5 * S, my - 1 * S, mx + 5 * S, my + 0 * S), fill=(255, 255, 255))
        elif mood == 'kill':
            d.rectangle((mx - 5 * S, my - 2 * S, mx + 5 * S, my + 2 * S), fill=(255, 255, 255), outline=(60, 10, 10), width=S // 2)
            for k in range(-3, 4, 2):
                d.line((mx + k * S, my - 2 * S, mx + k * S, my + 2 * S), fill=(120, 120, 120), width=S // 3)
        elif pain <= 1:
            d.arc((mx - 5 * S, my - 5 * S, mx + 5 * S, my + 2 * S), 20, 160, fill=(110, 30, 20), width=S)
        elif pain == 2:
            d.line((mx - 4 * S, my, mx + 4 * S, my), fill=(110, 30, 20), width=S)
        else:
            d.arc((mx - 5 * S, my - 1 * S, mx + 5 * S, my + 5 * S), 200, 340, fill=(110, 30, 20), width=S)
    # pain accessories (sweat, band-aids, dizzy) — never blood
    if pain >= 1 and mood != 'dead':
        x0 = cx + 9 * S
        d.ellipse((x0 - 1 * S, 8 * S, x0 + 2 * S, 12 * S), fill=(130, 200, 255), outline=(40, 90, 160), width=S // 2)
    if pain >= 2 and mood != 'dead':
        bx, by = cx - 6 * S + turn * S, 19 * S
        d.rounded_rectangle((bx - 4 * S, by - 1 * S, bx + 3 * S, by + 2 * S), radius=S, fill=(240, 200, 150), outline=(150, 110, 70), width=S // 2)
        d.line((bx - 1 * S, by - 1 * S, bx - 1 * S, by + 2 * S), fill=(150, 110, 70), width=S // 3)
    if pain >= 3 and mood != 'dead':
        bx, by = cx + 3 * S + turn * S, 7 * S
        d.rounded_rectangle((bx - 5 * S, by - 1 * S, bx + 4 * S, by + 2 * S), radius=S, fill=(250, 250, 250), outline=(160, 160, 170), width=S // 2)
        d.line((bx - 4 * S, by - 1 * S, bx + 3 * S, by + 2 * S), fill=(200, 60, 60), width=S // 2)
    if pain >= 4 and mood != 'dead':
        for k in range(3):
            a = k * 2.1
            x, y = cx + 9 * math.cos(a) * S, 1 * S + 2 * math.sin(a) * S
            d.ellipse((x - 1.5 * S, y - 1.5 * S + 2 * S, x + 1.5 * S, y + 1.5 * S + 2 * S), fill=(255, 230, 60))
    out = np.array(im.resize((w, h), Image.LANCZOS))
    return out


def build_faces(wad, pal):
    n = 0
    for li, (name, data) in enumerate(wad.lumps):
        if not name.startswith('STF') or name.startswith('STFB'):
            continue
        try:
            idx, m, lo, to = decode_picture(data)
        except Exception:
            continue
        h, w = idx.shape
        pain = int(name[-2]) if name[-2].isdigit() and not name.startswith('STFST') else 0
        if name.startswith('STFST'):
            pain = int(name[5]); look = [-1, 0, 1][int(name[6])]
            a = face_rgba(w, h, pain, look)
        elif name.startswith('STFTL'):
            a = face_rgba(w, h, int(name[5]), -1, turn=-1)
        elif name.startswith('STFTR'):
            a = face_rgba(w, h, int(name[5]), 1, turn=1)
        elif name.startswith('STFOUCH'):
            a = face_rgba(w, h, int(name[7]), 0, 'ouch')
        elif name.startswith('STFEVL'):
            a = face_rgba(w, h, int(name[6]), 0, 'evil')
        elif name.startswith('STFKILL'):
            a = face_rgba(w, h, int(name[7]), 0, 'kill')
        elif name.startswith('STFGOD'):
            a = face_rgba(w, h, 0, 0, 'god')
        elif name.startswith('STFDEAD'):
            a = face_rgba(w, h, 0, 0, 'dead')
        else:
            continue
        wad.lumps[li][1] = picture_from_rgba(pal, a, lo, to, alpha_thresh=100)
        n += 1
    return n


# ---------------------------------------------------------------- walls / flats
def pic_rgb(pal, data):
    idx, m, lo, to = decode_picture(data)
    return pal.rgb[idx].astype(np.uint8), m, lo, to


def red_to_ink(rgb):
    r, g, b = [rgb[..., i].astype(float) for i in range(3)]
    red = (r > g * 1.35 + 12) & (r > b * 1.35 + 12)
    v = r
    out = rgb.copy().astype(float)
    out[red] = np.stack([v[red] * 0.22, v[red] * 0.32, v[red] * 1.0], -1)
    return np.clip(out, 0, 255).astype(np.uint8)


def corkboard(w, h, seed):
    rnd = np.random.default_rng(seed)
    base = np.zeros((h, w, 3)) + np.array([176, 128, 78]) + _noise(h, w, 3, 40, seed)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    cols = [(250, 250, 240), (255, 240, 140), (180, 220, 255), (255, 190, 200), (200, 255, 200)]
    for k in range(max(2, w * h // 900)):
        pw, ph = int(rnd.integers(12, 26)), int(rnd.integers(14, 30))
        x, y = int(rnd.integers(0, max(1, w - pw))), int(rnd.integers(0, max(1, h - ph)))
        c = cols[k % len(cols)]
        d.rectangle((x, y, x + pw, y + ph), fill=c, outline=(120, 100, 80))
        for ly in range(y + 4, y + ph - 2, 3):
            d.line((x + 2, ly, x + pw - 3 - (ly * 7) % 6, ly), fill=(90, 90, 130))
        d.ellipse((x + pw // 2 - 1, y - 1, x + pw // 2 + 1, y + 1), fill=(220, 30, 30))
    d.rectangle((0, 0, w - 1, h - 1), outline=(100, 60, 30), width=2)
    return np.array(im)


def switch_panel(w, h, on):
    base = np.zeros((h, w, 3)) + np.array([120, 120, 128]) + _noise(h, w, 2, 16, 4)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle((1, 1, w - 2, h - 2), outline=(60, 60, 66))
    cx, cy = w // 2, h // 2
    d.rectangle((cx - w // 4, cy - h // 4, cx + w // 4, cy + h // 4), fill=(70, 70, 76), outline=(30, 30, 34))
    ly = cy - h // 6 if on else cy + h // 6
    d.line((cx, cy, cx, ly), fill=(20, 20, 20), width=max(2, w // 12))
    d.ellipse((cx - w // 10, ly - w // 10, cx + w // 10, ly + w // 10), fill=(220, 30, 30))
    lc = (60, 255, 80) if on else (255, 40, 30)
    d.ellipse((cx - 3, 3, cx + 3, 9), fill=lc)
    return np.array(im)


def build_walls(wad, pal, log=print):
    n = 0
    for li, (name, data) in enumerate(wad.lumps):
        try:
            if name.startswith('BLOD'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = red_to_ink(rgb)
            elif name in ('SPINE3_1', 'SPINE3_2', 'SPINE4_1', 'SKULFACE', 'BODY_1', 'BODY_2', 'BRNOPEN'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = corkboard(rgb.shape[1], rgb.shape[0], li)
                m[:] = True
            elif name in ('SW1SKULL', 'SW2SKULL'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = switch_panel(rgb.shape[1], rgb.shape[0], name.startswith('SW2'))
                m[:] = True
            else:
                continue
        except Exception as e:
            log('skip', name, e); continue
        wad.lumps[li][1] = encode_picture(pal.quantize(rgb), m, lo, to)
        n += 1
    fi, fj = wad.index('F_START'), wad.index('F_END')
    for li in range(fi + 1, fj):
        name = wad.lumps[li][0]
        if name.startswith('BLOOD') and len(wad.lumps[li][1]) == 4096:
            rgb = pal.rgb[np.frombuffer(wad.lumps[li][1], np.uint8).reshape(64, 64)].astype(np.uint8)
            wad.lumps[li][1] = pal.quantize(red_to_ink(rgb)).tobytes()
            n += 1
    return n


# ---------------------------------------------------------------- sounds
SR = 11025


def _t(d):
    return np.arange(int(SR * d)) / SR


def _env(n, a=0.005, r=0.1):
    e = np.ones(n); ai, ri = min(int(a * SR), n // 4), min(int(r * SR), n // 2)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e


def sweep(f0, f1, d, wave='sine', vib=0.0):
    t = _t(d); f = f0 * (f1 / f0) ** (t / d)
    if vib: f = f * (1 + vib * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave == 'square': s = np.sign(np.sin(ph)) * 0.6
    elif wave == 'saw': s = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif wave == 'tri': s = 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    else: s = np.sin(ph)
    return s * _env(len(t))


def noise(d, lp=0.5, seed=0):
    r = np.random.default_rng(seed).uniform(-1, 1, int(SR * d))
    out = np.zeros_like(r); acc = 0
    for i, v in enumerate(r):
        acc += lp * (v - acc); out[i] = acc
    return out / (np.abs(out).max() + 1e-9)


def cat(*xs):
    return np.concatenate(xs)


def mix(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o


def norm(x, g=0.9):
    return x / (np.abs(x).max() + 1e-9) * g


def sounds():
    s = {}
    faint = lambda f0, w, sd: norm(cat(sweep(f0, f0 * 0.3, 0.45, w, 0.04), mix(sweep(140, 90, 0.12, 'sine') * _env(int(0.12 * SR), 0.001, 0.1), noise(0.08, 0.3, sd) * 0.3)))
    s['DSPODTH1'] = faint(900, 'square', 1)
    s['DSPODTH2'] = faint(760, 'tri', 2)
    s['DSPODTH3'] = faint(1100, 'square', 3)
    bub = lambda sd: norm(cat(*[sweep(300 + 120 * k, 900 + 200 * k, 0.05, 'sine') for k in range(4)], sweep(700, 160, 0.35, 'tri')))
    s['DSBGDTH1'] = bub(1)
    s['DSBGDTH2'] = norm(cat(sweep(500, 1500, 0.08), sweep(1200, 200, 0.4, 'tri', 0.05)))
    s['DSSGTDTH'] = norm(mix(noise(0.6, 0.6, 5) * np.linspace(0.8, 0, int(0.6 * SR)) * 0.6, sweep(400, 80, 0.6, 'square', 0.08) * 0.6))
    s['DSCACDTH'] = norm(sweep(600, 120, 0.8, 'sine', 0.15))
    s['DSBRSDTH'] = norm(mix(noise(0.9, 0.08, 7) * np.linspace(1, 0, int(0.9 * SR)), sweep(110, 50, 0.9, 'sine') * 0.5))
    pd = lambda d: norm(mix(sweep(900, 40, d, 'saw', 0.03) * 0.7, noise(d, 0.15, 9) * np.linspace(0, 0.5, int(d * SR))))
    s['DSCYBDTH'] = pd(1.6)
    s['DSSPIDTH'] = pd(2.0)
    s['DSSKLDTH'] = norm(cat(*[sweep(f, f * 1.01, 0.06, 'tri') for f in (880, 1108, 1318, 1760)]))
    tromb = lambda base: norm(cat(*[sweep(base * r, base * r * 0.97, d, 'saw', 0.03 if d > 0.3 else 0) * 0.6 for r, d in [(1, 0.25), (0.94, 0.25), (0.89, 0.25), (0.84, 0.7)]]))
    s['DSPLDETH'] = tromb(392)
    s['DSPDIEHI'] = tromb(523)
    s['DSSLOP'] = norm(cat(noise(0.05, 0.9, 11), mix(noise(0.35, 0.95, 12) * np.exp(-_t(0.35) * 12), sweep(1500, 600, 0.2, 'tri') * 0.3)))
    return {k: dmx_sound(v) for k, v in s.items()}
