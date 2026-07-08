# -*- coding: utf-8 -*-
"""나노바나나(gemini-2.5-flash-image)로 앱 에셋 일괄 생성.
사용: GEMINI_API_KEY 환경변수 설정 후  python _gen_assets.py
이미 존재하는 파일은 건너뜀(재실행 안전). 키는 저장하지 않음.
"""
import os, sys, base64, json, time, urllib.request

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

KEY = os.environ.get('GEMINI_API_KEY')
if not KEY:
    sys.exit('GEMINI_API_KEY 환경변수가 없습니다.')

MODEL = 'gemini-2.5-flash-image'
URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}'

STYLE = ('초등학교 교재용 플랫 벡터 일러스트 스타일, 밝은 파스텔 톤에 스카이블루(#5B9CF6)와 '
         '민트(#34D399) 포인트, 부드러운 그림자, 깨끗한 순백색 배경, 정사각형 구도, '
         '이미지 안에 글자나 문자는 절대 넣지 말 것. ')
BADGE = '금색 테두리의 동그란 메달 배지 안에 '

ASSETS = [
 ('badge_classify.png', BADGE+'빨간 사과와 토마토가 화살표를 따라 두 바구니에 나뉘어 담기는 아이콘. 분류를 상징.'),
 ('badge_predict.png',  BADGE+'위로 올라가는 꺾은선 그래프와 그 끝에 반짝이는 별. 예측을 상징.'),
 ('badge_cluster.png',  BADGE+'색깔별로 세 무리로 모인 동글동글한 점들. 군집화를 상징.'),
 ('badge_genai.png',    BADGE+'연필로 쓴 문서 위에 큼직한 체크 표시가 있는 돋보기. 생성형 AI 결과 확인을 상징.'),
 ('badge_safety.png',   BADGE+'든든한 방패와 자물쇠. 안전과 윤리를 상징.'),
 ('badge_human.png',    BADGE+'사람 손이 체크 표시 도장을 찍는 아이콘. 사람의 최종 확인을 상징.'),
 ('stamp_seal.png',     '빨간 잉크의 원형 인증 도장 인장. 이중 원 테두리, 가운데에 별과 월계수 잎, 살짝 긁힌 잉크 질감. 공식 합격 도장 느낌.'),
 ('license_logo.png',   "'AI 탐험가' 자격증 엠블럼: 방패 모양 안에 나침반과 회로 무늬가 합쳐진 문장(紋章), 금색과 스카이블루."),
 ('maru_hero.png',      '탐험가 모자를 쓴 초등학생 캐릭터가 허리에 손을 얹고 자신만만하게 웃으며 서 있는 전신 일러스트. 옆에 작은 로봇 친구. 밝고 친근한 만화체.'),
 ('maru_cheer.png',     '탐험가 모자를 쓴 초등학생 캐릭터가 두 팔을 번쩍 들고 환호하는 전신 일러스트, 주변에 색종이 조각이 날림. 밝고 친근한 만화체.'),
]

def gen(prompt):
    body = json.dumps({'contents':[{'parts':[{'text': STYLE + prompt}]}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read())
    for part in res['candidates'][0]['content']['parts']:
        if 'inlineData' in part:
            return base64.b64decode(part['inlineData']['data'])
    raise RuntimeError('이미지 파트 없음: ' + str(res)[:300])

os.makedirs('assets', exist_ok=True)
for fname, prompt in ASSETS:
    path = os.path.join('assets', fname)
    if os.path.exists(path):
        print('건너뜀(이미 있음):', fname); continue
    for attempt in range(3):
        try:
            data = gen(prompt)
            open(path, 'wb').write(data)
            print(f'생성 ✅ {fname} ({len(data)//1024}KB)')
            break
        except Exception as e:
            print(f'재시도 {attempt+1}/3 {fname}: {str(e)[:120]}')
            time.sleep(4)
    else:
        print('실패 ❌', fname)
    time.sleep(1.5)
print('완료')
