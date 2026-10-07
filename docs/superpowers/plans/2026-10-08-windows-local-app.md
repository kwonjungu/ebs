# AI 탐험대 Windows 로컬 앱 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** kwonjungu/ebs 체험 웹앱을 zip으로 받아 풀고 `AI탐험대.exe`를 더블클릭하면 모든 체험이 동작하는 Windows 로컬 앱으로 만든다.

**Architecture:** C# 단일 exe(Windows 내장 csc로 빌드)가 `127.0.0.1:47815`에서 `app\` 폴더를 정적 서빙하고 Edge 앱 창을 연다. 웹앱은 구조를 유지하되 CDN 의존(17강 face-api, 25강 폰트)만 `assets/vendor/`로 옮긴다. 로고 원본을 가공해 exe 아이콘·favicon·허브 로고로 쓴다.

**Tech Stack:** C# (.NET Framework 4.x, `csc.exe`), Windows Forms(NotifyIcon), PowerShell 5.1(빌드), Git Bash + curl(서버 테스트), Python 3 + Pillow + numpy(로고 가공, 개발 PC 전용)

**Spec:** `docs/superpowers/specs/2026-10-08-windows-local-app-design.md`

## Global Constraints

- 대상 OS: Windows 10/11, 관리자 권한 없음, 추가 설치 없음
- 컴파일러: `%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe` 만 사용 (외부 DLL·NuGet 금지). 이 컴파일러는 **C# 5까지만** 지원 → `catch … when`, `?.`, `$"..."`, `out var`, `=>` 멤버, `nameof` 사용 금지
- 포트: `47815` 고정, 바인드 주소 `IPAddress.Loopback`만
- 중복 실행 판별: `GET /__ebs_ping` → 본문 `ebs-ai-explorer`
- `.ent` 등 모든 파일은 `Content-Encoding` 없이 원본 바이트 그대로 전송
- 모든 응답에 `Cache-Control: no-cache`, `Connection: close`
- 웹앱 수정은 온라인(GitHub Pages)과 로컬 양쪽에서 같은 코드로 동작 (로컬 전용 분기 금지)
- 배포 폴더명·exe명: `AI탐험대`, `AI탐험대.exe`, zip명 `AI탐험대_v1.0.zip`
- 온라인 주소: `https://kwonjungu.github.io/ebs/`
- 한글이 든 `.ps1`·`.txt`는 UTF-8 **BOM** 저장(PowerShell 5.1·메모장 호환), `.cs`는 `/codepage:65001`로 컴파일
- 웹에서 쓰는 로고는 `assets/brand/`(zip에 포함), 원본·가공 스크립트·`app.ico`는 `brand/`(zip 제외)
- `dist/`는 git 제외

## Review Focus

1. 압축을 풀지 않고 zip 안에서 exe 실행 → `app\` 없음 → 안내 후 종료(크래시·빈 창 금지) — Task 3 테스트
2. 압축 해제 경로에 한글·공백(`바탕화면\AI탐험대 (1)\`) → 정상 서빙 — Task 7 테스트
3. 포트 47815를 다른 프로그램이 점유 → 안내 후 종료, 우리 앱이 이미 실행 중이면 창만 다시 열기 — Task 3 테스트
4. 같은 대용량 파일(MediaPipe wasm 9MB 등)을 여러 요청이 동시에 받거나 중간에 끊음 → 다른 요청·서버 생존에 영향 없음 — Task 2 테스트
5. 학교 프록시가 설정된 PC → ping 요청이 프록시로 새지 않음(`Proxy = null`) — Task 3 코드·리뷰 항목

---

## File Structure

| 파일 | 책임 |
|---|---|
| `brand/logo_source.png` | Gemini 생성 원본 (커밋 완료) |
| `brand/make_icons.py` | 원본 → 투명 배경·워터마크 제거 → 각 크기 PNG·ICO |
| `brand/test_make_icons.py` | 가공 결과 검증 |
| `brand/logo_1024.png`, `brand/app.ico` | 가공 결과(커밋) |
| `assets/brand/logo_512.png`, `assets/brand/favicon-32.png` | 웹용 로고(커밋) |
| `launcher/Options.cs` | 명령줄 옵션 파싱 |
| `launcher/MimeTypes.cs` | 확장자 → Content-Type |
| `launcher/StaticServer.cs` | TcpListener 기반 정적 서버 |
| `launcher/BrowserLauncher.cs` | Edge/Chrome/기본 브라우저 열기 |
| `launcher/Program.cs` | 시작 흐름(앱 확인·포트·중복 실행·트레이) |
| `launcher/tests/server_test.sh` | 서버 동작 테스트(curl) |
| `launcher/tests/startup_test.sh` | 시작 흐름 테스트(종료 코드) |
| `build.ps1` | 컴파일 + 패키징 + zip |
| `package/사용법.txt` | 학생·교사 안내 |
| `tests/check_vendor.sh` | 외부 CDN 참조 제거·로컬 파일 존재 확인 |
| `tests/package_test.sh` | zip 해제 후 한글 경로 실행 확인 |
| `assets/vendor/face-api/…` | 17강 라이브러리·모델 |
| `assets/vendor/fonts/…` | 25강 폰트 |
| `docs/superpowers/verification/2026-10-08-local-app.md` | 실기 검증 기록 |

---

### Task 1: 로고 가공

**Files:**
- Create: `brand/make_icons.py`, `brand/test_make_icons.py`
- Generate: `brand/logo_1024.png`, `brand/app.ico`, `assets/brand/logo_512.png`, `assets/brand/favicon-32.png`

**Interfaces:**
- Consumes: `brand/logo_source.png` (2048×2048 RGBA, 체크무늬가 실제 픽셀, 파란 사각형 bbox 약 x104–1944 / y103–1964, 워터마크 약 x1758–1855 / y1760–1855)
- Produces: `brand/app.ico`(16/24/32/48/64/128/256) — Task 2의 `/win32icon`; `assets/brand/favicon-32.png`, `assets/brand/logo_512.png` — Task 6

- [ ] **Step 1: 실패하는 테스트 작성** — `brand/test_make_icons.py`

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /c/Users/권준구/ebs && python -I brand/test_make_icons.py`
Expected: `FAIL logo_1024 exists` 등, 종료 코드 1

- [ ] **Step 3: 가공 스크립트 작성** — `brand/make_icons.py`

