#!/usr/bin/env bash
# 시작 흐름 테스트. 사용: bash launcher/tests/startup_test.sh "dist/AI탐험대/AI탐험대.exe"
set -u
EXE="$1"; WORK="$(mktemp -d)"; mkdir -p "$WORK/app" "$WORK/empty"
printf '<h1>hub</h1>' > "$WORK/app/index.html"
APPW="$(cygpath -w "$WORK/app")"
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
kill_port(){ for p in $(netstat -ano | tr -d '' | awk -v a="127.0.0.1:$1" '$2==a && $4=="LISTENING"{print $5}' | sort -u); do taskkill //F //PID "$p" >/dev/null 2>&1; done; }
cleanup(){ kill_port 47896; kill_port 47895; rm -rf "$WORK"; }
trap cleanup EXIT

# 1) app\index.html 없음(zip 안에서 실행한 경우) → 2
"$EXE" --quiet --no-browser --port 47897 --root "$(cygpath -w "$WORK/empty")"
check "missing app exit 2" "$?" "2"

# 2) 이미 실행 중 → 두 번째 실행은 0으로 바로 종료
"$EXE" --quiet --no-browser --port 47896 --root "$APPW" >/dev/null 2>&1 &
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
