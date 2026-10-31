/* CLASS BUSTER — browser runtime for the doomgeneric/Chocolate Doom engine (GPLv2)
   - tiny in-memory WASI filesystem (WAD, config, savegames → localStorage)
   - 35 Hz tic clock, canvas presenter, keyboard / pointer-lock mouse
   - WebAudio: DMX sound effects (8 channels, stereo separation) + General-MIDI synth for music */
'use strict';
(() => {
const $ = (id) => document.getElementById(id);
const canvas = $('screen'), ctx2d = canvas.getContext('2d', { alpha: false });
const overlay = $('overlay'), statusEl = $('status'), barEl = $('bar');
let inst = null, mem = null, ex = null, started = false;
const dec = new TextDecoder(), enc = new TextEncoder();
const u8 = () => new Uint8Array(mem.buffer);
const dv = () => new DataView(mem.buffer);
const cstr = (p) => { const a = u8(); let e = p; while (a[e]) e++; return dec.decode(a.subarray(p, e)); };

/* ------------------------------------------------------------------ WASI FS */
const files = new Map();               // path -> {data:Uint8Array, size}
const dirs = new Set(['', '.']);
const fds = new Map();                 // fd -> {path, pos, dir, dirty}
let nextFd = 4, logBuf = '';
const PERSIST = /(\.dsg|\.cfg)$/i, LS = 'classbuster:';
const norm = (p) => p.replace(/\\/g, '/').replace(/^(\.\/)+/, '').replace(/^\/+/, '').replace(/\/\.\//g, '/').replace(/\/+$/, '');
function loadPersisted() {
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i); if (!k.startsWith(LS)) continue;
    try { const bin = atob(localStorage.getItem(k)); const d = new Uint8Array(bin.length);
      for (let j = 0; j < bin.length; j++) d[j] = bin.charCodeAt(j);
      const p = k.slice(LS.length); files.set(p, { data: d, size: d.length });
      const dir = p.split('/').slice(0, -1).join('/'); if (dir) dirs.add(dir);
    } catch (e) {}
  }
}
function persist(path) {
  const f = files.get(path); if (!f || !PERSIST.test(path)) return;
  let s = ''; const d = f.data.subarray(0, f.size);
  for (let i = 0; i < d.length; i += 0x8000) s += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000));
  try { localStorage.setItem(LS + path, btoa(s)); } catch (e) { console.warn('save failed', e); }
}
const E = { OK: 0, BADF: 8, EXIST: 20, NOENT: 44, NOTDIR: 54, ISDIR: 31 };
class Exit extends Error { constructor(c) { super('exit ' + c); this.code = c; } }
const wasi = {
  fd_prestat_get(fd, p) { if (fd !== 3) return E.BADF; const v = dv(); v.setUint8(p, 0); v.setUint32(p + 4, 1, true); return 0; },
  fd_prestat_dir_name(fd, p, l) { if (fd !== 3) return E.BADF; u8()[p] = 47; return 0; },
  fd_fdstat_get(fd, p) {
    const v = dv(); const o = fds.get(fd);
    const type = fd <= 2 ? 2 : fd === 3 || (o && o.dir) ? 3 : o ? 4 : -1;
    if (type < 0) return E.BADF;
    v.setUint8(p, type); v.setUint16(p + 2, 0, true);
    v.setBigUint64(p + 8, 0xffffffffffffffffn, true); v.setBigUint64(p + 16, 0xffffffffffffffffn, true); return 0;
  },
  fd_fdstat_set_flags() { return 0; },
  path_open(dirfd, dflags, pp, pl, oflags, rb, ri, fdflags, outp) {
    const path = norm(dec.decode(u8().slice(pp, pp + pl)));
    const CREAT = 1, DIRECTORY = 2, EXCL = 4, TRUNC = 8;
    if (dirs.has(path)) { const fd = nextFd++; fds.set(fd, { path, pos: 0, dir: true }); dv().setUint32(outp, fd, true); return 0; }
    if (oflags & DIRECTORY) return E.NOENT;
    let f = files.get(path);
    if (!f) { if (!(oflags & CREAT)) return E.NOENT; f = { data: new Uint8Array(1024), size: 0 }; files.set(path, f); }
    else if (oflags & EXCL) return E.EXIST;
    if (oflags & TRUNC) f.size = 0;
    const fd = nextFd++; fds.set(fd, { path, pos: (fdflags & 1) ? f.size : 0, dir: false, dirty: !!(oflags & (CREAT | TRUNC)) });
    dv().setUint32(outp, fd, true); return 0;
  },
  fd_read(fd, iovs, n, outp) {
    const o = fds.get(fd); if (!o || o.dir) { dv().setUint32(outp, 0, true); return fd === 0 ? 0 : E.BADF; }
    const f = files.get(o.path); const v = dv(), m = u8(); let total = 0;
    for (let i = 0; i < n; i++) {
      const b = v.getUint32(iovs + i * 8, true), l = v.getUint32(iovs + i * 8 + 4, true);
      const c = Math.max(0, Math.min(l, f.size - o.pos));
      m.set(f.data.subarray(o.pos, o.pos + c), b); o.pos += c; total += c; if (c < l) break;
    }
    v.setUint32(outp, total, true); return 0;
  },
  fd_write(fd, iovs, n, outp) {
    const v = dv(), m = u8(); let total = 0;
    for (let i = 0; i < n; i++) {
      const b = v.getUint32(iovs + i * 8, true), l = v.getUint32(iovs + i * 8 + 4, true);
      const chunk = m.subarray(b, b + l);
      if (fd === 1 || fd === 2) { logBuf += dec.decode(chunk); }
      else {
        const o = fds.get(fd); if (!o || o.dir) return E.BADF;
        const f = files.get(o.path);
        if (o.pos + l > f.data.length) { const nd = new Uint8Array(Math.max(o.pos + l, f.data.length * 2)); nd.set(f.data.subarray(0, f.size)); f.data = nd; }
        f.data.set(chunk, o.pos); o.pos += l; if (o.pos > f.size) f.size = o.pos; o.dirty = true;
      }
      total += l;
    }
    if (fd === 1 || fd === 2) { const lines = logBuf.split('\n'); logBuf = lines.pop(); lines.forEach((s) => s && console.log('[doom] ' + s)); }
    v.setUint32(outp, total, true); return 0;
  },
  fd_seek(fd, off, whence, outp) {
    const o = fds.get(fd); if (!o || o.dir) return E.BADF;
    const f = files.get(o.path); off = Number(off);
    o.pos = whence === 0 ? off : whence === 1 ? o.pos + off : f.size + off;
    if (o.pos < 0) o.pos = 0;
    dv().setBigUint64(outp, BigInt(o.pos), true); return 0;
  },
  fd_close(fd) { const o = fds.get(fd); if (o && o.dirty) persist(o.path); fds.delete(fd); return 0; },
  path_create_directory(fd, pp, pl) { const p = norm(dec.decode(u8().slice(pp, pp + pl))); if (dirs.has(p)) return E.EXIST; dirs.add(p); return 0; },
  path_remove_directory(fd, pp, pl) { dirs.delete(norm(dec.decode(u8().slice(pp, pp + pl)))); return 0; },
  path_unlink_file(fd, pp, pl) {
    const p = norm(dec.decode(u8().slice(pp, pp + pl))); if (!files.has(p)) return E.NOENT;
    files.delete(p); localStorage.removeItem(LS + p); return 0;
  },
  path_rename(fd, pp, pl, fd2, np, nl) {
    const a = norm(dec.decode(u8().slice(pp, pp + pl))), b = norm(dec.decode(u8().slice(np, np + nl)));
    const f = files.get(a); if (!f) return E.NOENT;
    files.delete(a); localStorage.removeItem(LS + a); files.set(b, f); persist(b); return 0;
  },
  proc_exit(code) { throw new Exit(code); },
};

