# -*- coding: utf-8 -*-
"""manual.template.html + manual_img/ -> package/설명서.html, Edge 인쇄로 package/설명서.pdf, 검수(설계서 §6).
사용: python tools/manual/build_manual.py   (capture.py 를 먼저 돌려 그림을 만들어 둔다). 검수 실패 시 종료 코드 1.
"""
import io, re, shutil, subprocess, sys, tempfile, zlib
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PKG = ROOT / 'package'
IMG = PKG / 'manual_img'
HTML = PKG / '설명서.html'
PDF = PKG / '설명서.pdf'
QHTML = PKG / '빠른안내.html'
QPDF = PKG / '빠른안내.pdf'
EDGE = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
FORBIDDEN = ['실행 파일', '서버', '포트', '로컬', '인증서']
errors = []


def err(msg):
    errors.append(msg); print('검수 실패:', msg, file=sys.stderr)


def white_to_alpha(im):
    """마루 그림의 바깥쪽 흰 바탕만 투명하게 (안쪽 흰색은 그대로). 복사본만 바꾸고 원본은 건드리지 않는다."""
    from PIL import ImageDraw
    rgb = im.convert('RGB')
    mask = Image.eval(rgb.convert('L'), lambda v: 255 if v > 236 else 0)
    for pt in ((0, 0), (mask.width - 1, 0), (0, mask.height - 1), (mask.width - 1, mask.height - 1)):
        if mask.getpixel(pt) == 255: ImageDraw.floodfill(mask, pt, 128, thresh=0)
    alpha = Image.eval(mask, lambda v: 0 if v == 128 else 255)
    out = rgb.convert('RGBA'); out.putalpha(alpha)
    return out


def copy_assets():
    """마루·로고를 manual_img/ 로 복사 (원본은 건드리지 않음). 마루는 흰 바탕을 투명하게, 300KB 넘으면 줄여서 저장."""
    for src, name in [(ROOT / 'assets' / 'maru_hero.png', 'maru_hero.png'), (ROOT / 'assets' / 'maru_cheer.png', 'maru_cheer.png'),
                      (ROOT / 'assets' / 'brand' / 'logo_512.png', 'logo_512.png')]:
        dst = IMG / name
        im = Image.open(src)
        if name.startswith('maru'): im = white_to_alpha(im)
        elif src.stat().st_size <= 300 * 1024:
            shutil.copyfile(src, dst); continue
        im = im.convert('RGBA')
        for colors in (256, 128, 64):
            buf = io.BytesIO(); im.quantize(colors=colors, method=Image.FASTOCTREE).save(buf, 'PNG', optimize=True)
            if len(buf.getvalue()) <= 300 * 1024: break
        dst.write_bytes(buf.getvalue())


class Collect(HTMLParser):
    def __init__(self):
        super().__init__(); self.imgs = []; self.links = []; self.ids = set(); self.stack = []
        self.sections = {}; self.cur = None; self.say = None; self.say_text = []; self.says = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        if 'id' in a: self.ids.add(a['id'])
        if tag == 'section' and 'step' in (a.get('class') or '').split():
            self.cur = a['id']; self.sections[self.cur] = {'figs': int(a.get('data-figs', -1)), 'imgs': 0, 'says': []}
        if tag == 'img' and a.get('src'):
            self.imgs.append(a['src'])
            if self.cur and self.stack and 'fig' in self.stack_classes(): self.sections[self.cur]['imgs'] += 1
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag not in ('img', 'br', 'link', 'meta', 'use', 'path', 'circle', 'rect', 'ellipse', 'line', 'symbol') or tag == 'symbol':
            self.stack.append((tag, (a.get('class') or '').split()))
        if tag == 'p' and 'say' in (a.get('class') or '').split():
            self.say = []
    def stack_classes(self):
        return [c for _, cl in self.stack for c in cl]
    def handle_endtag(self, tag):
        if tag == 'p' and self.say is not None:
            txt = ''.join(self.say).strip()
            if self.cur: self.sections[self.cur]['says'].append(txt)
            self.say = None
        if tag == 'section': self.cur = None
        if self.stack and self.stack[-1][0] == tag: self.stack.pop()
    def handle_data(self, d):
        if self.say is not None: self.say.append(d)