```python
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
    blue = (rgb[..., 2] > 180) & (rgb[..., 2] - rgb[..., 0] > 100)
    rows = np.where(blue.sum(1) > 200)[0]
    cols = np.where(blue.sum(0) > 200)[0]
    return cols.min(), rows.min(), cols.max(), rows.max()


def remove_watermark(rgb, bbox):
    """워터마크 상자를 좌우 대칭인 왼쪽 아래 모서리에서 뒤집어 복사한다. 원본보다 밝은 픽셀만 바꾼다."""
    x0, y0, x1, y1 = WM_BOX
    mx = bbox[0] + bbox[2]  # 좌우 대칭축 * 2
    src = rgb[y0:y1, mx - x1 + 1:mx - x0 + 1][:, ::-1]
    cur = rgb[y0:y1, x0:x1]
    lighter = cur.sum(-1) - src.sum(-1) > 24
    lighter = np.asarray(Image.fromarray((lighter * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    cur[lighter] = src[lighter]
    return rgb


def background_mask(rgb, bbox):
    """True = 배경. 밝은 무채색(체크무늬) 중 가장자리에서 이어진 영역 + 상자 바깥 전부."""
    h, w = rgb.shape[:2]
    grey = (rgb.max(-1) - rgb.min(-1) < 30) & (rgb.min(-1) > 150)
    m = Image.fromarray((grey * 255).astype(np.uint8))
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
```

- [ ] **Step 4: 실행 후 테스트 통과 확인**

Run: `cd /c/Users/권준구/ebs && python -I brand/make_icons.py && python -I brand/test_make_icons.py`
Expected: 모든 줄 `ok`, 종료 코드 0

- [ ] **Step 5: 눈으로 확인** — `brand/logo_1024.png`를 Read 도구로 열어 ① 테두리에 회색 체크무늬·회색 띠가 없는지 ② 우하단 반짝이가 없고 덮은 자국이 어색하지 않은지 ③ 좌측 하늘색 점이 없는지 확인. 덮은 자국이 보이면 `WM_BOX`와 임계값(24)을 조정해 Step 4부터 반복.

- [ ] **Step 6: 커밋**

```bash
git add brand/make_icons.py brand/test_make_icons.py brand/logo_1024.png brand/app.ico assets/brand/
git commit -m "로고 가공: 투명 배경·워터마크 제거, 앱 아이콘·파비콘 생성"
```

---

### Task 2: 정적 서버 실행기

**Files:**
- Create: `launcher/Options.cs`, `launcher/MimeTypes.cs`, `launcher/StaticServer.cs`, `launcher/Program.cs`(최소판), `launcher/tests/server_test.sh`, `build.ps1`(컴파일 단계만), `.gitignore`에 `dist/` 추가

**Interfaces:**
- Consumes: `brand/app.ico` (Task 1)
- Produces:
  - `Options.Parse(string[] args) → Options { int Port=47815; string Root=null; bool OpenBrowser=true; bool Quiet=false; }` — 플래그 `--port N`, `--root DIR`, `--no-browser`, `--quiet`
  - `StaticServer(string root, int port)`, `void Start()`(포트 사용 중이면 `SocketException`), `void Stop()`, 상수 `StaticServer.PingPath="/__ebs_ping"`, `StaticServer.PingBody="ebs-ai-explorer"`
  - `MimeTypes.For(string extensionWithDot) → string`
  - `build.ps1 [-SkipPackage]` → `dist\AI탐험대\AI탐험대.exe`

- [ ] **Step 1: 실패하는 테스트 작성** — `launcher/tests/server_test.sh`

```bash
#!/usr/bin/env bash
# 정적 서버 동작 테스트. 사용: bash launcher/tests/server_test.sh "dist/AI탐험대/AI탐험대.exe"
set -u
EXE="$1"; PORT=47899; BASE="http://127.0.0.1:$PORT"
WORK="$(mktemp -d)"; APP="$WORK/app"
mkdir -p "$APP/sub" "$APP/한글 폴더"
printf '<h1>hub</h1>' > "$APP/index.html"
printf '<h1>sub</h1>' > "$APP/sub/index.html"
printf 'hello' > "$APP/한글 폴더/파일 이름.txt"
printf '\0asm\1\0\0\0' > "$APP/a.wasm"
printf 'export const x=1;' > "$APP/m.mjs"
head -c 200000 /dev/urandom | gzip > "$APP/x.ent"
head -c 9000000 /dev/urandom > "$APP/big.bin"
printf 'secret' > "$WORK/secret.txt"

"$EXE" --no-browser --port $PORT --root "$(cygpath -w "$APP")" &
PID=$!
WINPID=$(cat /proc/$PID/winpid 2>/dev/null)
cleanup(){ taskkill //F //PID "$WINPID" >/dev/null 2>&1; rm -rf "$WORK"; }
trap cleanup EXIT
curl -s --retry 20 --retry-connrefused --retry-delay 1 -o /dev/null "$BASE/__ebs_ping"

FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
code(){ curl -s -o /dev/null -w '%{http_code}' --path-as-is "$@"; }
hdr(){ curl -s -o /dev/null -D - --path-as-is "$BASE$1" | tr -d '\r' | grep -i "^$2:" | head -1 | cut -d' ' -f2-; }
body(){ curl -s --path-as-is "$BASE$1"; }
sha(){ sha256sum "$1" | cut -d' ' -f1; }

check "ping body"            "$(body /__ebs_ping)" "ebs-ai-explorer"
check "root 200"             "$(code "$BASE/")" "200"
check "root body"            "$(body /)" "<h1>hub</h1>"
check "query string ok"      "$(code "$BASE/index.html?v=1")" "200"
check "html type"            "$(hdr /index.html content-type)" "text/html; charset=utf-8"
check "wasm type"            "$(hdr /a.wasm content-type)" "application/wasm"
check "mjs type"             "$(hdr /m.mjs content-type)" "text/javascript; charset=utf-8"
check "ent type"             "$(hdr /x.ent content-type)" "application/octet-stream"
check "ent no encoding"      "$(hdr /x.ent content-encoding)" ""
check "no-cache"             "$(hdr /index.html cache-control)" "no-cache"
curl -s -o "$WORK/got.ent" "$BASE/x.ent"
check "ent bytes identical"  "$(sha "$WORK/got.ent")" "$(sha "$APP/x.ent")"
check "dir redirect"         "$(code "$BASE/sub")" "301"
check "dir redirect target"  "$(hdr /sub location)" "/sub/"
check "dir index"            "$(body /sub/)" "<h1>sub</h1>"
KO=$(python -I -c "import urllib.parse;print(urllib.parse.quote('/한글 폴더/파일 이름.txt'))")
check "korean path"          "$(body "$KO")" "hello"
check "dotdot 403"           "$(code "$BASE/../secret.txt")" "403"
check "encoded dotdot 403"   "$(code "$BASE/%2e%2e/secret.txt")" "403"
check "backslash dotdot 403" "$(code "$BASE/..%5csecret.txt")" "403"
check "missing 404"          "$(code "$BASE/nope.txt")" "404"
check "post 405"             "$(code -X POST "$BASE/")" "405"
check "head length"          "$(hdr /x.ent content-length)" "$(stat -c %s "$APP/x.ent")"
check "head empty body"      "$(curl -s -I "$BASE/x.ent" -o /dev/null -w '%{size_download}')" "0"

# 동시 대용량 요청 8개 + 중간에 끊는 요청 3개 → 모두 원본과 같고 서버 생존
for i in 1 2 3; do curl -s -m 0.05 -o /dev/null "$BASE/big.bin"; done
for i in 1 2 3 4 5 6 7 8; do curl -s -o "$WORK/big$i" "$BASE/big.bin" & done; wait
ALLSAME=yes; for i in 1 2 3 4 5 6 7 8; do [ "$(sha "$WORK/big$i")" = "$(sha "$APP/big.bin")" ] || ALLSAME=no; done
check "parallel big identical" "$ALLSAME" "yes"
check "alive after aborts"   "$(body /__ebs_ping)" "ebs-ai-explorer"

exit $FAIL
```