/* ------------------------------------------------------------------ audio */
let AC = null, master = null, sfxBus = null, musBus = null;
function initAudio() {
  if (AC) { AC.resume(); return; }
  AC = new (window.AudioContext || window.webkitAudioContext)();
  master = AC.createDynamicsCompressor(); master.threshold.value = -10; master.ratio.value = 4; master.connect(AC.destination);
  sfxBus = AC.createGain(); sfxBus.gain.value = 0.9; sfxBus.connect(master);
  musBus = AC.createGain(); musBus.gain.value = 0.35; musBus.connect(master);
  Synth.init();
}
const sfxCache = new Map(), chans = [];
function sfxBuffer(lump, ptr, len) {
  let b = sfxCache.get(lump); if (b) return b;
  const v = dv(); const fmt = v.getUint16(ptr, true); if (fmt !== 3 || len < 8) return null;
  const rate = v.getUint16(ptr + 2, true) || 11025; let n = v.getUint32(ptr + 4, true);
  let start = ptr + 8, cnt = n;
  if (n > 32) { start += 16; cnt = n - 32; }
  cnt = Math.min(cnt, len - (start - ptr)); if (cnt <= 0) return null;
  b = AC.createBuffer(1, cnt, rate); const d = b.getChannelData(0), m = u8();
  for (let i = 0; i < cnt; i++) d[i] = (m[start + i] - 128) / 128;
  sfxCache.set(lump, b); return b;
}
function sfxStop(ch) { const c = chans[ch]; if (c) { try { c.src.stop(); } catch (e) {} chans[ch] = null; } }
const env = {
  js_ticks: () => (performance.now() | 0) >>> 0,
  js_title: (p) => { document.title = 'CLASS BUSTER — ' + cstr(p); },
  js_draw(ptr, w, h) {
    if (!img || canvas.width !== w) { canvas.width = w; canvas.height = h; img = ctx2d.createImageData(w, h); px = new Uint32Array(img.data.buffer); }
    const src = new Uint32Array(mem.buffer, ptr, w * h);
    for (let i = 0; i < src.length; i++) { const p = src[i]; px[i] = 0xff000000 | ((p & 0xff) << 16) | (p & 0xff00) | ((p >>> 16) & 0xff); }
    ctx2d.putImageData(img, 0, 0);
  },
  js_sfx_start(ch, lump, ptr, len, vol, sep) {
    if (!AC) return; sfxStop(ch);
    const buf = sfxBuffer(lump, ptr, len); if (!buf) return;
    const src = AC.createBufferSource(); src.buffer = buf;
    const g = AC.createGain(); g.gain.value = vol / 127;
    const pan = AC.createStereoPanner(); pan.pan.value = Math.max(-1, Math.min(1, (sep - 128) / 127));
    src.connect(g); g.connect(pan); pan.connect(sfxBus);
    const c = { src, g, pan, done: false }; src.onended = () => { c.done = true; };
    src.start(); chans[ch] = c;
  },
  js_sfx_update(ch, vol, sep) { const c = chans[ch]; if (!c) return; c.g.gain.value = vol / 127; c.pan.pan.value = Math.max(-1, Math.min(1, (sep - 128) / 127)); },
  js_sfx_stop: (ch) => sfxStop(ch),
  js_sfx_playing: (ch) => (chans[ch] && !chans[ch].done ? 1 : 0),
  js_mus_play(ptr, len, loop) { if (AC) Synth.play(u8().slice(ptr, ptr + len), !!loop); },
  js_mus_stop() { Synth.stop(); },
  js_mus_volume(v) { if (musBus) musBus.gain.value = 0.5 * v / 127; },
  js_mus_pause(p) { Synth.pause(!!p); },
};
let img = null, px = null;