def sentences(text):
    return len([s for s in re.split(r'[.!?](?:\s+|$)', text.strip()) if s.strip()])


def build_html():
    tpl = (HERE / 'manual.template.html').read_text(encoding='utf-8')
    chips = []
    for m in re.finditer(r'<section class="page[^"]*" id="([^"]+)" data-toc="([^"]+)"(?: data-n="(\d+)")?', tpl):
        sid, name, n = m.groups()
        chips.append(f'<a href="#{sid}">{f"<i>{n}</i>" if n else ""}{name}</a>')
    out = tpl.replace('<!--TOC-->', '\n    '.join(chips))
    HTML.write_text(out, encoding='utf-8', newline='\n')
    return out


def static_checks(html):
    p = Collect(); p.feed(html)
    for src in p.imgs:
        if not (PKG / src).exists(): err(f'그림 파일이 없어요: {src}')
    for href in p.links:
        if href.startswith('#'):
            if href[1:] not in p.ids: err(f'목차 링크가 가리키는 쪽이 없어요: {href}')
        elif not href.startswith('http') and not (PKG / href).exists():
            err(f'링크 파일이 없어요: {href}')
    for sid, s in p.sections.items():
        if s['imgs'] != s['figs']: err(f'{sid}: 그림 {s["imgs"]}개 (기대 {s["figs"]}개)')
        for t in s['says']:
            if sentences(t) > 2: err(f'{sid}: 문장이 2개를 넘어요: {t}')
    print(f'정적 검수: 그림 {len(p.imgs)}개, 단계 쪽 {len(p.sections)}개')


def browser_checks():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge', headless=True)
        for media in ('screen', 'print'):
            pg = b.new_page(viewport={'width': 1366, 'height': 768})
            pg.emulate_media(media=media)
            pg.goto(HTML.as_uri()); pg.evaluate('document.fonts.ready')
            small = pg.evaluate("""() => { const bad = new Set(); const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              while (w.nextNode()) { const n = w.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement;
                if (e.closest('svg,script,style')) continue; const fs = parseFloat(getComputedStyle(e).fontSize);
                if (fs < 16) bad.add(fs + 'px: ' + n.textContent.trim().slice(0, 20)); } return [...bad]; }""")
            for s in small: err(f'글자가 16px보다 작아요({media}): {s}')
            if media == 'screen':
                sw = pg.evaluate('[document.documentElement.scrollWidth, innerWidth]')
                if sw[0] > sw[1]: err(f'가로 스크롤이 생겨요: {sw}')
                hs = pg.evaluate("[...document.querySelectorAll('.step')].map(e => [e.id, Math.round(e.getBoundingClientRect().height)])")
                for sid, h in hs:
                    if h > 768 * 1.5: err(f'{sid}: 한 단계가 한 화면보다 너무 길어요 ({h}px)')
                print('1366x768 단계 높이(px):', ', '.join(f'{i[2:]}={h}' for i, h in hs))
                bad = pg.evaluate("""() => { const t = [...document.querySelectorAll('body *')].filter(e => !e.closest('.teacher,svg,script,style')).map(e => e.childNodes.length ? [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('') : '').join('\\n');
                  return t; }""")
                text = bad.replace("'다운로드'", '')
                for w in FORBIDDEN + ['다운로드']:
                    if w in text: err(f'안 쓰기로 한 말이 본문에 있어요: {w}')
            pg.close()
        b.close()


