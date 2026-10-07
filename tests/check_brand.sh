#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
FAIL=0
check(){ if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$3] got [$2]"; FAIL=1; fi; }
check "hub favicon" "$(grep -c 'rel="icon" type="image/png" href="assets/brand/favicon-32.png"' index.html)" "1"
check "hub logo img" "$(grep -c 'src="assets/brand/logo_512.png"' index.html)" "1"
for n in 14 15 16 17 18 19 20 21 22 23 24 25; do
  check "$n favicon" "$(grep -c 'rel="icon" type="image/png" href="../assets/brand/favicon-32.png"' $n/index.html)" "1"
done
exit $FAIL