/* ------------------------------------------------------------------ General MIDI synth */
const Synth = (() => {
  let events = [], loop = true, idx = 0, t0 = 0, timer = null, songLen = 0, paused = false, pauseAt = 0;
  const ch = [], voices = new Set();
  let noiseBuf = null, distCurve = null;
  function init() {
    noiseBuf = AC.createBuffer(1, AC.sampleRate, AC.sampleRate);
    const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    distCurve = new Float32Array(1024); for (let i = 0; i < 1024; i++) { const x = i / 512 - 1; distCurve[i] = Math.tanh(x * 6) * 0.9; }
  }
  function resetCh() { for (let i = 0; i < 16; i++) ch[i] = { prog: 0, vol: 100 / 127, expr: 1, pan: 0, bend: 0, notes: new Map() }; }
  function parse(d) {
    const v = new DataView(d.buffer, d.byteOffset, d.byteLength);
    if (dec.decode(d.subarray(0, 4)) !== 'MThd') return null;
    const ntr = v.getUint16(10), div = v.getUint16(12); let p = 8 + v.getUint32(4);
    const evs = [];
    for (let t = 0; t < ntr && p < d.length; t++) {
      const len = v.getUint32(p + 4); let q = p + 8; const end = q + len; p = end;
      let tick = 0, run = 0;
      const vlq = () => { let r = 0, b; do { b = d[q++]; r = (r << 7) | (b & 0x7f); } while (b & 0x80 && q < end); return r; };
      while (q < end) {
        tick += vlq(); let st = d[q];
        if (st & 0x80) q++; else st = run;
        const ty = st & 0xf0;
        if (st === 0xff) { const mt = d[q++]; const l = vlq(); if (mt === 0x51) evs.push({ tick, type: 'tempo', v: (d[q] << 16) | (d[q + 1] << 8) | d[q + 2] }); if (mt === 0x2f) { q = end; break; } q += l; continue; }
        if (st === 0xf0 || st === 0xf7) { q += vlq(); continue; }
        run = st; const c = st & 15;
        if (ty === 0xc0 || ty === 0xd0) { evs.push({ tick, type: ty, c, a: d[q++] }); }
        else { evs.push({ tick, type: ty, c, a: d[q++], b: d[q++] }); }
      }
    }
    evs.sort((a, b) => a.tick - b.tick);
    let tempo = 500000, lastTick = 0, sec = 0;
    for (const e of evs) { sec += (e.tick - lastTick) * tempo / 1e6 / div; lastTick = e.tick; e.t = sec; if (e.type === 'tempo') tempo = e.v; }
    return { evs, len: sec };
  }
  const freq = (n) => 440 * Math.pow(2, (n - 69) / 12);
  function family(p) {
    if (p < 8) return 'piano'; if (p < 16) return 'bell'; if (p < 24) return 'organ'; if (p < 29) return 'guitar';
    if (p < 32) return 'dist'; if (p < 40) return 'bass'; if (p < 56) return 'strings'; if (p < 64) return 'brass';
    if (p < 80) return 'pipe'; if (p < 88) return 'lead'; if (p < 104) return 'pad'; return 'lead';
  }
  function noteOn(c, n, vel, t) {
    const C = ch[c]; noteOff(c, n, t);
    const out = AC.createGain(); const pan = AC.createStereoPanner(); pan.pan.value = C.pan; out.connect(pan); pan.connect(musBus);
    const amp = (vel / 127) * C.vol * C.expr;
    const v = { c, n, out, oscs: [], rel: 0.15, perc: c === 9 };
    if (c === 9) { drum(n, amp, t, out); v.end = t + 1.2; voices.add(v); setTimeout(() => voices.delete(v), 1600); return; }
    const fam = family(C.prog), f = freq(n + C.bend);
    const mk = (type, fr, det = 0) => { const o = AC.createOscillator(); o.type = type; o.frequency.value = fr; o.detune.value = det; v.oscs.push(o); return o; };
    const g = out.gain; let a = 0.005, dcy = 0.3, sus = 0.6, peak = 0.22 * amp; let chain = out;
    const lp = AC.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 1; lp.connect(out);
    switch (fam) {
      case 'dist': { const ws = AC.createWaveShaper(); ws.curve = distCurve; const pre = AC.createGain(); pre.gain.value = 2.5;
        lp.frequency.value = 2600; ws.connect(lp); pre.connect(ws); mk('sawtooth', f, -8).connect(pre); mk('square', f, 8).connect(pre); mk('sawtooth', f / 2).connect(pre);
        peak = 0.12 * amp; sus = 0.8; dcy = 0.4; v.rel = 0.08; break; }
      case 'guitar': lp.frequency.value = 2200; mk('sawtooth', f).connect(lp); mk('triangle', f * 2).connect(lp); sus = 0.15; dcy = 0.8; break;
      case 'bass': lp.frequency.value = 900; mk('sawtooth', f).connect(lp); mk('triangle', f).connect(lp); peak = 0.3 * amp; sus = 0.5; dcy = 0.5; v.rel = 0.06; break;
      case 'piano': lp.frequency.value = 3000; mk('triangle', f).connect(lp); mk('square', f * 2).connect(lp); sus = 0.05; dcy = 1.2; peak = 0.18 * amp; break;
      case 'bell': lp.frequency.value = 6000; mk('sine', f).connect(lp); mk('sine', f * 3.5).connect(lp); sus = 0; dcy = 1.5; break;
      case 'organ': lp.frequency.value = 3500; mk('square', f).connect(lp); mk('sine', f * 2).connect(lp); sus = 0.9; peak = 0.12 * amp; break;
      case 'strings': lp.frequency.value = 2400; mk('sawtooth', f, -7).connect(lp); mk('sawtooth', f, 7).connect(lp); a = 0.12; sus = 0.85; peak = 0.11 * amp; v.rel = 0.4; break;
      case 'brass': lp.frequency.value = 2000; mk('sawtooth', f).connect(lp); a = 0.04; sus = 0.8; peak = 0.16 * amp; break;
      case 'pipe': lp.frequency.value = 4000; mk('sine', f).connect(lp); mk('triangle', f * 2).connect(lp); a = 0.03; sus = 0.8; peak = 0.15 * amp; break;
      case 'pad': lp.frequency.value = 1800; mk('sawtooth', f, -10).connect(lp); mk('triangle', f, 10).connect(lp); a = 0.3; sus = 0.9; peak = 0.1 * amp; v.rel = 0.8; break;
      default: lp.frequency.value = 3200; mk('square', f).connect(lp); sus = 0.7; peak = 0.12 * amp;
    }
    g.setValueAtTime(0, t); g.linearRampToValueAtTime(peak, t + a); g.setTargetAtTime(peak * sus, t + a, dcy / 3);
    v.oscs.forEach((o) => o.start(t));
    C.notes.set(n, v); voices.add(v);
    if (voices.size > 48) { const old = voices.values().next().value; kill(old, AC.currentTime); }
  }
  function kill(v, t) { voices.delete(v); try { v.out.gain.cancelScheduledValues(t); v.out.gain.setTargetAtTime(0, t, 0.01); v.oscs.forEach((o) => o.stop(t + 0.1)); } catch (e) {} }
  function noteOff(c, n, t) {
    const C = ch[c]; const v = C.notes.get(n); if (!v) return; C.notes.delete(n);
    try { v.out.gain.cancelScheduledValues(t); v.out.gain.setTargetAtTime(0, t, v.rel / 3); v.oscs.forEach((o) => o.stop(t + v.rel * 2 + 0.05)); } catch (e) {}
    setTimeout(() => voices.delete(v), (t - AC.currentTime + v.rel * 2) * 1000 + 200);
  }
  function drum(n, amp, t, out) {
    const g = out.gain; const nz = () => { const s = AC.createBufferSource(); s.buffer = noiseBuf; return s; };
    const osc = (fr) => { const o = AC.createOscillator(); o.frequency.value = fr; return o; };
    if (n === 35 || n === 36) { const o = osc(150); o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(40, t + 0.12); o.connect(out);
      g.setValueAtTime(0.9 * amp, t); g.exponentialRampToValueAtTime(0.001, t + 0.25); o.start(t); o.stop(t + 0.3); }
    else if (n === 38 || n === 40 || n === 37 || n === 39) { const s = nz(); const bp = AC.createBiquadFilter(); bp.type = 'highpass'; bp.frequency.value = 1200; s.connect(bp); bp.connect(out);
      const o = osc(200); o.type = 'triangle'; o.connect(out); g.setValueAtTime(0.5 * amp, t); g.exponentialRampToValueAtTime(0.001, t + 0.18); s.start(t); s.stop(t + 0.2); o.start(t); o.stop(t + 0.1); }
    else if (n === 42 || n === 44 || n === 46) { const s = nz(); const hp = AC.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 7000; s.connect(hp); hp.connect(out);
      const d = n === 46 ? 0.25 : 0.05; g.setValueAtTime(0.25 * amp, t); g.exponentialRampToValueAtTime(0.001, t + d); s.start(t); s.stop(t + d + 0.02); }
    else if (n === 49 || n === 51 || n === 52 || n === 55 || n === 57 || n === 59) { const s = nz(); const hp = AC.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 4500; s.connect(hp); hp.connect(out);
      g.setValueAtTime(0.25 * amp, t); g.exponentialRampToValueAtTime(0.001, t + 1.0); s.start(t); s.stop(t + 1.05); }
    else { const fr = 80 + (n - 41) * 12; const o = osc(fr * 1.6); o.frequency.exponentialRampToValueAtTime(fr, t + 0.15); o.connect(out);
      g.setValueAtTime(0.5 * amp, t); g.exponentialRampToValueAtTime(0.001, t + 0.3); o.start(t); o.stop(t + 0.32); }
  }
  function apply(e, t) {
    const C = ch[e.c];
    switch (e.type) {
      case 0x90: if (e.b) noteOn(e.c, e.a, e.b, t); else noteOff(e.c, e.a, t); break;
      case 0x80: noteOff(e.c, e.a, t); break;
      case 0xc0: C.prog = e.a; break;
      case 0xe0: C.bend = (((e.b << 7) | e.a) - 8192) / 4096; break;
      case 0xb0:
        if (e.a === 7) C.vol = e.b / 127; else if (e.a === 11) C.expr = e.b / 127; else if (e.a === 10) C.pan = (e.b - 64) / 64;
        else if (e.a === 123 || e.a === 120) { C.notes.forEach((v, n) => noteOff(e.c, n, t)); }
        break;
    }
  }
  function pump() {
    if (paused || !events.length) return;
    const now = AC.currentTime, horizon = now + 0.25;
    while (true) {
      if (idx >= events.length) { if (!loop) return; t0 += songLen; idx = 0; allOff(t0); }
      const e = events[idx]; const t = t0 + e.t; if (t > horizon) break;
      apply(e, Math.max(t, now)); idx++;
    }
  }
  function allOff(t) { ch.forEach((C, c) => C.notes.forEach((v, n) => noteOff(c, n, t))); }
  function stop() { if (timer) clearInterval(timer); timer = null; events = []; if (AC) { voices.forEach((v) => kill(v, AC.currentTime)); } if (ch.length) allOff(AC ? AC.currentTime : 0); }
  function play(data, lp) {
    stop(); const s = parse(data); if (!s || !s.evs.length) return;
    resetCh(); events = s.evs; songLen = Math.max(s.len, 0.5); loop = lp; idx = 0; paused = false; t0 = AC.currentTime + 0.1;
    timer = setInterval(pump, 40); pump();
  }
  function pause(p) {
    if (!AC || p === paused) return; paused = p;
    if (p) { pauseAt = AC.currentTime; voices.forEach((v) => kill(v, AC.currentTime)); ch.forEach((C) => C.notes.clear()); }
    else { t0 += AC.currentTime - pauseAt; }
  }
  resetCh();
  return { init, play, stop, pause };
})();

