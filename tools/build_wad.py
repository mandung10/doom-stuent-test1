#!/usr/bin/env python3
"""Build web/classbuster.wad from Freedoom (Phase 1) + CLASS BUSTER replacement art.
usage: python3 tools/build_wad.py path/to/freedoom1.wad web/classbuster.wad"""
import sys, time
import numpy as np
from wadlib import Wad, Palette, picture_from_rgba
import art2d as A2
import art3d as A3

MENU = {
    'M_NGAME': '새 게임', 'M_OPTION': '설정', 'M_LOADG': '불러오기', 'M_SAVEG': '저장하기',
    'M_RDTHIS': '도움말', 'M_QUITG': '그만하기', 'M_NEWG': '새 게임', 'M_SKILL': '난이도를 고르시오:',
    'M_EPISOD': '학기를 고르시오:', 'M_JKILL': '연습 문제', 'M_ROUGH': '쪽지 시험', 'M_HURT': '중간고사',
    'M_ULTRA': '기말고사', 'M_NMARE': '수능 지옥!', 'M_EPI1': '1학기: 본관 대소동', 'M_EPI2': '2학기: 과학관 폭주',
    'M_EPI3': '3학기: 시험장 지옥', 'M_EPI4': '4학기: 방학은 없다', 'M_PAUSE': '일시정지', 'M_ENDGAM': '게임 끝내기',
    'M_MESSG': '메시지:', 'M_MSGON': '켬', 'M_MSGOFF': '끔', 'M_DETAIL': '화질:', 'M_GDHIGH': '높음',
    'M_GDLOW': '낮음', 'M_SCRNSZ': '화면 크기', 'M_MSENS': '마우스 감도', 'M_SVOL': '소리 크기',
    'M_SFXVOL': '효과음', 'M_MUSVOL': '배경음악', 'M_OPTTTL': '설정', 'M_SGTTL': '저장하기', 'M_LGTTL': '불러오기',
    'M_DISOPT': '화면 설정', 'M_SOUND': '소리',
}
TITLES = {'M_OPTTTL', 'M_SGTTL', 'M_LGTTL', 'M_NEWG', 'M_PAUSE'}
LEVELS = [
    ['교문 앞', '1층 복도', '교무실', '컴퓨터실', '급식실', '도서관', '강당', '옥상', '비밀 창고'],
    ['과학관 입구', '화학 실험실', '생물실', '물리실', '천체 관측실', '온실', '준비실', '지하 보일러실', '비밀 표본실'],
    ['시험장 복도', '문제 은행', '채점실', '성적 처리실', '답안지 창고', '감독관실', '시험 본부', '최후의 시험장', '비밀 오답 노트'],
    ['보충 수업', '학원가', '독서실', '야간 자습실', '모의고사장', '체육관', '운동장', '졸업식장', '비밀 동아리방'],
]
WI = {'WIF': '완료!', 'WIENTER': '다음 장소', 'WIOSTK': '처치', 'WIOSTI': '아이템', 'WISCRT2': '비밀',
      'WIOSTS': '비밀', 'WITIME': '시간', 'WIPAR': '기준', 'WISUCKS': '많이 걸림', 'WIMSTT': '총계', 'WIFRGS': '점수'}


def main(src, dst):
    t0 = time.time()
    w = Wad(src)
    pal = Palette(w.get('PLAYPAL'))
    have = set(w.names())

    def put(name, data):
        if name in have:
            w.set(name, data)

    # ---- menu graphics
    for k, txt in MENU.items():
        if k not in have:
            continue
        size = 17 if k in TITLES else 14
        data, tw, th = A2.patch_text(pal, txt, size)
        put(k, data)
    logo = A2.logo_rgba(0.82)
    put('M_DOOM', picture_from_rgba(pal, logo, logo.shape[1] // 2 - 66, 0, 110))
    # ---- intermission
    for e, names in enumerate(LEVELS):
        for m, nm in enumerate(names):
            data, _, _ = A2.patch_text(pal, nm, 16)
            put(f'WILV{e}{m}', data)
    for k, txt in WI.items():
        data, _, _ = A2.patch_text(pal, txt, 15)
        put(k, data)
    star = A2.text_rgba('★', 16, A2.GOLD, A2.FONT_HEAVY, stroke=1, outline='#402000', shadow=0)
    put('WISPLAT', picture_from_rgba(pal, star, star.shape[1] // 2, star.shape[0] // 2, 110))
    # ---- full screens
    put('TITLEPIC', A2.full_rgb_to_pic(pal, A2.titlepic()))
    hp = A2.full_rgb_to_pic(pal, A2.help_screen())
    put('HELP1', hp); put('HELP2', hp); put('HELP', hp)
    put('CREDIT', A2.full_rgb_to_pic(pal, A2.credit_screen()))
    put('VICTORY2', A2.full_rgb_to_pic(pal, A2.ending_screen('VICTORY2')))
    put('ENDPIC', A2.full_rgb_to_pic(pal, A2.ending_screen('ENDPIC')))
    put('PFUB1', A2.full_rgb_to_pic(pal, A2.panorama(1)))
    put('PFUB2', A2.full_rgb_to_pic(pal, A2.panorama(0)))
    print('menus/screens', round(time.time() - t0, 1), 's')
    # ---- faces, walls, sounds, sprites
    print('faces', A2.build_faces(w, pal))
    print('walls/flats', A2.build_walls(w, pal))
    for k, data in A2.sounds().items():
        put(k, data)
    print('sounds done')
    A3.build_sprites(w, pal)
    w.save(dst)
    print('wrote', dst, round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