def quick_browser_check():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge', headless=True)
        for media in ('screen', 'print'):
            pg = b.new_page(viewport={'width': 1366, 'height': 768}); pg.emulate_media(media=media)
            pg.goto(QHTML.as_uri()); pg.evaluate('document.fonts.ready')
            small = pg.evaluate("""() => { const bad = new Set(); const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              while (w.nextNode()) { const n = w.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement;
                const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 16) bad.add(fs + 'px: ' + n.textContent.trim().slice(0, 20)); } return [...bad]; }""")
            for t in small: err(f'빠른안내 글자가 16px보다 작아요({media}): {t}')
            pg.close()
        b.close()


def make_pdf(HTML=HTML, PDF=PDF):
    tmp = tempfile.mkdtemp(prefix='edge_')
    if PDF.exists(): PDF.unlink()
    r = subprocess.run([str(EDGE), '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--user-data-dir={tmp}',
                        f'--print-to-pdf={PDF}', HTML.as_uri()], capture_output=True, timeout=180)
    shutil.rmtree(tmp, ignore_errors=True)
    if not PDF.exists(): err('PDF를 만들지 못했어요 ' + r.stderr.decode('utf-8', 'ignore')[:200])


def pdf_checks(PDF=PDF, max_pages=12, label='PDF'):
    if not PDF.exists(): return
    data = PDF.read_bytes()
    kb = len(data) / 1024
    try:
        from pypdf import PdfReader
        rd = PdfReader(str(PDF)); n = len(rd.pages); w, h = (float(x) for x in rd.pages[0].mediabox[2:])
        fonts = set()
        for pgx in rd.pages:
            for f in (pgx['/Resources'].get('/Font') or {}).values():
                fd = f.get_object(); fonts.add(str(fd.get('/BaseFont')))
                emb = ('/FontDescriptor' in fd and any(k in fd['/FontDescriptor'] for k in ('/FontFile', '/FontFile2', '/FontFile3'))) \
                    or fd.get('/Subtype') == '/Type0' or fd.get('/Subtype') == '/Type3'
                if not emb: err(f'폰트가 PDF에 포함되지 않았어요: {fd.get("/BaseFont")}')
    except ImportError:
        n = len(re.findall(rb'/Type\s*/Page[^s]', data)); w, h = 595, 842; fonts = set()
    print(f'{label}: {n}쪽, {w:.0f}x{h:.0f}pt, {kb/1024:.2f}MB, 폰트 {len(fonts)}종')
    if n > max_pages or (max_pages == 1 and n != 1): err(f'{label}가 {n}쪽이에요 ({max_pages}쪽 이하여야 해요)')
    if abs(w - 595) > 3 or abs(h - 842) > 3: err(f'A4가 아니에요: {w}x{h}')
    if kb > 3072: err(f'PDF가 3MB를 넘어요 ({kb/1024:.1f}MB)')


def main():
    if not IMG.exists() or not list(IMG.glob('s*.png')):
        print('그림이 없어요. 먼저 python tools/manual/capture.py 를 돌려 주세요.', file=sys.stderr); sys.exit(1)
    copy_assets()
    html = build_html()
    static_checks(html)
    browser_checks()
    make_pdf()
    pdf_checks()
    # A4 한 장 빠른 안내
    shutil.copyfile(HERE / 'quick.template.html', QHTML)
    q = Collect(); q.feed(QHTML.read_text(encoding='utf-8'))
    for src in q.imgs:
        if not (PKG / src).exists(): err(f'빠른안내 그림 파일이 없어요: {src}')
    quick_browser_check()
    make_pdf(QHTML, QPDF)
    pdf_checks(QPDF, 1, '빠른안내 PDF')
    big = [f.name for f in list(IMG.glob('*.png')) + list((IMG / 'raw').glob('*.png')) if f.stat().st_size > 300 * 1024]
    if big: err(f'300KB 넘는 그림: {big}')
    if errors:
        print(f'검수 실패 {len(errors)}건', file=sys.stderr); sys.exit(1)
    print('설명서 만들기 완료:', HTML, PDF)


if __name__ == '__main__':
    main()