/* ------------------------------------------------------------------ input */
const K = { RIGHT: 0xae, LEFT: 0xac, UP: 0xad, DOWN: 0xaf, USE: 0xa2, FIRE: 0xa3, ESC: 27, ENTER: 13, TAB: 9, BKSP: 0x7f, PAUSE: 0xff, RSHIFT: 0x80 + 0x36, RCTRL: 0x80 + 0x1d, RALT: 0x80 + 0x38 };
const FK = [0x3b, 0x3c, 0x3d, 0x3e, 0x3f, 0x40, 0x41, 0x42, 0x43, 0x44, 0x57, 0x58];
function mapKey(e) {
  const c = e.code;
  if (/^Key[A-Z]$/.test(c)) return c.charCodeAt(3) + 32;
  if (/^Digit[0-9]$/.test(c)) return c.charCodeAt(5);
  if (/^Numpad[0-9]$/.test(c)) return c.charCodeAt(6);
  if (/^F([1-9]|1[0-2])$/.test(c)) return 0x80 + FK[+c.slice(1) - 1];
  switch (c) {
    case 'ArrowRight': return K.RIGHT; case 'ArrowLeft': return K.LEFT; case 'ArrowUp': return K.UP; case 'ArrowDown': return K.DOWN;
    case 'Space': return 32; case 'Enter': case 'NumpadEnter': return K.ENTER; case 'Escape': return K.ESC; case 'Tab': return K.TAB;
    case 'Backspace': return K.BKSP; case 'Pause': return K.PAUSE;
    case 'ShiftLeft': case 'ShiftRight': return K.RSHIFT;
    case 'ControlLeft': case 'ControlRight': return K.FIRE;
    case 'AltLeft': case 'AltRight': return K.RALT;
    case 'Minus': case 'NumpadSubtract': return 0x2d; case 'Equal': case 'NumpadAdd': return 0x3d;
    case 'Comma': return 44; case 'Period': return 46; case 'Slash': return 47; case 'Semicolon': return 59; case 'Quote': return 39;
    case 'BracketLeft': return 91; case 'BracketRight': return 93; case 'Backquote': return 96; case 'Backslash': return 92;
  }
  return 0;
}
const held = new Set();
addEventListener('keydown', (e) => {
  if (!started) return; const k = mapKey(e); if (!k) return;
  e.preventDefault(); if (e.repeat) return; held.add(k); ex.dg_key(1, k);
  if (e.code === 'Escape' && document.pointerLockElement) {/* browser releases lock itself */}
});
addEventListener('keyup', (e) => { if (!started) return; const k = mapKey(e); if (!k) return; e.preventDefault(); held.delete(k); ex.dg_key(0, k); });
addEventListener('blur', () => { if (!started) return; held.forEach((k) => ex.dg_key(0, k)); held.clear(); });
let mdx = 0, mbtn = 0, mDirty = false;
const sens = () => +($('sens').value || 4);
canvas.addEventListener('mousedown', (e) => {
  if (!started) return;
  if (document.pointerLockElement !== canvas) { canvas.requestPointerLock(); return; }
  mbtn |= [1, 4, 2][e.button] || 0; mDirty = true; e.preventDefault();
});
addEventListener('mouseup', (e) => { mbtn &= ~([1, 4, 2][e.button] || 0); mDirty = true; });
canvas.addEventListener('contextmenu', (e) => e.preventDefault());
addEventListener('mousemove', (e) => { if (document.pointerLockElement === canvas) { mdx += e.movementX; mDirty = true; } });
canvas.addEventListener('wheel', (e) => { if (!started) return; e.preventDefault(); }, { passive: false });
document.addEventListener('pointerlockchange', () => { document.body.classList.toggle('locked', document.pointerLockElement === canvas); if (!document.pointerLockElement && mbtn) { mbtn = 0; mDirty = true; } });

