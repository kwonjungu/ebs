# -*- coding: utf-8 -*-
"""설명서 그림 만들기: 앱을 테스트 포트로 띄워 진짜 화면을 찍고, Windows 화면 모형(mock/*.html)을 찍어
package/manual_img/ 에 저장한다. 강조 표시(빨간 원/네모+화살표)는 그림에 구워 넣는다.
사용: python tools/manual/capture.py   (사전: pip install playwright pillow, dist\\AI탐험대\\AI탐험대.exe 필요)
"""
import io, json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
import http.server, threading, functools, math
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'package' / 'manual_img'
EXE = ROOT / 'dist' / 'AI탐험대' / 'AI탐험대.exe'
PORT = 47816
BASE = f'http://127.0.0.1:{PORT}'
MOCK = HERE / 'mock'
RAW = OUT / 'raw'
SRC_PORT = 47817   # 작업 폴더(소스)를 그대로 서빙하는 임시 서버 (아직 exe에 안 들어간 새 기능 촬영용)
RED = (229, 57, 53)
MAX_W, MAX_KB = 1280, 300

# 강 번호 -> 화면에서 쓰는 선택자 (없으면 실패 처리: 조용히 넘어가지 않는다)
LESSONS = {
    'hub_title': ('/', 'h1'),
    'hub_grid': ('/', '.grid'),
    'hub_card': ('/', 'a.card[href="16/"]'),
    'topbar': ('/16/', '.lessonbar'),
    'cam_start': ('/16/', '#btnStart'),
    'entry_btn': ('/17/', 'a[href$=".ent"]'),
}

RECT_JS = """([sel, tight]) => { const e = document.querySelector(sel); if (!e) return null;
  let r; if (tight) { const g = document.createRange(); g.selectNodeContents(e); r = g.getBoundingClientRect(); } else r = e.getBoundingClientRect();
  return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; }
"""
SCROLL_JS = "(sel) => { const e = document.querySelector(sel); if (e) e.scrollIntoView({block: 'center'}); }"


def fail(msg):
    print('캡처 실패:', msg, file=sys.stderr)
    sys.exit(1)


def save_png(im, path, quiet=False):
    """2배 캡처 -> 1280px 이하 + 300KB 이하 PNG (Pillow quantize, 결정적)."""
    im = im.convert('RGB')
    width = min(MAX_W, im.width)
    for colors in (256, 192, 128, 96, 64):
        w = width
        while True:
            h = round(im.height * w / im.width)
            small = im.resize((w, h), Image.LANCZOS) if w != im.width else im
            q = small.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
            buf = io.BytesIO(); q.save(buf, 'PNG', optimize=True)
            if len(buf.getvalue()) <= MAX_KB * 1024:
                path.write_bytes(buf.getvalue())
                if not quiet: print(f'  {path.name} {w}x{h} {len(buf.getvalue())//1024}KB')
                return
            if colors > 64: break
            w = int(w * 0.9)
            if w < 640: break
    fail(f'{path.name} 를 {MAX_KB}KB 이하로 줄이지 못했어요')


def load_callouts():
    d = json.loads((HERE / 'callouts.json').read_text(encoding='utf-8'))
    return {k: v for k, v in d.items() if not k.startswith('_')}


CALLOUTS = load_callouts()


def callout_items(page, name, selmap, clip, scroll=False):
    """callouts.json 의 대상 상자를 읽어 clip(그림 영역) 대비 비율 좌표로 바꾼다 (손 좌표 없음)."""
    items = []
    for c in CALLOUTS.get(name, []):
        sel = selmap(c['target'])
        if scroll:
            page.evaluate(SCROLL_JS, sel); page.wait_for_timeout(900)
        r = page.evaluate(RECT_JS, [sel, bool(c.get('tight'))])
        if not r: fail(f'{name}: 강조 대상을 찾을 수 없어요 ({sel})')
        items.append({'rx': (r['x'] - clip['x']) / clip['width'], 'ry': (r['y'] - clip['y']) / clip['height'],
                      'rw': r['w'] / clip['width'], 'rh': r['h'] / clip['height'],
                      'pad': c['pad'], 'from': c['from'], 'len': c.get('len', 110), 'num': c.get('num')})
    return items


COMPUTED = {}


def burn_callouts(png_bytes, name, items, css_w):
    """원본(raw/)을 따로 저장하고, Pillow로 빨간 둥근 네모+화살표(+번호 원)를 구워 manual_img/ 에 저장."""
    im = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    save_png(im, RAW / f'{name}.png', quiet=True)
    COMPUTED[name] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in it.items()} for it in items]
    if items:
        im = draw_callouts(im, items, css_w)
    save_png(im, OUT / f'{name}.png')


