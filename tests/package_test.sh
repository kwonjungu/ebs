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
kill_port(){ for p in $(netstat -ano | tr -d '\r' | awk -v a="127.0.0.1:$1" '$2==a && $4=="LISTENING"{print $5}' | sort -u); do taskkill //F //PID "$p" >/dev/null 2>&1; done; }
trap 'kill_port $PORT' EXIT
"$ROOT/AI탐험대.exe" --no-browser --port $PORT >/dev/null 2>&1 &
curl -s --retry 20 --retry-connrefused --retry-delay 1 -o /dev/null "$BASE/__ebs_ping"
for p in / /14/ /15/ /16/ /17/ /18/ /19/ /20/ /21/ /22/ /23/ /24/ /25/ /assets/mediapipe/wasm/vision_wasm_internal.wasm /assets/mediapipe/vision_bundle.mjs; do
  check "200 $p" "$(curl -s -o /dev/null -w '%{http_code}' "$BASE$p")" "200"
done
for e in emotion-dj face-door object-box voice-command; do
  curl -s -o "$DEST/$e.ent" "$BASE/assets/entry/$e.ent"
  check "ent $e identical" "$(sha256sum < "$DEST/$e.ent")" "$(sha256sum < "assets/entry/$e.ent")"
done
exit $FAIL
