# -*- coding: utf-8 -*-
# 20강 마스코트 단계 이미지를 일관된 캐릭터로 생성한다.
# 규칙: step1에서 더한 '달리는 자세'와 눈 모양은 이후 모든 단계에서 유지되고,
#       각 단계는 요소(모자→배지→가방→스타일)만 하나씩 추가한다.
import os

OUT = os.path.join(os.path.dirname(__file__), 'svg')
os.makedirs(OUT, exist_ok=True)

INK = '#141414'
FUR = '#F5A24B'
FUR_DK = '#E0892F'
CREAM = '#FBF1E0'
BRIGHT = '#FFF3C4'
HAT = '#D8C089'
BAND = '#8B6F47'
BAG = '#C4813C'
STRAP = '#8A5A2B'
STAR = '#FFD93B'
PINK = '#F9B8C4'

def capsule(x1, y1, x2, y2, w, color):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w-9}" stroke-linecap="round"/>')

def curve(d, w, color):
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w-9}" stroke-linecap="round"/>')

def star_pts(cx, cy, R, r):
    import math
    pts = []
    for i in range(10):
        rad = math.pi / 5 * i - math.pi / 2
        rr = R if i % 2 == 0 else r
        pts.append(f'{cx + rr * math.cos(rad):.1f},{cy + rr * math.sin(rad):.1f}')
    return ' '.join(pts)

def sparkle(cx, cy, s):
    return (f'<path d="M{cx},{cy-s} Q{cx+s*0.18},{cy-s*0.18} {cx+s},{cy} Q{cx+s*0.18},{cy+s*0.18} {cx},{cy+s} '
            f'Q{cx-s*0.18},{cy+s*0.18} {cx-s},{cy} Q{cx-s*0.18},{cy-s*0.18} {cx},{cy-s} Z" '
            f'fill="{STAR}" stroke="{INK}" stroke-width="4"/>')

def bg(color):
    return (f'<rect width="400" height="400" fill="#FFFEF9"/>'
            f'<circle cx="200" cy="200" r="172" fill="{color}" stroke="{INK}" stroke-width="8"/>')

def face(cx, cy, blush=False, happy=False):
    p = ''
    p += f'<circle cx="{cx-20}" cy="{cy-8}" r="7" fill="{INK}"/>'
    p += f'<circle cx="{cx+20}" cy="{cy-8}" r="7" fill="{INK}"/>'
    p += f'<polygon points="{cx-6},{cy+8} {cx+6},{cy+8} {cx},{cy+16}" fill="{INK}"/>'
    if happy:
        p += f'<path d="M{cx-13},{cy+19} Q{cx},{cy+32} {cx+13},{cy+19}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    else:
        p += (f'<path d="M{cx-12},{cy+18} q6,7 12,0 q6,7 12,0" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>')
    if blush:
        p += f'<ellipse cx="{cx-36}" cy="{cy+14}" rx="11" ry="7" fill="{PINK}"/>'
        p += f'<ellipse cx="{cx+36}" cy="{cy+14}" rx="11" ry="7" fill="{PINK}"/>'
    # 수염
    p += (f'<g stroke="{INK}" stroke-width="4" stroke-linecap="round">'
          f'<line x1="{cx-42}" y1="{cy+2}" x2="{cx-70}" y2="{cy-3}"/>'
          f'<line x1="{cx-42}" y1="{cy+12}" x2="{cx-69}" y2="{cy+15}"/>'
          f'<line x1="{cx+42}" y1="{cy+2}" x2="{cx+70}" y2="{cy-3}"/>'
          f'<line x1="{cx+42}" y1="{cy+12}" x2="{cx+69}" y2="{cy+15}"/></g>')
    return p

def standing_cat():
    p = ''
    # 꼬리
    p += curve('M268,282 C322,268 334,214 302,188', 26, FUR)
    # 몸
    p += f'<ellipse cx="200" cy="250" rx="84" ry="80" fill="{FUR}" stroke="{INK}" stroke-width="7"/>'
    p += f'<ellipse cx="200" cy="272" rx="44" ry="40" fill="#FFF6E8"/>'
    # 등 줄무늬
    p += (f'<g stroke="{FUR_DK}" stroke-width="10" stroke-linecap="round">'
          f'<line x1="132" y1="218" x2="150" y2="212"/>'
          f'<line x1="128" y1="244" x2="147" y2="240"/>'
          f'<line x1="132" y1="270" x2="150" y2="266"/></g>')
    # 발
    p += f'<ellipse cx="166" cy="324" rx="23" ry="12" fill="{FUR}" stroke="{INK}" stroke-width="6"/>'
    p += f'<ellipse cx="234" cy="324" rx="23" ry="12" fill="{FUR}" stroke="{INK}" stroke-width="6"/>'
    # 앞발
    p += capsule(180, 262, 180, 296, 26, FUR)
    p += capsule(220, 262, 220, 296, 26, FUR)
    # 귀
    p += f'<polygon points="160,100 146,52 200,86" fill="{FUR}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    p += f'<polygon points="200,86 254,52 240,100" fill="{FUR}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    p += f'<polygon points="164,90 156,62 188,82" fill="{PINK}"/>'
    p += f'<polygon points="212,82 244,62 236,90" fill="{PINK}"/>'
    # 머리
    p += f'<circle cx="200" cy="138" r="57" fill="{FUR}" stroke="{INK}" stroke-width="7"/>'
    p += (f'<g stroke="{FUR_DK}" stroke-width="9" stroke-linecap="round">'
          f'<line x1="186" y1="90" x2="186" y2="103"/>'
          f'<line x1="200" y1="86" x2="200" y2="101"/>'
          f'<line x1="214" y1="90" x2="214" y2="103"/></g>')
    p += face(200, 140)
    return p

