# AI 탐험대 Windows 로컬 앱 — 설계

- 작성일: 2026-10-08
- 대상 레포: kwonjungu/ebs (브랜치 `local-app`)

## 1. 목표

GitHub Pages로 서비스 중인 중급 14~25강 체험 웹앱을 **Windows PC에서 zip을 받아 풀고 exe를 더블클릭하면 그대로 작동**하는 로컬 앱으로 만든다.

- 대상: 학교 Windows 10/11 PC (관리자 권한 없음 가정)
- 전제: 인터넷 연결됨 (15강 음성 인식, 18강 YouTube는 인터넷 사용)
- 성공 기준: 14~25강의 모든 체험(마이크·카메라·MediaPipe·face-api·음성 인식·YouTube·클립보드·저장)과 엔트리 `.ent` 4종 내려받기가 온라인 버전과 똑같이 동작
- 웹앱 구조(허브 `index.html` + `14/`~`25/` + `assets/`)는 그대로 유지하고, GitHub Pages 온라인 버전도 계속 서비스한다

## 2. 왜 로컬 서버인가

`index.html` 더블클릭(`file://`)으로는 안 되는 것들이 있다.

- 16·23강: `type="module"` + `import()`로 MediaPipe 로딩 → `file://`에서 차단
- 14~17·23강: `getUserMedia`(카메라·마이크)는 보안 컨텍스트(`localhost`/`https`)에서만 확실히 동작
- 18강: `navigator.clipboard`도 보안 컨텍스트 필요
- `localStorage`는 출처(origin)별로 저장 → 주소가 매번 같아야 기록이 이어짐

그래서 `http://127.0.0.1:<고정 포트>`로 서빙하는 작은 실행기를 둔다. 검토한 대안:

| 방식 | 기각 이유 |
|---|---|
| Electron | 200MB+, Electron 안에서는 Web Speech API(15강)가 동작하지 않음 |
| PWA 설치 | 첫 실행에 인터넷·설치 권한 필요, 학교 PC 정책에 막히기 쉬움 |
| Python/Node 서버 동봉 | 런타임 크기·설치 문제, 더블클릭 한 번이 안 됨 |

## 3. 배포 형태

```
AI탐험대\                 ← AI탐험대_vX.Y.zip 압축 해제
  AI탐험대.exe            ← 실행기 (로고 아이콘)
  사용법.txt
  app\                    ← 레포의 index.html, 14~25, assets 그대로 복사
```

- 배포: GitHub Releases에 zip 업로드 (약 60MB)
- 레포 산출물 위치: 실행기 소스 `launcher/`, 빌드 스크립트 `build.ps1`, 로고 원본·가공본 `brand/`, 빌드 결과 `dist/`(git 제외)
- `docs/`, `_designsystem/`, `_tools/` 등 개발용 폴더는 zip에 넣지 않는다

## 4. 실행기 `AI탐험대.exe`

### 4.1 구현
- 언어: C#, Windows 내장 .NET Framework 4.x 컴파일러(`%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`)로 빌드 → 별도 SDK 설치 불필요, 모든 Windows 10/11에서 실행
- `/target:winexe` (콘솔 창 없음), `/win32icon:brand\app.ico`
- 단일 파일, 외부 DLL 없음

### 4.2 동작 순서
1. exe 옆 `app\index.html` 존재 확인 → 없으면 "압축을 먼저 풀어 주세요" 안내 후 종료 (zip 안에서 바로 실행한 경우 대비)
2. 고정 포트 `47815`에 `TcpListener(IPAddress.Loopback)` 바인드
   - 성공 → 서버 시작
   - 실패 시 `http://127.0.0.1:47815/__ebs_ping` 요청 → 응답이 우리 앱이면 "이미 실행 중"으로 보고 창만 다시 열고 종료
   - 다른 프로그램이 포트 점유 → 안내 메시지 후 종료 (포트를 바꾸면 기록이 끊기므로 자동 변경하지 않음)
3. 브라우저 열기 (앱 창 모드)
   - Edge(`msedge.exe`, Program Files(x86)/Program Files/레지스트리 App Paths 순 탐색) `--app=http://127.0.0.1:47815/`
   - 없으면 Chrome 같은 방식, 그것도 없으면 기본 브라우저(`Process.Start(url)`)
4. 트레이 아이콘(NotifyIcon, 로고): 메뉴 "다시 열기" / "종료". 종료 시 리스너 닫고 프로세스 종료

`127.0.0.1` 루프백 바인드이므로 방화벽 경고가 뜨지 않고 외부에서 접속할 수 없다. 관리자 권한 불필요(HttpListener의 URL 예약 문제를 피하려고 TcpListener로 직접 구현).