- [ ] **Step 2: 빌드 스크립트(컴파일 단계) 작성** — `build.ps1` (UTF-8 BOM으로 저장)

```powershell
# AI 탐험대 로컬 앱 빌드. 사용: powershell -ExecutionPolicy Bypass -File build.ps1 [-SkipPackage]
param([switch]$SkipPackage)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$AppName = 'AI탐험대'
$Version = '1.0'
$Out = Join-Path $Repo "dist\$AppName"
$Exe = Join-Path $Out "$AppName.exe"
$Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

New-Item -ItemType Directory -Force $Out | Out-Null
$sources = Get-ChildItem (Join-Path $Repo 'launcher') -Filter *.cs | ForEach-Object { $_.FullName }
& $Csc /nologo /target:winexe /codepage:65001 /optimize+ "/out:$Exe" "/win32icon:$(Join-Path $Repo 'brand\app.ico')" `
  /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $sources
if ($LASTEXITCODE -ne 0) { throw "csc failed ($LASTEXITCODE)" }
Write-Host "built $Exe"

if ($SkipPackage) { return }
# 패키징 단계는 Task 7에서 추가
```

BOM 추가 명령(파일을 Write 도구로 만든 직후):
Run: `powershell -NoProfile -Command "$p='C:\Users\권준구\ebs\build.ps1'; $t=[IO.File]::ReadAllText($p); [IO.File]::WriteAllText($p,$t,(New-Object Text.UTF8Encoding $true))"`

`.gitignore` 끝에 한 줄 추가: `dist/`

- [ ] **Step 3: 컴파일 실패 확인(소스 없음)**

Run: `cd /c/Users/권준구/ebs && powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -SkipPackage`
Expected: `csc failed` (소스 파일 없음)

- [ ] **Step 4: 구현** — 네 파일 작성

`launcher/Options.cs`:
```csharp
using System;

namespace EbsLauncher
{
    // 명령줄 옵션. 학생은 옵션 없이 더블클릭, 테스트만 옵션을 쓴다.
    public sealed class Options
    {
        public int Port = 47815;
        public string Root;          // null이면 exe 옆 app\
        public bool OpenBrowser = true;
        public bool Quiet;           // 메시지 창 대신 종료 코드만

        public static Options Parse(string[] args)
        {
            var o = new Options();
            for (int i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--port": o.Port = int.Parse(args[++i]); break;
                    case "--root": o.Root = args[++i]; break;
                    case "--no-browser": o.OpenBrowser = false; break;
                    case "--quiet": o.Quiet = true; break;
                }
            }
            return o;
        }
    }
}
```

`launcher/MimeTypes.cs`:
```csharp
using System.Collections.Generic;

namespace EbsLauncher
{
    public static class MimeTypes
    {
        static readonly Dictionary<string, string> Map = new Dictionary<string, string>
        {
            { ".html", "text/html; charset=utf-8" }, { ".htm", "text/html; charset=utf-8" },
            { ".js", "text/javascript; charset=utf-8" }, { ".mjs", "text/javascript; charset=utf-8" },
            { ".css", "text/css; charset=utf-8" }, { ".json", "application/json" },
            { ".txt", "text/plain; charset=utf-8" }, { ".md", "text/plain; charset=utf-8" },
            { ".wasm", "application/wasm" },
            { ".png", "image/png" }, { ".jpg", "image/jpeg" }, { ".jpeg", "image/jpeg" },
            { ".gif", "image/gif" }, { ".svg", "image/svg+xml" }, { ".ico", "image/x-icon" }, { ".webp", "image/webp" },
            { ".woff2", "font/woff2" }, { ".woff", "font/woff" }, { ".ttf", "font/ttf" }, { ".otf", "font/otf" },
            { ".mp3", "audio/mpeg" }, { ".wav", "audio/wav" }, { ".mp4", "video/mp4" },
        };

