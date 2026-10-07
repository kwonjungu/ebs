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

"$EXE" --no-browser --port $PORT --root "$(cygpath -w "$APP")" >/dev/null 2>&1 &
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
CPIDS=(); for i in 1 2 3 4 5 6 7 8; do curl -s -o "$WORK/big$i" "$BASE/big.bin" & CPIDS+=($!); done; wait "${CPIDS[@]}"  # 서버 프로세스는 기다리지 않음
ALLSAME=yes; for i in 1 2 3 4 5 6 7 8; do [ "$(sha "$WORK/big$i")" = "$(sha "$APP/big.bin")" ] || ALLSAME=no; done
check "parallel big identical" "$ALLSAME" "yes"
check "alive after aborts"   "$(body /__ebs_ping)" "ebs-ai-explorer"

exit $FAIL