def draw_callouts(im, items, css_w):
    W, H = im.size
    fin = min(MAX_W, W)
    k = (W / fin) * 3          # 최종 그림 1px = 그리기 단위 k (3배 확대해 그린 뒤 줄여서 계단 없애기)
    f = fin / css_w            # css px -> 최종 px
    layer = Image.new('RGBA', (W * 3, H * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    WHITE = (255, 255, 255, 255)
    for it in items:
        p = it['pad'] * f * k
        x0, y0 = it['rx'] * W * 3 - p, it['ry'] * H * 3 - p
        x1, y1 = x0 + it['rw'] * W * 3 + 2 * p, y0 + it['rh'] * H * 3 + 2 * p
        rad = min(16 * k, (x1 - x0) / 2, (y1 - y0) / 2)
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=RED + (30,))
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad, outline=WHITE, width=round(12 * k))
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad, outline=RED + (255,), width=round(6 * k))
        # 대각선 화살표: 박스 바깥 모서리 쪽에서 안쪽을 향해
        sx = -1 if 'left' in it['from'] else 1
        sy = -1 if 'top' in it['from'] else 1
        ux, uy = sx / math.sqrt(2), sy / math.sqrt(2)           # 꼬리 쪽 방향
        cx = x0 if sx < 0 else x1; cy = y0 if sy < 0 else y1     # 가리키는 모서리
        gap = 4 * k
        tip = (cx + ux * (gap + 3 * k), cy + uy * (gap + 3 * k))
        L = it['len'] * f * k
        tail = (tip[0] + ux * L, tip[1] + uy * L)
        hl, hw = 40 * k, 24 * k
        bx, by = tip[0] + ux * hl, tip[1] + uy * hl              # 머리 밑변 중심
        nx, ny = -uy, ux
        head = [tip, (bx + nx * hw, by + ny * hw), (bx - nx * hw, by - ny * hw)]
        cxh = sum(q[0] for q in head) / 3; cyh = sum(q[1] for q in head) / 3

        def grow(poly, g):
            out = []
            for qx, qy in poly:
                dx, dy = qx - cxh, qy - cyh; n = math.hypot(dx, dy) or 1
                out.append((qx + dx / n * g, qy + dy / n * g))
            return out

        def shaft(w, col):
            d.line([tail, (bx, by)], fill=col, width=round(w * k))
            r = w * k / 2
            d.ellipse([tail[0] - r, tail[1] - r, tail[0] + r, tail[1] + r], fill=col)

        shaft(18, WHITE); d.polygon(grow(head, 5 * k), fill=WHITE)
        shaft(10, RED + (255,)); d.polygon(head, fill=RED + (255,))
        if it.get('num'):
            from PIL import ImageFont
            r = 22 * k; nx0, ny0 = x0 + 6 * k, y0 + 6 * k
            d.ellipse([nx0 - r, ny0 - r, nx0 + r, ny0 + r], fill=WHITE)
            d.ellipse([nx0 - r + 4 * k, ny0 - r + 4 * k, nx0 + r - 4 * k, ny0 + r - 4 * k], fill=RED + (255,))
            ft = ImageFont.truetype(r'C:\Windows\Fonts\malgunbd.ttf', round(26 * k))
            d.text((nx0, ny0), str(it['num']), font=ft, fill=WHITE, anchor='mm')
    layer = layer.resize((W, H), Image.LANCZOS)
    out = im.convert('RGBA'); out.alpha_composite(layer)
    return out.convert('RGB')


def mock_sel(target):
    return f'[data-callout="{target}"]'


def shoot_mock(ctx, name, file, query='', also=None):
    page = ctx.new_page()
    page.goto((MOCK / file).as_uri() + query)
    page.wait_for_load_state('load')
    page.evaluate('document.fonts.ready')
    page.wait_for_function('[...document.images].every(i => i.complete)')
    box = page.evaluate(RECT_JS, ['#stage', False])
    clip = {'x': box['x'], 'y': box['y'], 'width': box['w'], 'height': box['h']}
    items = callout_items(page, name, mock_sel, clip)
    if also: also(page)
    burn_callouts(page.screenshot(clip=clip, full_page=True), name, items, clip['width'])
    page.close()


# ---- Program.cs 와 모형 글자 일치 검사 ----
def program_cs_messages():
    src = (ROOT / 'launcher' / 'Program.cs').read_text(encoding='utf-8')
    msgs = []
    for m in re.finditer(r'Notify\(opt,\s*(.+?)\);', src):
        out = ''
        for t in re.finditer(r'"((?:[^"\\]|\\.)*)"|opt\.Port', m.group(1)):
            out += t.group(1).encode().decode('unicode_escape').encode('latin-1').decode('utf-8') if t.group(1) is not None else str(47815)
        msgs.append(out)
    title = re.search(r'const string Title = "(.*?)";', src).group(1)
    tray = re.findall(r'menu\.Items\.Add\("(.*?)"', src)
    balloon = re.search(r'ShowBalloonTip\(\d+, Title, "(.*?)"', src).group(1)
    return msgs, title, tray, balloon