        // .ent(gzip 원본), .task, .tflite, .bin 등은 모두 octet-stream으로 바이트 그대로 보낸다.
        public static string For(string ext)
        {
            string t;
            return Map.TryGetValue((ext ?? "").ToLowerInvariant(), out t) ? t : "application/octet-stream";
        }
    }
}
```

`launcher/StaticServer.cs`:
```csharp
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace EbsLauncher
{
    // app\ 폴더를 127.0.0.1에서만 서빙한다. GET/HEAD만, 요청마다 연결을 닫는다.
    public sealed class StaticServer
    {
        public const string PingPath = "/__ebs_ping";
        public const string PingBody = "ebs-ai-explorer";
        const int MaxHead = 16 * 1024;

        readonly string root;   // 끝에 \ 포함
        readonly TcpListener listener;
        volatile bool running;

        public StaticServer(string root, int port)
        {
            this.root = Path.GetFullPath(root).TrimEnd('\\') + "\\";
            listener = new TcpListener(IPAddress.Loopback, port);
        }

        public void Start()
        {
            listener.Start();   // 포트 사용 중이면 SocketException
            running = true;
            var t = new Thread(AcceptLoop) { IsBackground = true };
            t.Start();
        }

        public void Stop()
        {
            running = false;
            try { listener.Stop(); } catch (SocketException) { }
        }

        void AcceptLoop()
        {
            while (running)
            {
                TcpClient c;
                try { c = listener.AcceptTcpClient(); }
                catch (SocketException) { if (!running) return; continue; }
                catch (ObjectDisposedException) { return; }
                ThreadPool.QueueUserWorkItem(_ => Handle(c));
            }
        }

        void Handle(TcpClient c)
        {
            using (c)
            {
                try
                {
                    c.ReceiveTimeout = 10000;
                    c.SendTimeout = 60000;
                    var s = c.GetStream();
                    string head = ReadHead(s);
                    if (head == null) return;
                    string[] parts = head.Substring(0, head.IndexOf("\r\n", StringComparison.Ordinal)).Split(' ');
                    if (parts.Length != 3) { SendText(s, 400, "Bad Request", false); return; }
                    bool isHead = parts[0] == "HEAD";
                    if (parts[0] != "GET" && !isHead) { SendText(s, 405, "Method Not Allowed", false); return; }
                    Respond(s, parts[1], isHead);
                }
                catch (IOException) { }
                catch (SocketException) { }
                catch (ObjectDisposedException) { }
            }
        }

        static string ReadHead(Stream s)
        {
            var buf = new byte[4096];
            var acc = new MemoryStream();
            while (acc.Length < MaxHead)
            {
                int n = s.Read(buf, 0, buf.Length);
                if (n <= 0) return null;
                acc.Write(buf, 0, n);
                string text = Encoding.ASCII.GetString(acc.GetBuffer(), 0, (int)acc.Length);
                if (text.Contains("\r\n\r\n")) return text;
            }
            return null;
        }

        void Respond(Stream s, string target, bool isHead)
        {
            string path = target;
            int q = path.IndexOfAny(new[] { '?', '#' });
            string query = q >= 0 ? path.Substring(q) : "";
            if (q >= 0) path = path.Substring(0, q);

            if (path == PingPath) { SendText(s, 200, PingBody, isHead); return; }

            string decoded;
            try { decoded = Uri.UnescapeDataString(path); }
            catch (UriFormatException) { SendText(s, 400, "Bad Request", isHead); return; }
            if (decoded.IndexOf('\0') >= 0 || !decoded.StartsWith("/")) { SendText(s, 400, "Bad Request", isHead); return; }

            string full;
            try { full = Path.GetFullPath(Path.Combine(root, decoded.TrimStart('/').Replace('/', '\\'))); }
            catch (ArgumentException) { SendText(s, 400, "Bad Request", isHead); return; }
            catch (NotSupportedException) { SendText(s, 400, "Bad Request", isHead); return; }
            catch (PathTooLongException) { SendText(s, 400, "Bad Request", isHead); return; }
            if (!(full.TrimEnd('\\') + "\\").StartsWith(root, StringComparison.OrdinalIgnoreCase))
            { SendText(s, 403, "Forbidden", isHead); return; }

            if (Directory.Exists(full))
            {
                if (!path.EndsWith("/"))
                {
                    WriteHead(s, 301, "Moved Permanently", "text/plain; charset=utf-8", 0, "Location: " + path + "/" + query + "\r\n");
                    return;
                }
                full = Path.Combine(full, "index.html");
            }
            if (!File.Exists(full)) { SendText(s, 404, "Not Found", isHead); return; }

            using (var fs = new FileStream(full, FileMode.Open, FileAccess.Read, FileShare.Read, 65536))
            {
                WriteHead(s, 200, "OK", MimeTypes.For(Path.GetExtension(full)), fs.Length, "");
                if (!isHead) fs.CopyTo(s, 65536);
            }
        }

        static void SendText(Stream s, int code, string text, bool isHead)
        {
            byte[] b = Encoding.UTF8.GetBytes(text);
            WriteHead(s, code, code == 200 ? "OK" : text, "text/plain; charset=utf-8", b.Length, "");
            if (!isHead) s.Write(b, 0, b.Length);
        }

        static void WriteHead(Stream s, int code, string reason, string type, long length, string extra)
        {
            string h = "HTTP/1.1 " + code + " " + reason + "\r\n" +
                       "Content-Type: " + type + "\r\n" +
                       "Content-Length: " + length + "\r\n" +
                       "Cache-Control: no-cache\r\n" +
                       "X-Content-Type-Options: nosniff\r\n" +
                       "Connection: close\r\n" + extra + "\r\n";
            byte[] b = Encoding.ASCII.GetBytes(h);
            s.Write(b, 0, b.Length);
        }
    }
}
```

`launcher/Program.cs` (최소판 — Task 3에서 교체):
```csharp
using System;
using System.IO;
using System.Windows.Forms;

