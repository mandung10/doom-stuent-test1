#!/bin/sh
# Build engine/*.c → classbuster.wasm  (needs zig: pip install ziglang)
set -e
cd "$(dirname "$0")/engine"
ZIGCC="${ZIGCC:-python3 -m ziglang cc}"
$ZIGCC -target wasm32-wasi -O2 -mexec-model=reactor -DFEATURE_SOUND -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS \
  -Wno-everything -lwasi-emulated-signal -lwasi-emulated-process-clocks \
  -Wl,--export=malloc -Wl,--export=free -Wl,--initial-memory=134217728 -Wl,--max-memory=268435456 \
  $(ls *.c) -o ../classbuster.wasm
echo built classbuster.wasm
