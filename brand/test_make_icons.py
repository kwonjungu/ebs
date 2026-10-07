"""make_icons.py 결과 검증. 사용: python -I brand/test_make_icons.py"""
from pathlib import Path
from PIL import Image
import numpy as np

REPO = Path(__file__).resolve().parent.parent
fails = []

def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

big = REPO / "brand" / "logo_1024.png"
check("logo_1024 exists", big.exists())
if big.exists():
    im = Image.open(big)
    a = np.asarray(im.convert("RGBA")).astype(int)
    check("logo_1024 size", im.size == (1024, 1024))
    check("corners transparent", all(a[y, x, 3] == 0 for y, x in [(0, 0), (0, 1023), (1023, 0), (1023, 1023)]))
    check("center opaque", a[512, 512, 3] == 255)
    # 체크무늬 회색(채도 낮고 밝은 픽셀)이 불투명하게 남아 있으면 안 됨 (안쪽 흰 눈금은 예외: 가운데 원 밖 테두리 띠만 검사)
    edge = np.zeros(a.shape[:2], bool)
    edge[:40, :] = edge[-40:, :] = True
    edge[:, :40] = edge[:, -40:] = True
    grey = (a[..., :3].max(-1) - a[..., :3].min(-1) < 30) & (a[..., :3].min(-1) > 150)
    check("no opaque checkerboard on border band", int((grey & edge & (a[..., 3] > 128)).sum()) == 0)
    # 워터마크 영역: 원본 좌표 (1758..1855, 1760..1855) → 1024 스케일 약 (870..930, 870..930)
    wm = a[870:930, 870:930]
    opaque = wm[..., 3] > 200
    bright = wm[..., :3].sum(-1) > 3 * 140
    check("watermark removed", int((opaque & bright).sum()) == 0)

for rel, size in [("assets/brand/logo_512.png", (512, 512)), ("assets/brand/favicon-32.png", (32, 32))]:
    p = REPO / rel
    check(rel + " exists", p.exists())
    if p.exists():
        check(rel + " size", Image.open(p).size == size)

ico = REPO / "brand" / "app.ico"
check("app.ico exists", ico.exists())
if ico.exists():
    sizes = Image.open(ico).info.get("sizes", set())
    check("app.ico sizes", {(16, 16), (32, 32), (48, 48), (256, 256)} <= set(sizes))

raise SystemExit(1 if fails else 0)
