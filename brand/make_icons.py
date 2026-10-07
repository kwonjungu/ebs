"""로고 원본(brand/logo_source.png)을 앱 아이콘·파비콘으로 가공한다.

원본 문제: 체크무늬가 실제 픽셀로 그려진 가짜 투명, 우하단 Gemini 워터마크, 좌측 가장자리 하늘색 잔여 점.
사용: python -I brand/make_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC = HERE / "logo_source.png"

# 워터마크가 있는 상자(원본 좌표). 테두리 여유 12px 포함.
WM_BOX = (1746, 1748, 1868, 1868)  # x0, y0, x1, y1


def logo_bbox(rgb):
    """파란 사각형 경계 상자. 파란 픽셀이 200개 넘는 행·열만 써서 가장자리 잔여 점을 무시한다."""
    c = rgb.astype(int)
    blue = (c[..., 2] > 180) & (c[..., 2] - c[..., 0] > 100)
    rows = np.where(blue.sum(1) > 200)[0]
    cols = np.where(blue.sum(0) > 200)[0]
    return cols.min(), rows.min(), cols.max(), rows.max()


def remove_watermark(rgb, bbox):
    """워터마크 상자를 좌우 대칭인 왼쪽 아래 모서리에서 뒤집어 복사한다. 원본보다 밝은 픽셀만 바꾼다."""
    x0, y0, x1, y1 = WM_BOX
    mx = bbox[0] + bbox[2]  # 좌우 대칭축 * 2
    src = rgb[y0:y1, mx - x1 + 1:mx - x0 + 1][:, ::-1]
    cur = rgb[y0:y1, x0:x1]
    lighter = cur.astype(int).sum(-1) - src.astype(int).sum(-1) > 24
    lighter = np.asarray(Image.fromarray((lighter * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    cur[lighter] = src[lighter]
    return rgb


def background_mask(rgb, bbox):
    """True = 배경. 밝은 무채색(체크무늬) 중 가장자리에서 이어진 영역 + 상자 바깥 전부."""
    h, w = rgb.shape[:2]
    grey = (rgb.max(-1) - rgb.min(-1) < 30) & (rgb.min(-1) > 150)
    m = Image.fromarray((grey * 255).astype(np.uint8)).copy()  # 복사 안 하면 Pillow 12에서 floodfill이 무시됨
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if m.getpixel(seed) == 255:
            ImageDraw.floodfill(m, seed, 128)
    bg = np.asarray(m) == 128
    x0, y0, x1, y1 = bbox
    outside = np.ones((h, w), bool)
    outside[y0 - 2:y1 + 3, x0 - 2:x1 + 3] = False
    return bg | outside


def main():
    rgb = np.asarray(Image.open(SRC).convert("RGB")).copy()
    bbox = logo_bbox(rgb)
    rgb = remove_watermark(rgb, bbox)
    bg = background_mask(rgb, bbox)
    alpha = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))  # 회색 테두리 번짐 2px 깎기
    im = Image.fromarray(rgb).convert("RGBA")
    im.putalpha(alpha)

    x0, y0, x1, y1 = bbox
    side = max(x1 - x0, y1 - y0) + 1
    pad = side // 32
    canvas = Image.new("RGBA", (side + 2 * pad, side + 2 * pad), (0, 0, 0, 0))
    crop = im.crop((x0, y0, x1 + 1, y1 + 1))
    canvas.paste(crop, (pad + (side - crop.width) // 2, pad + (side - crop.height) // 2))

    big = canvas.resize((1024, 1024), Image.LANCZOS)
    big.save(HERE / "logo_1024.png")
    out = REPO / "assets" / "brand"
    out.mkdir(parents=True, exist_ok=True)
    big.resize((512, 512), Image.LANCZOS).save(out / "logo_512.png", optimize=True)
    big.resize((32, 32), Image.LANCZOS).save(out / "favicon-32.png", optimize=True)
    big.save(HERE / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("bbox", bbox)


if __name__ == "__main__":
    main()