def check_msgbox_text(page, expected, title):
    got = page.evaluate("document.getElementById('msg').textContent")
    if got != expected:
        fail(f'모형 글자가 Program.cs와 달라요:\n  모형: {got!r}\n  원본: {expected!r}')
    if title not in page.evaluate("document.querySelector('.tb').textContent"):
        fail('모형 제목이 Program.cs 의 Title 과 달라요')


# ---- 서버 ----
def port_busy():
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', PORT)) == 0


def start_server():
    if not EXE.exists():
        fail(f'{EXE} 가 없어요. 먼저 powershell -ExecutionPolicy Bypass -File build.ps1 을 돌려 주세요.')
    if port_busy():
        fail(f'{PORT}번을 이미 다른 프로그램이 쓰고 있어요. 끝내고 다시 해 주세요.')
    proc = subprocess.Popen([str(EXE), '--no-browser', '--quiet', '--port', str(PORT)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    for _ in range(60):
        try:
            if urllib.request.urlopen(BASE + '/__ebs_ping', timeout=1).read().decode() == 'ebs-ai-explorer':
                return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    fail('앱 서버가 응답하지 않아요')


def stop_server(proc):
    proc.terminate()  # 우리가 띄운 PID만 끝낸다
    try: proc.wait(10)
    except subprocess.TimeoutExpired: proc.kill()
    if port_busy(): print('경고: 서버 포트가 아직 열려 있어요', file=sys.stderr)


def make_face_y4m(dst):
    """마루 그림으로 가짜 카메라 영상(y4m) 생성 (진짜 얼굴이 없어도 '카메라 켜짐' 화면용)."""
    import numpy as np
    W, H = 640, 480
    bg = Image.new('RGB', (W, H), (235, 235, 230))
    im = Image.open(ROOT / 'assets' / 'maru_hero.png').convert('RGBA'); im.thumbnail((440, 440))
    bg.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)
    ycc = np.asarray(bg.convert('YCbCr'))
    y = ycc[..., 0].tobytes(); u = ycc[::2, ::2, 1].tobytes(); v = ycc[::2, ::2, 2].tobytes()
    with open(dst, 'wb') as f:
        f.write(b'YUV4MPEG2 W640 H480 F15:1 Ip A1:1 C420jpeg\n')
        for _ in range(15): f.write(b'FRAME\n' + y + u + v)


def start_src_server():
    class Q(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', SRC_PORT), Q)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def app_shot(page, name, clip, selmap, scroll=False, fullpage=True):
    items = callout_items(page, name, selmap, clip, scroll)
    burn_callouts(page.screenshot(clip=clip, full_page=fullpage), name, items, clip['width'])


def main():
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    msgs, title, tray, balloon = program_cs_messages()
    if len(msgs) != 2: fail('Program.cs 에서 안내창 문구 2개를 못 찾았어요')
    tmp = Path(tempfile.mkdtemp(prefix='manual_'))
    y4m = tmp / 'face.y4m'; make_face_y4m(y4m)
    proc = start_server()
    src = None
    try:
        with sync_playwright() as p:
            def launch(two=False):
                dev = '--use-fake-device-for-media-stream' + ('=device-count=2' if two else '')
                return p.chromium.launch(channel='msedge', headless=True, args=[
                    '--use-fake-ui-for-media-stream', dev,
                    f'--use-file-for-fake-video-capture={y4m}', '--autoplay-policy=no-user-gesture-required'])
            browser = launch()
            kw = dict(device_scale_factor=2, reduced_motion='reduce', locale='ko-KR')
            hubsel = lambda t: {'h1': LESSONS['hub_title'][1], 'card': LESSONS['hub_card'][1]}[t]

            # ---- 앱 화면 (진짜 캡처) ----
            ctx = browser.new_context(viewport={'width': 1280, 'height': 720}, **kw)
            pg = ctx.new_page()
            pg.goto(BASE + '/'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(500)
            app_shot(pg, 's05_hub', {'x': 0, 'y': 0, 'width': 1280, 'height': 720}, hubsel, fullpage=False)

            pg.set_viewport_size({'width': 1280, 'height': 800})
            pg.reload(); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
            g = pg.evaluate(RECT_JS, [LESSONS['hub_grid'][1], False])
            if not g: fail('허브 카드 영역을 못 찾았어요')
            app_shot(pg, 's06_pick', {'x': 0, 'y': max(0, g['y'] - 24), 'width': 1280, 'height': 640}, hubsel)

            pg.goto(BASE + '/16/'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(500)
            # 위 줄이 화면 맨 위에 붙어 있어 강조 테두리가 잘리므로, 위에 종이색 여백을 조금 둔다
            pg.evaluate("document.documentElement.style.cssText = 'padding-top:30px;background:#FBF7EC'"); pg.wait_for_timeout(200)
            app_shot(pg, 's06b_topbar', {'x': 200, 'y': 0, 'width': 880, 'height': 150}, lambda t: LESSONS['topbar'][1])

            pg.goto(BASE + LESSONS['entry_btn'][0]); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(500)
            esel = LESSONS['entry_btn'][1]
            pg.evaluate(SCROLL_JS, esel); pg.wait_for_timeout(900)
            r = pg.evaluate(RECT_JS, [esel, False])
            if not r: fail('엔트리 파일 내려받기 버튼을 못 찾았어요')
            app_shot(pg, 's08_entry', {'x': 190, 'y': max(0, r['y'] - 60), 'width': 900, 'height': 190}, lambda t: esel)
            pg.close(); ctx.close()

            # ---- 카메라 켜짐 화면 -> 허용 창 합성 ----
            ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, permissions=['camera', 'microphone'], **kw)
            pg = ctx.new_page(); pg.goto(BASE + '/16/'); pg.evaluate('document.fonts.ready')
            if not pg.evaluate(f'!!document.querySelector({json.dumps(LESSONS["cam_start"][1])})'): fail('카메라 시작 버튼 없음')
            pg.click(LESSONS['cam_start'][1])
            pg.wait_for_function("document.querySelector('video') && document.querySelector('video').readyState >= 2", timeout=20000)
            pg.wait_for_timeout(2500)
            base_png = tmp / 's07_base.png'; pg.screenshot(path=str(base_png))
            pg.close(); ctx.close(); browser.close()

            # ---- 카메라 고르기 상자 (카메라 2대짜리 가짜 장치, 소스 폴더 서빙) ----
            src = start_src_server()
            browser = launch(two=True)
            ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, permissions=['camera', 'microphone'], **kw)
            pg = ctx.new_page(); pg.goto(f'http://127.0.0.1:{SRC_PORT}/17/'); pg.evaluate('document.fonts.ready')
            pg.click('#camOn')
            pg.locator('#ebsCamPicker').wait_for(state='visible', timeout=20000)
            pg.evaluate('window.scrollTo(0, 0)'); pg.wait_for_timeout(1500)
            # 가짜 카메라의 이름은 임시 파일 경로(사용자 이름 포함)라서, 그림에서는 보통 이름으로 바꿔 보여 준다
            pg.evaluate("() => { const o = document.querySelectorAll('#ebsCamPicker select option'); const n = ['내장 카메라', 'USB 카메라']; o.forEach((e, i) => e.textContent = n[i] || ('카메라 ' + (i + 1))); }")
            app_shot(pg, 's07b_camera', {'x': 240, 'y': 540, 'width': 800, 'height': 260}, lambda t: '#ebsCamPicker', fullpage=False)
            pg.close(); ctx.close(); browser.close()

            # ---- Windows 모형 ----
            browser = launch()
            ctx = browser.new_context(viewport={'width': 1000, 'height': 700}, **kw)
            shoot_mock(ctx, 's01_download', 'edge_download.html')
            shoot_mock(ctx, 's02_extract', 'explorer_menu.html')
            shoot_mock(ctx, 's03_folder', 'explorer_folder.html')
            shoot_mock(ctx, 's04a_smart', 'smartscreen.html', '?step=1')
            shoot_mock(ctx, 's04b_smart', 'smartscreen.html', '?step=2')
            shoot_mock(ctx, 's07_perm', 'edge_perm.html', '?bg=' + base_png.as_uri())

            def chk_tray(page):
                txt = page.evaluate('document.body.innerText')
                for s in tray + [balloon]:
                    if s not in txt: fail(f'트레이 모형에 "{s}" 글자가 없어요 (Program.cs 기준)')
            shoot_mock(ctx, 's09_tray', 'tray_menu.html', also=chk_tray)
            shoot_mock(ctx, 's10a_nofolder', 'msgbox.html', '?t=2', also=lambda pg: check_msgbox_text(pg, msgs[0], title))
            shoot_mock(ctx, 's10b_portbusy', 'msgbox.html', '?t=3', also=lambda pg: check_msgbox_text(pg, msgs[1], title))
            shoot_mock(ctx, 's10c_url', 'addressbar.html')
            ctx.close(); browser.close()
        (HERE / 'callouts.computed.json').write_text(json.dumps(COMPUTED, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')
    finally:
        if src: src.shutdown()
        stop_server(proc)
        shutil.rmtree(tmp, ignore_errors=True)
    print('캡처 완료:', OUT)


if __name__ == '__main__':
    main()