/* ------------------------------------------------------------------ main loop */
let lastTic = -1;
function frame() {
  requestAnimationFrame(frame);
  if (!started) return;
  try {
    if (mDirty) { const dx = Math.round(mdx * sens()); mdx = 0; mDirty = false; ex.dg_mouse(mbtn, dx, 0); }
    const tic = Math.floor(performance.now() * 35 / 1000);
    if (tic !== lastTic) { lastTic = tic; ex.dg_tick(); }
  } catch (e) { crash(e); }
}
function crash(e) {
  started = false;
  const msg = e instanceof Exit ? (e.code === 0 ? '게임을 종료했습니다. 다시 하려면 새로고침하세요.' : '엔진 오류: ' + logBuf) : String(e && e.stack || e);
  overlay.classList.remove('hidden'); $('start').style.display = 'none'; statusEl.textContent = msg; console.error(e);
}

async function fetchWithProgress(url) {
  const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status);
  const total = +r.headers.get('content-length') || 0; const reader = r.body.getReader(); const parts = []; let got = 0;
  for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); got += value.length;
    if (total) barEl.style.width = (100 * got / total).toFixed(1) + '%'; }
  const out = new Uint8Array(got); let o = 0; for (const p of parts) { out.set(p, o); o += p.length; } return out;
}
async function boot() {
  try {
    statusEl.textContent = '교실을 불러오는 중…';
    const [wad, wasmBytes] = await Promise.all([fetchWithProgress('classbuster.wad'), fetch('classbuster.wasm').then((r) => r.arrayBuffer())]);
    files.set('classbuster.wad', { data: wad, size: wad.length });
    loadPersisted();
    const { instance } = await WebAssembly.instantiate(wasmBytes, { env, wasi_snapshot_preview1: wasi });
    inst = instance; ex = instance.exports; mem = ex.memory;
    if (ex._initialize) ex._initialize();
    barEl.style.width = '100%'; statusEl.textContent = '준비 완료'; $('start').disabled = false; $('start').focus();
  } catch (e) {
    statusEl.textContent = '불러오기 실패: ' + e.message + (location.protocol === 'file:' ? ' — 파일을 직접 열면 동작하지 않습니다. GitHub Pages나 로컬 서버(python -m http.server)로 여세요.' : '');
  }
}
$('start').addEventListener('click', () => {
  if (started || !ex) return;
  initAudio(); overlay.classList.add('hidden'); started = true; canvas.focus();
  canvas.requestPointerLock && canvas.requestPointerLock();
  try { ex.dg_start(0, 0); } catch (e) { crash(e); }
});
$('fs').addEventListener('click', () => { const w = $('wrap'); (w.requestFullscreen || w.webkitRequestFullscreen).call(w); });
window.__cb = { files, get ex() { return ex; }, key: (p, k) => ex.dg_key(p, k), mouse: (b, dx) => ex.dg_mouse(b, dx, 0) };
requestAnimationFrame(frame);
boot();
})();
