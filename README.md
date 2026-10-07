# EBS AI 탐험대 중급 14~25강 체험

## PC 앱으로 쓰기 (Windows)

1. [Releases](https://github.com/kwonjungu/ebs/releases)에서 `AI탐험대_v1.0.zip`을 내려받아 압축을 풉니다.
2. `AI탐험대.exe`를 더블클릭하면 체험 창이 열립니다. 자세한 안내는 압축 안의 `사용법.txt`.
3. 인터넷 주소로 쓰려면: https://kwonjungu.github.io/ebs/

**빌드(개발자):** `powershell -ExecutionPolicy Bypass -File build.ps1` → `dist\AI탐험대_v1.0.zip`
테스트: `bash launcher/tests/server_test.sh dist/AI탐험대/AI탐험대.exe`, `bash launcher/tests/startup_test.sh dist/AI탐험대/AI탐험대.exe`, `bash tests/check_vendor.sh`, `bash tests/check_brand.sh`, `bash tests/package_test.sh`, `python -I brand/test_make_icons.py`

## 25강 · AI 탐험가 라이선스 발급 미션

중급 25차시 종합 정리 활동을 게임형 웹앱으로 만든 것입니다. 설치 없이 `index.html`을 브라우저로 열면 됩니다.

**흐름** (교재 25차시 구성 그대로):
배지 퀴즈 6관문(분류·예측·군집화·생성형 AI 확인·안전·윤리·사람 확인) → 나만의 AI 서비스 설계(포트폴리오 6칸) + 안전 방패 2개 이상 → AI 탐험가 다짐·서명 → 라이선스 카드 발급(도장·색종이) → 우리 반 갤러리

**게임 요소**
- 효과음: 정답 딩동·오답 부저·배지 팡파레·도장 쾅·발급 팡파레 (Web Audio 합성 — 파일 불필요, 우하단 🔊 버튼으로 끄기)
- XP 진행 바, 무오답 통과 시 🏆 리본
- 자동 저장·이어하기 (같은 브라우저에서 새로 고침해도 진행 유지)
- 이미지 에셋 자동 인식: `assets/` 폴더에 [ASSET_PROMPTS.md](ASSET_PROMPTS.md)의 파일명으로 넣으면 이모지 대신 그림 사용

**주의**: 학생 이름 대신 닉네임·번호 사용을 권장합니다(개인정보). 모든 데이터는 학생 브라우저(localStorage)에만 저장됩니다.
