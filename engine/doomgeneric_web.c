// CLASS BUSTER — browser platform layer for doomgeneric (GPLv2)
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "doomgeneric.h"
#include "doomkeys.h"
#include "d_event.h"
#include "i_sound.h"
#include "w_wad.h"
#include "z_zone.h"
#include "memio.h"
#include "mus2mid.h"

#define IMPORT(n) __attribute__((import_module("env"), import_name(#n)))
#define EXPORT(n) __attribute__((export_name(#n)))

IMPORT(js_ticks) unsigned int js_ticks(void);
IMPORT(js_draw) void js_draw(void *buf, int w, int h);
IMPORT(js_title) void js_title(const char *s);
IMPORT(js_sfx_start) void js_sfx_start(int ch, int lump, const void *data, int len, int vol, int sep);
IMPORT(js_sfx_update) void js_sfx_update(int ch, int vol, int sep);
IMPORT(js_sfx_stop) void js_sfx_stop(int ch);
IMPORT(js_sfx_playing) int js_sfx_playing(int ch);
IMPORT(js_mus_play) void js_mus_play(const void *data, int len, int loop);
IMPORT(js_mus_stop) void js_mus_stop(void);
IMPORT(js_mus_volume) void js_mus_volume(int v);
IMPORT(js_mus_pause) void js_mus_pause(int p);

#define KQ 256
static unsigned short kq[KQ]; static unsigned kqr, kqw;

EXPORT(dg_key) void dg_key(int pressed, int key) {
  kq[kqw++ % KQ] = (unsigned short)((pressed ? 0x100 : 0) | (key & 0xff));
}
EXPORT(dg_mouse) void dg_mouse(int buttons, int dx, int dy) {
  event_t ev; ev.type = ev_mouse; ev.data1 = buttons; ev.data2 = dx; ev.data3 = dy; ev.data4 = 0;
  D_PostEvent(&ev);
}
static char *argv_store[16]; 
EXPORT(dg_start) void dg_start(int skill, int warp) {
  static char a0[]="classbuster", a1[]="-iwad", a2[]="classbuster.wad";
  int n = 0; argv_store[n++]=a0; argv_store[n++]=a1; argv_store[n++]=a2;
  doomgeneric_Create(n, argv_store);
}
EXPORT(dg_tick) void dg_tick(void) { doomgeneric_Tick(); }

void DG_Init() {}
void DG_DrawFrame() { js_draw(DG_ScreenBuffer, DOOMGENERIC_RESX, DOOMGENERIC_RESY); }
void DG_SleepMs(uint32_t ms) { (void)ms; }
uint32_t DG_GetTicksMs() { return js_ticks(); }
int DG_GetKey(int *pressed, unsigned char *key) {
  if (kqr == kqw) return 0;
  unsigned short v = kq[kqr++ % KQ]; *pressed = v >> 8; *key = v & 0xff; return 1;
}
void DG_SetWindowTitle(const char *t) { js_title(t); }

// ---------------- sound ----------------
static snddevice_t snd_devs[] = { SNDDEVICE_SB, SNDDEVICE_PAS, SNDDEVICE_GUS, SNDDEVICE_WAVEBLASTER, SNDDEVICE_SOUNDCANVAS, SNDDEVICE_AWE32 };
static boolean use_prefix;
static boolean W_Init(boolean p) { use_prefix = p; return true; }
static void W_Shutdown(void) {}
static int W_GetLump(sfxinfo_t *sfx) {
  char nb[16];
  if (sfx->link) sfx = sfx->link;
  if (use_prefix) snprintf(nb, sizeof nb, "ds%s", sfx->name); else snprintf(nb, sizeof nb, "%s", sfx->name);
  return W_CheckNumForName(nb);
}
static void W_Update(void) {}
static void W_UpdateParams(int ch, int vol, int sep) { js_sfx_update(ch, vol, sep); }
static int W_Start(sfxinfo_t *sfx, int ch, int vol, int sep) {
  int lump = sfx->lumpnum;
  if (lump < 0) return -1;
  byte *d = W_CacheLumpNum(lump, PU_STATIC);
  int len = W_LumpLength(lump);
  js_sfx_start(ch, lump, d, len, vol, sep);
  return ch;
}
static void W_Stop(int ch) { js_sfx_stop(ch); }
static boolean W_Playing(int ch) { return js_sfx_playing(ch) ? true : false; }
static void W_Cache(sfxinfo_t *s, int n) { (void)s; (void)n; }
sound_module_t DG_sound_module = { snd_devs, sizeof(snd_devs)/sizeof(*snd_devs), W_Init, W_Shutdown, W_GetLump, W_Update, W_UpdateParams, W_Start, W_Stop, W_Playing, W_Cache };

// ---------------- music (MIDI → JS synth) ----------------
typedef struct { void *data; int len; } song_t;
static boolean M_Init(void) { return true; }
static void M_Shutdown(void) { js_mus_stop(); }
static void M_Vol(int v) { js_mus_volume(v); }
static void M_Pause(void) { js_mus_pause(1); }
static void M_Resume(void) { js_mus_pause(0); }
static void *M_Register(void *data, int len) {
  song_t *s = malloc(sizeof *s);
  if (len > 4 && !memcmp(data, "MUS\x1a", 4)) {
    MEMFILE *in = mem_fopen_read(data, len), *out = mem_fopen_write();
    void *buf; size_t blen;
    if (mus2mid(in, out)) { mem_fclose(in); mem_fclose(out); free(s); return NULL; }
    mem_get_buf(out, &buf, &blen);
    s->data = malloc(blen); memcpy(s->data, buf, blen); s->len = (int)blen;
    mem_fclose(in); mem_fclose(out);
  } else { s->data = malloc(len); memcpy(s->data, data, len); s->len = len; }
  return s;
}
static void M_Unregister(void *h) { song_t *s = h; if (s) { free(s->data); free(s); } }
static void M_Play(void *h, boolean loop) { song_t *s = h; if (s) js_mus_play(s->data, s->len, loop); }
static void M_Stop(void) { js_mus_stop(); }
static boolean M_Playing(void) { return true; }
static void M_Poll(void) {}
music_module_t DG_music_module = { snd_devs, sizeof(snd_devs)/sizeof(*snd_devs), M_Init, M_Shutdown, M_Vol, M_Pause, M_Resume, M_Register, M_Unregister, M_Play, M_Stop, M_Playing, M_Poll };
int use_libsamplerate = 0;
float libsamplerate_scale = 0.65f;
int system(const char *c) { (void)c; return -1; }