namespace EbsLauncher
{
    static class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            var opt = Options.Parse(args);
            string root = opt.Root ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app");
            var server = new StaticServer(root, opt.Port);
            server.Start();
            Application.Run();
            return 0;
        }
    }
}
```

- [ ] **Step 5: 빌드 후 테스트 통과 확인**

Run: `cd /c/Users/권준구/ebs && powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -SkipPackage && bash launcher/tests/server_test.sh "dist/AI탐험대/AI탐험대.exe"`
Expected: 모든 줄 `ok`, 종료 코드 0

- [ ] **Step 6: 커밋**

```bash
git add launcher/ build.ps1 .gitignore
git commit -m "실행기: 127.0.0.1 정적 서버(MIME·경로 탈출 차단·.ent 원본 전송) + 테스트"
```

---

### Task 3: 시작 흐름 (앱 확인·중복 실행·포트 점유·브라우저·트레이)

**Files:**
- Create: `launcher/BrowserLauncher.cs`, `launcher/tests/startup_test.sh`
- Modify: `launcher/Program.cs` (전체 교체)

**Interfaces:**
- Consumes: `Options`, `StaticServer`, `StaticServer.PingPath/PingBody` (Task 2)
- Produces: 종료 코드 계약 — `0` 정상(또는 이미 실행 중이라 창만 엶), `2` `app\index.html` 없음, `3` 포트를 다른 프로그램이 점유. `BrowserLauncher.Open(string url)`

- [ ] **Step 1: 실패하는 테스트 작성** — `launcher/tests/startup_test.sh`

```bash
#!/usr/bin/env bash
# 시작 흐름 테스트. 사용: bash launcher/tests/startup_test.sh "dist/AI탐험대/AI탐험대.exe"
set -u
EXE="$1"; WORK="$(mktemp -d)"; mkdir -p "$WORK/app" "$WORK/empty"
printf '<h1>hub</h1>' > "$WORK/app/index.html"
APPW="$(cygpath -w "$WORK/app")"
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
PIDS=()
cleanup(){ for p in "${PIDS[@]}"; do taskkill //F //PID "$p" >/dev/null 2>&1; done; rm -rf "$WORK"; }
trap cleanup EXIT

# 1) app\index.html 없음(zip 안에서 실행한 경우) → 2
"$EXE" --quiet --no-browser --port 47897 --root "$(cygpath -w "$WORK/empty")"
check "missing app exit 2" "$?" "2"

# 2) 이미 실행 중 → 두 번째 실행은 0으로 바로 종료
"$EXE" --quiet --no-browser --port 47896 --root "$APPW" &
PIDS+=("$(cat /proc/$!/winpid)")
curl -s --retry 20 --retry-connrefused --retry-delay 1 -o /dev/null http://127.0.0.1:47896/__ebs_ping
"$EXE" --quiet --no-browser --port 47896 --root "$APPW"
check "second instance exit 0" "$?" "0"

# 3) 다른 프로그램이 포트 점유 → 3
python -I -m http.server 47895 --bind 127.0.0.1 --directory "$WORK" >/dev/null 2>&1 &
PYPID=$!
curl -s --retry 20 --retry-connrefused --retry-delay 1 -o /dev/null http://127.0.0.1:47895/
"$EXE" --quiet --no-browser --port 47895 --root "$APPW"
check "port taken exit 3" "$?" "3"
kill $PYPID 2>/dev/null

exit $FAIL
```

- [ ] **Step 2: 실패 확인**

Run: `cd /c/Users/권준구/ebs && bash launcher/tests/startup_test.sh "dist/AI탐험대/AI탐험대.exe"`
Expected: FAIL (최소판은 app 확인을 안 하고, 포트 충돌 시 처리되지 않은 예외로 종료)
※ 최소판이 1)에서 `Application.Run()`으로 멈추면 Ctrl+C 후 `taskkill //F //IM "AI탐험대.exe"` 하고 실패로 판정한다.

- [ ] **Step 3: 구현**

`launcher/BrowserLauncher.cs`:
```csharp
using System;
using System.Diagnostics;
using System.IO;
using Microsoft.Win32;

namespace EbsLauncher
{
    // Edge → Chrome → 기본 브라우저 순으로 앱 창(--app)을 연다.
    public static class BrowserLauncher
    {
        public static void Open(string url)
        {
            string browser = Find("msedge.exe", @"Microsoft\Edge\Application\msedge.exe")
                          ?? Find("chrome.exe", @"Google\Chrome\Application\chrome.exe");
            if (browser != null)
            {
                try
                {
                    Process.Start(new ProcessStartInfo(browser, "--app=" + url + " --window-size=1280,860") { UseShellExecute = false });
                    return;
                }
                catch (System.ComponentModel.Win32Exception) { }
            }
            Process.Start(url);
        }

        static string Find(string exe, string rel)
        {
            foreach (var env in new[] { "ProgramFiles(x86)", "ProgramFiles", "LocalAppData" })
            {
                string dir = Environment.GetEnvironmentVariable(env);
                if (string.IsNullOrEmpty(dir)) continue;
                string p = Path.Combine(dir, rel);
                if (File.Exists(p)) return p;
            }
            foreach (var hive in new[] { Registry.CurrentUser, Registry.LocalMachine })
            {
                using (var k = hive.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\" + exe))
                {
                    string p = k == null ? null : k.GetValue(null) as string;
                    if (!string.IsNullOrEmpty(p) && File.Exists(p)) return p;
                }
            }
            return null;
        }
    }
}
```

`launcher/Program.cs` (전체 교체):
```csharp
using System;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Windows.Forms;

namespace EbsLauncher
{
    static class Program
    {
        const string Title = "AI 탐험대";

        [STAThread]
        static int Main(string[] args)
        {
            var opt = Options.Parse(args);
            string root = opt.Root ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app");
            string url = "http://127.0.0.1:" + opt.Port + "/";

            if (!File.Exists(Path.Combine(root, "index.html")))
            {
                Notify(opt, "앱 파일(app 폴더)을 찾을 수 없어요.\n\n압축 파일(zip)을 먼저 [모두 압축 풀기] 한 다음,\n풀린 폴더 안의 AI탐험대.exe를 실행해 주세요.");
                return 2;
            }

            var server = new StaticServer(root, opt.Port);
            try { server.Start(); }
            catch (SocketException)
            {
                if (IsOurServer(url))
                {
                    if (opt.OpenBrowser) BrowserLauncher.Open(url);
                    return 0;
                }
                Notify(opt, "다른 프로그램이 " + opt.Port + "번 포트를 쓰고 있어서 시작할 수 없어요.\n\n컴퓨터를 다시 시작한 뒤 실행하거나, 온라인 주소를 사용해 주세요.\nhttps://kwonjungu.github.io/ebs/");
                return 3;
            }

            if (opt.OpenBrowser) BrowserLauncher.Open(url);
            RunTray(server, url);
            return 0;
        }

        static bool IsOurServer(string url)
        {
            try
            {
                var req = (HttpWebRequest)WebRequest.Create(url.TrimEnd('/') + StaticServer.PingPath);
                req.Proxy = null;          // 학교 프록시로 새지 않게
                req.Timeout = 2000;
                using (var res = req.GetResponse())
                using (var r = new StreamReader(res.GetResponseStream()))
                    return r.ReadToEnd() == StaticServer.PingBody;
            }
            catch (WebException) { return false; }
        }

        static void Notify(Options opt, string message)
        {
            if (!opt.Quiet) MessageBox.Show(message, Title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        static void RunTray(StaticServer server, string url)
        {
            var menu = new ContextMenuStrip();
            var tray = new NotifyIcon
            {
                Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath),
                Text = Title + " 실행 중",
                ContextMenuStrip = menu,
                Visible = true,
            };
            menu.Items.Add("다시 열기", null, (s, e) => BrowserLauncher.Open(url));
            menu.Items.Add("종료", null, (s, e) => { server.Stop(); tray.Visible = false; Application.Exit(); });
            tray.DoubleClick += (s, e) => BrowserLauncher.Open(url);
            tray.ShowBalloonTip(3000, Title, "실행 중이에요. 끝낼 때는 이 나침반 아이콘을 오른쪽 클릭 → 종료", ToolTipIcon.Info);
            Application.Run();
            tray.Dispose();
        }
    }
}
```

- [ ] **Step 4: 빌드 후 두 테스트 모두 통과 확인**

Run: `cd /c/Users/권준구/ebs && powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -SkipPackage && bash launcher/tests/startup_test.sh "dist/AI탐험대/AI탐험대.exe" && bash launcher/tests/server_test.sh "dist/AI탐험대/AI탐험대.exe"`
Expected: 모든 줄 `ok`

- [ ] **Step 5: 수동 확인** — `dist\AI탐험대\`에 레포의 `index.html`·`14`~`25`·`assets`를 임시 복사(`robocopy`)하고 exe 더블클릭 → Edge 앱 창이 열리고 허브가 보이는지, 트레이 나침반 아이콘 우클릭 → 종료가 되는지 확인. exe를 다시 실행하면 앱 창이 다시 열리는지 확인.

- [ ] **Step 6: 커밋**

```bash
git add launcher/
git commit -m "실행기 시작 흐름: 앱 폴더 확인·중복 실행·포트 점유 안내·Edge 앱 창·트레이"
```

---

### Task 4: 17강 face-api 로컬화

**Files:**
- Create: `assets/vendor/face-api/face-api.js`, `assets/vendor/face-api/LICENSE`, `assets/vendor/face-api/model/` 6개 파일, `tests/check_vendor.sh`
- Modify: `17/index.html:607-608`

**Interfaces:**
- Produces: `tests/check_vendor.sh` — Task 5가 폰트 검사를 덧붙인다

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/check_vendor.sh`

```bash
#!/usr/bin/env bash
# 외부 CDN 의존 제거 확인. 사용: bash tests/check_vendor.sh
cd "$(dirname "$0")/.." || exit 1
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
exists(){ [ -s "$1" ] && echo yes || echo no; }

check "17 no jsdelivr" "$(grep -c 'cdn.jsdelivr' 17/index.html)" "0"
check "face-api.js" "$(exists assets/vendor/face-api/face-api.js)" "yes"
for m in tiny_face_detector_model face_landmark_68_model face_recognition_model; do
  check "$m.bin" "$(exists assets/vendor/face-api/model/$m.bin)" "yes"
  check "$m manifest" "$(exists assets/vendor/face-api/model/$m-weights_manifest.json)" "yes"
done
exit $FAIL
```

- [ ] **Step 2: 실패 확인**

Run: `cd /c/Users/권준구/ebs && bash tests/check_vendor.sh`
Expected: `FAIL 17 no jsdelivr: expected [0] got [2]` 등

- [ ] **Step 3: 파일 내려받기**

```bash
cd /c/Users/권준구/ebs
V=assets/vendor/face-api; B=https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15
mkdir -p $V/model
curl -sfL -o $V/face-api.js $B/dist/face-api.js
curl -sfL -o $V/LICENSE $B/LICENSE
for m in tiny_face_detector_model face_landmark_68_model face_recognition_model; do
  curl -sfL -o $V/model/$m.bin $B/model/$m.bin
  curl -sfL -o $V/model/$m-weights_manifest.json $B/model/$m-weights_manifest.json
done
ls -la $V $V/model
```
Expected 크기: face-api.js 1333943, tiny .bin 193321, landmark .bin 356840, recognition .bin 6444032

- [ ] **Step 4: 경로 교체** — `17/index.html` 607–608행

```javascript
  const FA_CDN = '../assets/vendor/face-api/face-api.js';
  const FA_MODELS = '../assets/vendor/face-api/model';
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `bash tests/check_vendor.sh`
Expected: 모든 줄 `ok`

- [ ] **Step 6: 커밋**

```bash
git add assets/vendor/face-api tests/check_vendor.sh 17/index.html
git commit -m "17강 face-api 라이브러리·모델 로컬화 (CDN 차단 학교망 대비)"
```

---

### Task 5: 25강 폰트 로컬화

**Files:**
- Create: `assets/vendor/fonts/fonts.css`, `PretendardVariable.woff2`, `Jua-Regular.ttf`, `Montserrat-Variable.ttf`, `OFL-Pretendard.txt`, `OFL-Jua.txt`, `OFL-Montserrat.txt`
- Modify: `25/index.html:607-609`, `tests/check_vendor.sh`

- [ ] **Step 1: 테스트 추가** — `tests/check_vendor.sh`의 `exit $FAIL` 바로 앞에 삽입

```bash
check "25 no google fonts" "$(grep -c 'fonts.googleapis' 25/index.html)" "0"
check "25 no jsdelivr" "$(grep -c 'cdn.jsdelivr' 25/index.html)" "0"
check "25 links fonts.css" "$(grep -c 'assets/vendor/fonts/fonts.css' 25/index.html)" "1"
for f in fonts.css PretendardVariable.woff2 Jua-Regular.ttf Montserrat-Variable.ttf; do
  check "font $f" "$(exists assets/vendor/fonts/$f)" "yes"
done
check "no CDN anywhere" "$(grep -l -E 'cdn.jsdelivr|fonts.googleapis|unpkg.com' index.html */index.html | wc -l)" "0"
```

- [ ] **Step 2: 실패 확인**

Run: `bash tests/check_vendor.sh`
Expected: `FAIL 25 no google fonts` 등

- [ ] **Step 3: 내려받기**

```bash
cd /c/Users/권준구/ebs
F=assets/vendor/fonts; mkdir -p $F
curl -sfL -o $F/PretendardVariable.woff2 https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/woff2/PretendardVariable.woff2
curl -sfL -o $F/OFL-Pretendard.txt https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/LICENSE
curl -sfL -o $F/Jua-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/jua/Jua-Regular.ttf
curl -sfL -o $F/OFL-Jua.txt https://raw.githubusercontent.com/google/fonts/main/ofl/jua/OFL.txt
curl -sfL -o $F/Montserrat-Variable.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
curl -sfL -o $F/OFL-Montserrat.txt https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/OFL.txt
ls -la $F
```
Expected: PretendardVariable.woff2 = 2057688 바이트, 나머지 0이 아닌 크기

`assets/vendor/fonts/fonts.css`:
```css
/* 25강 폰트 (로컬). 라이선스: 같은 폴더 OFL-*.txt */
@font-face { font-family: 'Pretendard Variable'; src: url('PretendardVariable.woff2') format('woff2-variations'); font-weight: 45 920; font-style: normal; font-display: swap; }
@font-face { font-family: 'Jua'; src: url('Jua-Regular.ttf') format('truetype'); font-weight: 400; font-style: normal; font-display: swap; }
@font-face { font-family: 'Montserrat'; src: url('Montserrat-Variable.ttf') format('truetype'); font-weight: 100 900; font-style: normal; font-display: swap; }
```

- [ ] **Step 4: 링크 교체** — `25/index.html` 607–609행 세 줄(`preconnect`, Google Fonts, Pretendard CDN)을 한 줄로

```html
<link rel="stylesheet" href="../assets/vendor/fonts/fonts.css">
```

- [ ] **Step 5: 테스트 통과 + 화면 확인**

Run: `bash tests/check_vendor.sh` → 모든 줄 `ok`
Task 3 Step 5의 임시 복사본을 새로 고쳐(`robocopy` 재실행) 25강을 열고, 카드 제목(Jua 둥근 글씨)·영문 라벨(Montserrat 굵은 대문자)이 이전과 같은 모양인지 온라인 버전과 나란히 비교

- [ ] **Step 6: 커밋**

```bash
git add assets/vendor/fonts tests/check_vendor.sh 25/index.html
git commit -m "25강 폰트(Pretendard·Jua·Montserrat) 로컬화"
```

---

### Task 6: 로고 적용 (favicon·허브 헤더)

**Files:**
- Modify: `index.html`(head, header), `14/index.html` ~ `25/index.html`(head)
- Create: `tests/check_brand.sh`

**Interfaces:**
- Consumes: `assets/brand/favicon-32.png`, `assets/brand/logo_512.png` (Task 1)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/check_brand.sh`

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
check "hub favicon" "$(grep -c 'rel="icon" href="assets/brand/favicon-32.png"' index.html)" "1"
check "hub logo img" "$(grep -c 'src="assets/brand/logo_512.png"' index.html)" "1"
for n in 14 15 16 17 18 19 20 21 22 23 24 25; do
  check "$n favicon" "$(grep -c 'rel="icon" href="../assets/brand/favicon-32.png"' $n/index.html)" "1"
done
exit $FAIL
```

- [ ] **Step 2: 실패 확인**

Run: `bash tests/check_brand.sh` → FAIL 13건

- [ ] **Step 3: favicon 삽입** — 각 파일의 `<meta charset="UTF-8">` 바로 다음 줄에 추가 (대소문자 다른 `<meta charset="utf-8">`도 대응)

```bash
cd /c/Users/권준구/ebs
sed -i '0,/<meta charset="[Uu][Tt][Ff]-8">/s//&\n<link rel="icon" type="image\/png" href="assets\/brand\/favicon-32.png">/' index.html
for n in 14 15 16 17 18 19 20 21 22 23 24 25; do
  sed -i '0,/<meta charset="[Uu][Tt][Ff]-8">/s//&\n<link rel="icon" type="image\/png" href="..\/assets\/brand\/favicon-32.png">/' $n/index.html
done
git diff --stat
```
Expected: 13개 파일 각 +1줄. 어느 파일에서 0줄이면 그 파일의 charset 표기를 확인해 같은 방식으로 수동 삽입.

- [ ] **Step 4: 허브 헤더에 로고** — `index.html`

`<style>` 안 `header{margin-bottom:30px}` 다음 줄에 추가:
```css
  .brandrow{display:flex;align-items:center;gap:14px;margin-bottom:16px}
  .brandrow img{width:64px;height:64px;filter:drop-shadow(3px 3px 0 var(--ink))}
  .brandrow .kicker{margin-bottom:0}
```

기존 `<span class="kicker">EBS AI 탐험대 · 중급</span>` 줄을 교체:
```html
    <div class="brandrow">
      <img src="assets/brand/logo_512.png" alt="" width="64" height="64">
      <span class="kicker">EBS AI 탐험대 · 중급</span>
    </div>
```

- [ ] **Step 5: 테스트 통과 + 화면 확인**

Run: `bash tests/check_brand.sh` → 모든 줄 `ok`
임시 복사본 갱신 후 허브를 열어 로고·제목 정렬, 탭/앱 창 아이콘이 나침반인지 확인. 폭 375px(모바일)에서도 겹치지 않는지 확인.

- [ ] **Step 6: 커밋**

```bash
git add index.html 14 15 16 17 18 19 20 21 22 23 24 25 tests/check_brand.sh
git commit -m "로고 적용: 전 페이지 favicon, 허브 헤더 로고"
```

---

### Task 7: 패키징 (사용법·zip)

**Files:**
- Create: `package/사용법.txt` (UTF-8 BOM), `tests/package_test.sh`
- Modify: `build.ps1` (패키징 단계 추가)

**Interfaces:**
- Consumes: Task 2 `build.ps1`, Task 3 종료 코드 계약, Task 4–6 결과
- Produces: `dist\AI탐험대_v1.0.zip` (최상위 폴더 `AI탐험대\`)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/package_test.sh`

```bash
#!/usr/bin/env bash
# zip을 한글·공백 경로에 풀어 실제로 서빙되는지 확인. 사용: bash tests/package_test.sh
cd "$(dirname "$0")/.." || exit 1
ZIP="dist/AI탐험대_v1.0.zip"
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
check "zip exists" "$([ -f "$ZIP" ] && echo yes || echo no)" "yes"
[ -f "$ZIP" ] || exit 1

DEST="$(mktemp -d)/바탕화면 테스트/AI탐험대 (1)"
mkdir -p "$DEST"
powershell -NoProfile -Command "Expand-Archive -LiteralPath '$(cygpath -w "$ZIP")' -DestinationPath '$(cygpath -w "$DEST")'"
ROOT="$DEST/AI탐험대"
for f in "AI탐험대.exe" "사용법.txt" "app/index.html" "app/25/index.html" "app/assets/entry/face-door.ent" "app/assets/vendor/face-api/face-api.js" "app/assets/brand/favicon-32.png"; do
  check "has $f" "$([ -f "$ROOT/$f" ] && echo yes || echo no)" "yes"
done
for d in docs brand launcher _designsystem _tools; do
  check "excludes $d" "$([ -e "$ROOT/app/$d" ] && echo yes || echo no)" "no"
done

PORT=47894; BASE="http://127.0.0.1:$PORT"
"$ROOT/AI탐험대.exe" --no-browser --port $PORT &
WINPID=$(cat /proc/$!/winpid)
trap 'taskkill //F //PID $WINPID >/dev/null 2>&1' EXIT
curl -s --retry 20 --retry-connrefused --retry-delay 1 -o /dev/null "$BASE/__ebs_ping"
for p in / /14/ /15/ /16/ /17/ /18/ /19/ /20/ /21/ /22/ /23/ /24/ /25/ /assets/mediapipe/wasm/vision_wasm_internal.wasm /assets/mediapipe/vision_bundle.mjs; do
  check "200 $p" "$(curl -s -o /dev/null -w '%{http_code}' "$BASE$p")" "200"
done
for e in emotion-dj face-door object-box voice-command; do
  curl -s -o "/tmp/$e.ent" "$BASE/assets/entry/$e.ent"
  check "ent $e identical" "$(sha256sum < "/tmp/$e.ent")" "$(sha256sum < "assets/entry/$e.ent")"
done
exit $FAIL
```

- [ ] **Step 2: 실패 확인**

Run: `bash tests/package_test.sh` → `FAIL zip exists`

- [ ] **Step 3: 사용법 작성** — `package/사용법.txt` (작성 후 Task 2의 BOM 추가 명령을 이 파일 경로로 실행)

```text
AI 탐험대 (EBS AI 탐험대 중급 14~25강 체험) 사용법
=====================================================

1. 시작하기
   - 내려받은 zip 파일을 오른쪽 클릭 → [모두 압축 풀기]
   - 풀린 폴더 안의 [AI탐험대.exe]를 더블클릭
   - 잠시 뒤 체험 화면이 새 창으로 열려요.

2. 처음 실행할 때 파란 경고 창이 뜨면
   - "Windows의 PC 보호" 창 → [추가 정보] → [실행]
   - 서명(인증서)이 없는 프로그램이라 뜨는 안내예요. 다음부터는 뜨지 않아요.

3. 카메라·마이크
   - 14~17강, 23강은 카메라나 마이크를 써요.
   - "카메라/마이크를 사용하시겠습니까?" 창이 뜨면 [허용]을 눌러 주세요.
   - 영상과 소리는 이 컴퓨터 안에서만 처리되고, 어디에도 보내지 않아요.
     (15강 음성 인식은 브라우저의 음성 인식 기능을 써서 인터넷이 필요해요.)

4. 끝내기
   - 체험 창을 닫은 뒤, 화면 오른쪽 아래 작업 표시줄의 나침반 아이콘을
     오른쪽 클릭 → [종료]
   - 창만 닫았다면 AI탐험대.exe를 다시 누르면 창이 다시 열려요.

5. 엔트리 파일
   - 15·17·18·23강의 [엔트리 파일 내려받기]를 누르면 '다운로드' 폴더에 저장돼요.
   - 엔트리(playentry.org) → [작품 불러오기]로 열어요.

6. 이럴 땐
   - "앱 파일을 찾을 수 없어요" → 압축을 풀지 않고 실행한 경우예요. 1번부터 다시.
   - exe가 실행되지 않는 컴퓨터(학교 보안 설정) → 온라인 주소를 쓰세요.
     https://kwonjungu.github.io/ebs/
   - 진행 기록은 이 컴퓨터에만 저장돼요. 다른 컴퓨터로는 옮겨지지 않아요.
   - 학생 이름 대신 닉네임이나 번호를 써 주세요.
```

- [ ] **Step 4: `build.ps1` 패키징 단계 구현** — `# 패키징 단계는 Task 7에서 추가` 줄을 아래로 교체 (BOM 유지)

```powershell
$App = Join-Path $Out 'app'
if (Test-Path $App) { Remove-Item -Recurse -Force $App }
New-Item -ItemType Directory -Force $App | Out-Null
Copy-Item (Join-Path $Repo 'index.html') $App
14..25 | ForEach-Object { Copy-Item -Recurse (Join-Path $Repo "$_") (Join-Path $App "$_") }
Copy-Item -Recurse (Join-Path $Repo 'assets') (Join-Path $App 'assets')
Get-ChildItem $App -Recurse -Filter .gitkeep | Remove-Item -Force
Copy-Item (Join-Path $Repo 'package\사용법.txt') $Out

$Zip = Join-Path $Repo "dist\${AppName}_v$Version.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($Out, $Zip, [IO.Compression.CompressionLevel]::Optimal, $true, [Text.Encoding]::UTF8)
Write-Host ("packaged {0} ({1:N1} MB)" -f $Zip, ((Get-Item $Zip).Length / 1MB))
```

- [ ] **Step 5: 빌드 후 테스트 통과 확인**

Run: `cd /c/Users/권준구/ebs && powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 && bash tests/package_test.sh`
Expected: `packaged ... (약 60 MB)`, 모든 줄 `ok`

- [ ] **Step 6: 탐색기 호환 확인** — 탐색기에서 zip을 열어 폴더·파일 이름 한글이 깨지지 않는지 눈으로 확인(탐색기 [모두 압축 풀기]로도 한 번 풀어 봄)

- [ ] **Step 7: 커밋**

```bash
git add package build.ps1 tests/package_test.sh
git commit -m "패키징: 사용법 안내, app 폴더 구성, UTF-8 zip 생성 + 한글 경로 테스트"
```

---

### Task 8: 실기 검증

**Files:**
- Create: `docs/superpowers/verification/2026-10-08-local-app.md`

자동 테스트로 못 잡는 카메라·마이크·음성·YouTube를 실제 앱 창에서 확인한다. Claude in Chrome으로 콘솔 오류를 읽을 수 있는 항목은 Chrome에서 `http://127.0.0.1:47815/`를 열어 확인하고, 카메라·마이크 권한이 필요한 항목은 사용자(선생님)가 Edge 앱 창에서 직접 확인한다.

- [ ] **Step 1:** `dist\AI탐험대_v1.0.zip`을 바탕화면 `AI탐험대 테스트\`에 탐색기로 풀고 exe 더블클릭
- [ ] **Step 2:** 아래 표를 채운다 (각 항목 결과 ✅/❌ + 메모)

```markdown
# 로컬 앱 실기 검증 (2026-10-08)

| # | 항목 | 방법 | 결과 | 메모 |
|---|---|---|---|---|
| 1 | 허브·14~25강 로딩 | 각 페이지 열고 콘솔 오류 확인 | | |
| 2 | 14강 소리 게임 | 마이크 허용 → 게이지 반응 | | |
| 3 | 15강 음성 인식 | "불 켜" 말하기 → 인식 결과 | | |
| 4 | 16강 고양이 귀 AR | 카메라 → 귀가 얼굴을 따라감 | | |
| 5 | 17강 얼굴 인식 | 등록 → 인식, 특징점 보기 | | |
| 6 | 18강 YouTube | 곡 선택 → 앱 창 안에서 재생 (안 되면 '유튜브에서 열기' 링크로 재생되는지) | | |
| 7 | 18강 복사 | 반 예시 복사 → 메모장 붙여넣기 | | |
| 8 | 23강 사물 인식 | 카메라 → 박스·이름 표시 | | |
| 9 | .ent 4종 | 내려받기 → 엔트리 [작품 불러오기]로 열림 | | |
| 10 | 25강 기록 유지 | 퀴즈 2관문 진행 → 트레이 종료 → 재실행 → 이어하기 | | |
| 11 | 중복 실행 | exe 두 번 → 창만 하나 더 | | |
| 12 | 로고 | exe·작업 표시줄·트레이·탭 아이콘이 나침반 | | |
```

- [ ] **Step 3:** ❌ 항목은 superpowers:systematic-debugging으로 원인을 찾아 해당 Task의 파일을 고치고, 고친 Task의 테스트를 다시 돌린 뒤 이 표를 갱신. 18강 YouTube가 앱 창 안에서 막혀도 기존 '유튜브에서 열기' 링크로 재생되면 ✅(메모에 기록)로 본다 — 18강에는 이미 이 링크가 있다(`18/index.html:324`, `:967`).
- [ ] **Step 4: 커밋**

```bash
git add docs/superpowers/verification/
git commit -m "로컬 앱 실기 검증 기록"
```

---

### Task 9: README·배포 준비

**Files:**
- Modify: `README.md` (맨 위에 "PC 앱으로 쓰기" 절 추가)

- [ ] **Step 1: README 맨 위 제목 다음에 추가**

```markdown
## PC 앱으로 쓰기 (Windows)

1. [Releases](https://github.com/kwonjungu/ebs/releases)에서 `AI탐험대_v1.0.zip`을 내려받아 압축을 풉니다.
2. `AI탐험대.exe`를 더블클릭하면 체험 창이 열립니다. 자세한 안내는 압축 안의 `사용법.txt`.
3. 인터넷 주소로 쓰려면: https://kwonjungu.github.io/ebs/

**빌드(개발자):** `powershell -ExecutionPolicy Bypass -File build.ps1` → `dist\AI탐험대_v1.0.zip`
테스트: `bash launcher/tests/server_test.sh dist/AI탐험대/AI탐험대.exe`, `bash launcher/tests/startup_test.sh dist/AI탐험대/AI탐험대.exe`, `bash tests/check_vendor.sh`, `bash tests/check_brand.sh`, `bash tests/package_test.sh`, `python -I brand/test_make_icons.py`
```

- [ ] **Step 2: 전체 테스트 재실행**

Run: `cd /c/Users/권준구/ebs && powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 && python -I brand/test_make_icons.py && bash launcher/tests/server_test.sh "dist/AI탐험대/AI탐험대.exe" && bash launcher/tests/startup_test.sh "dist/AI탐험대/AI탐험대.exe" && bash tests/check_vendor.sh && bash tests/check_brand.sh && bash tests/package_test.sh`
Expected: 모두 `ok`

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "README: PC 앱 사용·빌드 안내"
```

- [ ] **Step 4: 마무리** — superpowers:finishing-a-development-branch로 `local-app` 브랜치 처리(main 병합·push 여부)를 사용자에게 묻는다. push하면 GitHub Pages(온라인 버전)에도 favicon·로컬 폰트·face-api 변경이 바로 반영된다. Release 업로드(zip 첨부)는 `gh`가 설치되어 있지 않으므로 사용자가 GitHub 웹에서 직접 하거나, 사용자 확인 후 브라우저 자동화로 진행한다.