### 4.3 정적 파일 서버 규칙
- GET/HEAD만 처리, 요청마다 스레드풀에서 처리
- URL 디코딩(UTF-8, 한글 파일명) 후 `app\` 기준 경로로 변환, `Path.GetFullPath` 결과가 `app\` 밖이면 403 (경로 탈출 방지)
- 디렉터리 요청은 `index.html`, `/14` → `/14/` 리디렉션(상대 경로 `../assets` 정상화)
- **압축 인코딩을 절대 붙이지 않는다**: `.ent`는 gzip 원본이므로 `Content-Encoding` 없이 `application/octet-stream`으로 바이트 그대로 전송 → 내려받은 파일이 원본과 바이트 단위로 같아야 함
- MIME 표:

| 확장자 | Content-Type |
|---|---|
| .html | text/html; charset=utf-8 |
| .js .mjs | text/javascript; charset=utf-8 |
| .css | text/css; charset=utf-8 |
| .json | application/json |
| .wasm | application/wasm |
| .png .jpg .svg .ico .webp | 각 image 타입 |
| .woff2 .woff .ttf | font 타입 |
| .ent .task .tflite 기타 | application/octet-stream |

- `Cache-Control: no-cache` (앱 업데이트 후 옛 파일이 남지 않도록)
- Range 요청은 처리하지 않는다(현재 앱에 동영상·오디오 파일 없음)
- `/__ebs_ping` → 고정 문자열 응답(중복 실행 판별용)

## 5. 웹앱 쪽 수정 (최소한)

| 대상 | 수정 |
|---|---|
| 17강 | face-api(`@vladmandic/face-api@1.7.15`) js와 사용하는 모델 파일을 `assets/vendor/face-api/`에 저장, 로컬 경로 우선 로딩 |
| 25강 | Jua·Montserrat(Google Fonts), Pretendard Variable을 `assets/vendor/fonts/`에 저장, `@font-face` 로컬 참조 |
| 18강 | YouTube 임베드가 `127.0.0.1` 출처에서 막히는지 실측 → 막히면 "YouTube에서 열기" 새 창 링크로 폴백 (온라인 버전 동작은 유지) |
| 허브 | 로고·favicon 추가 |
| 전 페이지 | `<link rel="icon">` 추가 |

수정은 온라인(GitHub Pages)과 로컬 양쪽에서 같은 코드로 동작해야 한다. 로컬 전용 분기는 두지 않는다.

## 6. 로고

- 원본: `brand/logo_source.png` (Gemini 생성, 2048×2048, A안: 나침반 + AI 반짝임)
- 원본의 문제와 처리:
  - 체크무늬가 실제 픽셀로 그려진 가짜 투명 → 둥근 사각형 바깥을 마스크로 지워 진짜 알파 채널 생성
  - 우하단 Gemini 워터마크(반짝이) → 주변 파란색으로 덮기
  - 좌측 가장자리 하늘색 잔여 픽셀 → 마스크로 함께 제거
- 산출물: `brand/logo_1024.png`(투명), `brand/app.ico`(16/24/32/48/64/128/256) — zip 제외 / `assets/brand/logo_512.png`, `assets/brand/favicon-32.png` — 웹에서 쓰므로 zip 포함
- 적용: exe 아이콘, 트레이 아이콘, 허브 헤더, 전 페이지 favicon
- 가로형(로고 + "AI 탐험대") 표기는 이미지가 아닌 HTML 텍스트로 붙인다

## 7. 빌드 `build.ps1`

1. 로고 가공(Python 스크립트 `brand/make_icons.py`, 결과물은 레포에 커밋 → 빌드 PC에 Python 없어도 됨)
2. `csc.exe`로 `launcher/*.cs` → `dist\AI탐험대\AI탐험대.exe`
3. 앱 파일 복사: `index.html`, `14`~`25`, `assets` → `dist\AI탐험대\app\`
4. `사용법.txt` 복사
5. `dist\AI탐험대_v<버전>.zip` 생성

## 8. 사용법.txt (학생·교사용)

- 압축을 먼저 풀고 `AI탐험대.exe` 실행
- 첫 실행 SmartScreen "Windows의 PC 보호" → [추가 정보] → [실행] (서명 없는 exe라서 뜸)
- 카메라·마이크 허용 창이 뜨면 [허용]
- 끝낼 때는 작업 표시줄 오른쪽 나침반 아이콘 → 종료
- exe 실행이 막힌 PC: 온라인 주소 `https://kwonjungu.github.io/ebs/` 사용
- 기록은 이 PC의 브라우저에 저장됨(다른 PC로 옮겨지지 않음)

## 9. 검증 (완료 판정 기준)

실제로 exe를 실행해서 확인한다.

| # | 항목 | 확인 방법 |
|---|---|---|
| 1 | 허브·14~25강 12페이지 로딩 | 각 페이지 열어 콘솔 오류 0건 |
| 2 | MIME | `.wasm` `.mjs` `.html` 응답 헤더 확인 |
| 3 | 16·23강 MediaPipe | 카메라 켜고 얼굴/사물 박스 표시 |
| 4 | 17강 face-api | 인터넷 CDN 차단 상태에서도 모델 로딩 |
| 5 | 14·15강 마이크 | 게이지 반응, 15강 음성 인식 결과 출력 |
| 6 | 18강 YouTube | 재생되거나 폴백 링크 표시 |
| 7 | 18강 클립보드 | 복사 동작 |
| 8 | .ent 4종 | 내려받은 파일 SHA-256 = 레포 원본 |
| 9 | 기록 유지 | 25강 진행 → exe 종료·재실행 → 이어하기 |
| 10 | 중복 실행 | exe 두 번 실행 → 창만 하나 더 열림 |
| 11 | 경로 탈출 | `/../` 요청 403 |
| 12 | 다른 PC | 압축 해제 경로에 한글·공백 포함(바탕화면\AI탐험대) 상태로 실행 |

카메라·마이크·음성은 자동화가 어려우므로 권한 허용 후 수동 확인하고 결과를 기록한다.

## 10. 범위 밖

- Mac·크롬북·태블릿
- 완전 오프라인(15강 음성 인식·18강 YouTube)
- 코드서명 인증서, 자동 업데이트, 설치 프로그램(MSI)
