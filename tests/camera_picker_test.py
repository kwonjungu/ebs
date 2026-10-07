"""카메라 선택·변경 기능 테스트 (가짜 카메라 2대).

사용: python -I tests/camera_picker_test.py http://127.0.0.1:<port>
(실행기를 --no-browser --port <port> 로 먼저 띄워 둔다)
"""
import sys
import tempfile
from playwright.sync_api import sync_playwright

BASE = sys.argv[1]
# 강: (켜기, 끄기) 버튼
# 23강도 같은 방식(새로 고침 후 자동 재시작)을 쓰지만, 헤드리스 Edge에서 사물 인식 모델과 가짜 카메라 2대를
# 함께 돌리면 탭이 죽어서 자동 검증에서는 뺀다(23강 껐다 켜기 반복·카메라 목록 표시는 따로 확인함).
PAGES = {'16': ('#btnStart', '#btnStart'), '17': ('#camOn', '#camOff')}
LIVE = """() => (window.__ebsCam ? window.__ebsCam.liveVideoDeviceId() : 'no-api')"""
fails = []


def check(name, cond, detail=''):
    print(('ok   ' if cond else 'FAIL ') + name + ('' if cond else '  ' + str(detail)))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        tempfile.mkdtemp(), channel='msedge', headless=True,
        args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream=device-count=2'])
    ctx.grant_permissions(['camera'], origin=BASE)
    ctx.set_default_navigation_timeout(90000)
    for n, (on, off) in PAGES.items():
        pg = ctx.new_page()
        pg.goto(f'{BASE}/{n}/', wait_until='domcontentloaded')
        pg.wait_for_timeout(500)
        check(f'{n} picker hidden before camera', not pg.locator('#ebsCamPicker').is_visible())
        pg.click(on)
        try:
            pg.locator('#ebsCamPicker').wait_for(state='visible', timeout=15000)
        except Exception:
            pass
        check(f'{n} picker visible after camera on', pg.locator('#ebsCamPicker').is_visible())
        pg.wait_for_timeout(6000)  # 모델 준비가 끝난 뒤에 상태를 읽는다(헤드리스에서 준비 중 읽으면 탭이 죽기도 함)
        opts = pg.locator('#ebsCamPicker select option').count()
        check(f'{n} lists 2 cameras', opts == 2, opts)
        before = pg.evaluate(LIVE)
        other = pg.evaluate("""(cur) => [...document.querySelectorAll('#ebsCamPicker select option')].map(o => o.value).find(v => v !== cur)""", before)
        if other:
            pg.select_option('#ebsCamPicker select', other)
            # 페이지가 껐다 다시 켜는 동안(모델 재준비 포함) 새 카메라가 켜질 때까지 기다린다
            for _ in range(50):
                pg.wait_for_timeout(500)
                try:
                    if pg.evaluate(LIVE) == other:
                        break
                except Exception:
                    pass  # 페이지를 새로 여는 중
            pg.wait_for_timeout(1500)
        after = pg.evaluate(LIVE)
        check(f'{n} switched camera', bool(before) and bool(after) and after != before and after == other, (before, after))
        playing = pg.evaluate("""() => [...document.querySelectorAll('video')].some(v => v.srcObject && v.videoWidth > 0 && !v.paused)""")
        check(f'{n} video still playing after switch', playing)
        pg.locator(off).first.wait_for(state='visible')
        for _ in range(20):
            if pg.locator(off).is_enabled():
                break
            pg.wait_for_timeout(500)
        pg.click(off)
        pg.wait_for_timeout(1500)
        check(f'{n} camera fully off after stop', pg.evaluate(LIVE) is None, pg.evaluate(LIVE))
        check(f'{n} picker hidden after stop', not pg.locator('#ebsCamPicker').is_visible())
        pg.close()
    # 선택 기억: 다음 페이지에서 고른 카메라로 시작
    pg = ctx.new_page()
    pg.goto(f'{BASE}/17/', wait_until='domcontentloaded')
    pg.click('#camOn')
    pg.wait_for_timeout(3000)
    saved = pg.evaluate("() => localStorage.getItem('ebs.cameraId')")
    check('remembered camera used on next page', saved is not None and pg.evaluate(LIVE) == saved, (saved, pg.evaluate(LIVE)))
    ctx.close()

sys.exit(1 if fails else 0)
