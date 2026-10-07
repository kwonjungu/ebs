#!/usr/bin/env bash
# 실행기 테스트 전체. 사용: bash launcher/tests/run_all.sh "dist/AI탐험대/AI탐험대.exe"
cd "$(dirname "$0")/../.." || exit 1
bash launcher/tests/startup_test.sh "$1" && bash launcher/tests/server_test.sh "$1"
