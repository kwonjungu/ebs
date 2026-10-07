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
check "25 no google fonts" "$(grep -c 'fonts.googleapis' 25/index.html)" "0"
check "25 no jsdelivr" "$(grep -c 'cdn.jsdelivr' 25/index.html)" "0"
check "25 links fonts.css" "$(grep -c 'assets/vendor/fonts/fonts.css' 25/index.html)" "1"
for f in fonts.css PretendardVariable.woff2 Jua-Regular.ttf Montserrat-Variable.ttf; do
  check "font $f" "$(exists assets/vendor/fonts/$f)" "yes"
done
check "no CDN anywhere" "$(grep -l -E 'cdn.jsdelivr|fonts.googleapis|unpkg.com' index.html */index.html | wc -l)" "0"
exit $FAIL
