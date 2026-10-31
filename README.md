# 교실 대소동 : CLASS BUSTER

학생용 **비잔혹 DOOM 개조판**입니다. 실제 DOOM 엔진(Chocolate Doom 기반 doomgeneric)을 WebAssembly로 컴파일해 브라우저에서 그대로 실행합니다.
이동감·무기·적 AI·문/리프트/비밀 통로·상태바·자동지도·메뉴·저장/불러오기·결과 화면·치트까지 원작 코드 그대로 동작합니다.

## GitHub Pages로 바로 플레이하기
1. 이 폴더의 **내용물 전체**를 새 저장소의 최상위에 올립니다 (`index.html`이 저장소 루트에 있어야 함).
2. 저장소 **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`** 를 선택하고 저장합니다.
3. 1~2분 뒤 `https://<아이디>.github.io/<저장소이름>/` 에서 플레이합니다.

> `index.html`을 파일 탐색기에서 더블클릭하면 실행되지 않습니다 (브라우저 보안 정책).
> 로컬 테스트: 이 폴더에서 `python3 -m http.server` 실행 후 `http://localhost:8000` 접속.

`classbuster.wad`는 약 28MB로 GitHub 일반 업로드 한도(100MB) 안입니다. 웹 화면 드래그 업로드는 파일당 25MB 제한이 있으므로 **git 명령어** 또는 **GitHub Desktop**으로 올리세요.

```bash
git init && git add . && git commit -m "CLASS BUSTER"
git branch -M main
git remote add origin https://github.com/<아이디>/<저장소이름>.git
git push -u origin main
```

## 조작
| 키 | 기능 |
|---|---|
| W A S D / ↑ ↓ | 이동·옆걸음 / 전진·후진 |
| 마우스 (화면 클릭 시 고정), ← → | 회전 |
| 클릭 · Ctrl | 발사 |
| Space · E | 문·스위치·리프트 |
| Shift | 달리기 |
| 1–7 | 무기 |
| Tab | 자동지도 |
| Esc | 메뉴 / F2 저장 / F3 불러오기 |

## 비잔혹 대체 내용
| 원작 | 교실 대소동 |
|---|---|
| 좀비맨·샷건가이·임프·데몬 | 계산기 로봇 · 영어 사전병 · 과학 플라스크 · 체육 농구공 |
| 로스트소울·카코데몬·바론 | 음표 · 외눈 지구본 · 돌하르방 |
| 사이버데몬·스파이더 마스터마인드 | 기말고사 거인 · 채점기 거미 |
| 사망 | 기절해 쓰러지고 머리 위에 별이 돎 |
| 폭발 사망(고어) | 시험지·색종이로 흩어지고 종이 더미가 남음 |
| 피 튀김 / 피 웅덩이 | 분필 가루 / 물감 |
| 시체·해골 장식 | 깃발·트로피·책 더미·등·현수막·모빌·메달 |
| 피 텍스처 / 시체 벽 / 해골 스위치 | 파란 잉크 / 게시판 / 레버 스위치 |
| 상태바 얼굴의 피 | 땀·반창고·어지러움, 쓰러지면 잠든 얼굴 |
| 비명 효과음 | 기절·종이 터짐 효과음 |

메뉴·난이도·학기·레벨 이름·결과 화면·타이틀·도움말·엔딩은 한글 그래픽으로 교체했습니다.
화면 위쪽 짧은 획득 메시지와 자동지도 레벨명은 엔진 글꼴 한계로 영어로 표시됩니다.

## 폴더 구성
- `index.html`, `runtime.js`, `classbuster.wasm`, `classbuster.wad` — 실행 파일 (이것만 있으면 플레이 가능)
- `engine/` — 수정한 엔진 C 소스 (`doomgeneric_web.c`가 브라우저 연결부)
- `tools/` — 그래픽·사운드 교체 도구 (`build_wad.py`, `art3d.py`, `art2d.py` 등)
- `build.sh` — 엔진 다시 빌드 (`pip install ziglang` 필요)

다시 만들기:
```bash
./build.sh                                                   # → classbuster.wasm
cd tools && python3 build_wad.py freedoom1.wad ../classbuster.wad   # numpy, pillow, 나눔 글꼴 필요
```

## 라이선스
- 엔진: DOOM 소스(© id Software), Chocolate Doom, doomgeneric — **GNU GPL v2** (`LICENSE`). 이 저장소의 코드도 GPL v2입니다.
- 게임 데이터 원본: **Freedoom** (BSD 계열, `COPYING-FREEDOOM.txt`). 원작 DOOM의 상용 데이터는 포함하지 않습니다.
- 맵 구조는 Freedoom Phase 1을 사용하며, 과목 몬스터·얼굴·한글 그래픽·효과음은 이 프로젝트에서 새로 제작했습니다.