def running_cat(hat=False, badge=False, bag=False, final=False):
    p = ''
    # 속도선
    p += (f'<g stroke="{INK}" stroke-width="6" stroke-linecap="round">'
          f'<line x1="48" y1="148" x2="78" y2="148"/>'
          f'<line x1="40" y1="184" x2="76" y2="184"/>'
          f'<line x1="48" y1="220" x2="78" y2="220"/></g>')
    # 반대쪽(뒤) 다리 — 진한 색
    p += capsule(160, 262, 112, 306, 28, FUR_DK)
    p += capsule(238, 262, 284, 306, 28, FUR_DK)
    # 가방 (몸 뒤)
    if bag:
        p += (f'<g transform="rotate(-10 126 186)">'
              f'<rect x="88" y="140" width="76" height="92" rx="24" fill="{BAG}" stroke="{INK}" stroke-width="7"/>'
              f'<rect x="104" y="140" width="44" height="22" rx="11" fill="{STRAP}" stroke="{INK}" stroke-width="6"/></g>')
    # 꼬리 (몸 뒤, 가방 앞)
    p += curve('M122,206 C74,184 66,124 112,102', 26, FUR)
    # 몸
    p += f'<g transform="rotate(-10 195 230)"><ellipse cx="195" cy="230" rx="88" ry="60" fill="{FUR}" stroke="{INK}" stroke-width="7"/>'
    p += f'<ellipse cx="222" cy="248" rx="40" ry="26" fill="#FFF6E8"/></g>'
    # 등 줄무늬
    p += (f'<g stroke="{FUR_DK}" stroke-width="10" stroke-linecap="round">'
          f'<line x1="136" y1="192" x2="160" y2="184"/>'
          f'<line x1="150" y1="216" x2="174" y2="208"/>'
          f'<line x1="140" y1="240" x2="162" y2="233"/></g>')
    # 가까운 쪽 다리 — 앞으로 뻗은 앞다리, 뒤로 뻗은 뒷다리
    p += capsule(152, 250, 76, 276, 30, FUR)
    p += capsule(242, 248, 324, 282, 30, FUR)
    # 가방끈 (몸 위, 배지 아래)
    if bag:
        p += curve('M236,166 C212,196 198,228 190,264', 19, STRAP)
    # 별 배지 (가슴)
    if badge:
        p += f'<polygon points="{star_pts(248, 222, 25, 11)}" fill="{STAR}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
    # 귀 — 모자 옆으로 벌어지게
    p += f'<polygon points="234,120 194,76 262,104" fill="{FUR}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    p += f'<polygon points="286,102 350,70 322,122" fill="{FUR}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    p += f'<polygon points="234,112 210,86 254,104" fill="{PINK}"/>'
    p += f'<polygon points="292,102 334,80 318,114" fill="{PINK}"/>'
    # 머리
    p += f'<circle cx="272" cy="148" r="54" fill="{FUR}" stroke="{INK}" stroke-width="7"/>'
    if not hat:
        p += (f'<g stroke="{FUR_DK}" stroke-width="9" stroke-linecap="round">'
              f'<line x1="258" y1="102" x2="258" y2="115"/>'
              f'<line x1="272" y1="98" x2="272" y2="113"/>'
              f'<line x1="286" y1="102" x2="286" y2="115"/></g>')
    p += face(272, 152, blush=final, happy=final)
    # 탐험 모자
    if hat:
        p += (f'<g transform="rotate(-6 272 106)">'
              f'<ellipse cx="272" cy="110" rx="76" ry="17" fill="{HAT}" stroke="{INK}" stroke-width="7"/>'
              f'<path d="M216,110 A56,50 0 0 1 328,110 Z" fill="{HAT}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
              f'<path d="M220,102 Q272,84 324,102" fill="none" stroke="{BAND}" stroke-width="13"/></g>')
    # 반짝이 (완성 단계)
    if final:
        p += sparkle(98, 104, 15)
        p += sparkle(332, 248, 13)
        p += sparkle(122, 318, 11)
        p += sparkle(294, 322, 9)
    return p

def svg(body, bgcolor=CREAM):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">'
            + bg(bgcolor) + body + '</svg>')

files = {
    'step0_base.svg':  svg(standing_cat()),
    'step1_run.svg':   svg(running_cat()),
    'step2_hat.svg':   svg(running_cat(hat=True)),
    'step3_badge.svg': svg(running_cat(hat=True, badge=True)),
    'step4_bag.svg':   svg(running_cat(hat=True, badge=True, bag=True)),
    'step5_final.svg': svg(running_cat(hat=True, badge=True, bag=True, final=True), bgcolor=BRIGHT),
}
for name, content in files.items():
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(content)
    print('wrote', name)
