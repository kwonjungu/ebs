# EBS AI 탐험대 체험 웹 — 디자인 시스템 (레퍼런스: 25강 라이선스 앱)

모든 강(/15 ~ /25) 페이지는 **단일 index.html**(외부 프레임워크 없음, CDN 라이브러리만 허용)로 만들고 아래 시스템을 따른다.

## 1. 컬러 토큰 (:root — 25강 앱과 동일하게 복사)
```css
:root {
  --sky: #5B9CF6;      --sky-light: #EBF3FF;
  --mint: #34D399;     --mint-light: #D1FAE5;
  --amber: #FBBF24;    --amber-light: #FEF3C7;
  --coral: #F87171;    --coral-light: #FEE2E2;
  --purple: #A78BFA;   --purple-light: #EDE9FE;
  --bg: #F0F7FF;  --card: #FFFFFF;
  --text: #1E293B;  --text-muted: #64748B;  --border: #E2E8F0;
  --radius: 20px;  --radius-sm: 12px;
  --shadow: 0 4px 20px rgba(91,156,246,0.12);
  --shadow-lg: 0 8px 40px rgba(91,156,246,0.2);
}
```
- 강별 포인트 컬러 1개를 정해 헤더·주요 버튼에 사용 (15강=sky, 16강=purple, 17강=mint, 18강=coral, 19강=purple, 20강=amber, 21강=sky, 22강=coral, 23강=mint, 24강=amber, 25강=기존).

## 2. 타이포·기본
- `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;` body 17px/1.6.
- `* { box-sizing: border-box; margin:0; padding:0; }`
- 제목은 짧고 큼직하게, 이모지 1개 허용.

## 3. 공통 레이아웃 패턴
- **상단 진행 바(progress-bar)**: sticky, 흰 배경, 단계 칩(①②③④). 25강 앱의 `.progress-bar/.progress-step` 패턴 재사용.
- **카드(.card)**: 흰 배경, `border-radius: var(--radius)`, `box-shadow: var(--shadow)`, padding 24px, max-width 720px 중앙 정렬.
- **큰 실행 버튼**: 포인트 컬러 배경, 흰 글씨, radius-sm, :active scale(0.97).
- **구조 원칙(저자 확정)**: 수업 흐름을 따라가는 코스형이 아니라 **기능 하나를 바로 체험하는 단일 화면 데모**. 진행 바·퀴즈·배지 없음. 구성 = [제목+한 줄 설명] → [체험 위젯(핵심)] → [관찰 포인트 1~2줄] → [안전 문구 한 줄]. 스크롤 1~2화면 이내.
- 안전 문구는 체크박스 강제 없이 상단/하단 한 줄로.

## 4. 어투 (하우영 톤)
- 안내문 "~해요"체, 버튼은 명사형("시작하기", "다시 듣기").
- 쿠션어·AI 번역투 금지("~을 통해", "다양한" 등).
- 개인정보 안내 문구 필수: 카메라/마이크를 쓰는 강은 "화면에만 보이고 저장되지 않아요" + "이름·주소 같은 개인정보는 말하지/보여주지 않아요".

## 5. 기술 규칙
- 서버 없음(GitHub Pages 정적 호스팅). API 키 요구 금지.
- 허용 CDN: MediaPipe Tasks Vision(jsdelivr), 그 외 금지. 나머지는 바닐라 JS.
- 카메라·마이크 실패/미지원 시 **반드시 시뮬레이션 모드 폴백** 제공(체험이 끊기지 않게).
- 모바일(태블릿) 우선: 터치 target 44px 이상, viewport meta 필수.
- 마지막 단계에서 배지/완료 화면 (25강 앱의 배지 감성).

## 6. 파일 구조
```
/            index.html   ← 통합 허브(전 강 목록)
/15 ~ /24    index.html   ← 강별 체험(단일 파일)
/25          index.html   ← 기존 라이선스 앱(이동 완료)
/assets      공용 이미지(기존 배지·마루 등)
/_설계       강별 설계서 md
```
- 각 강 페이지 하단에 「← 전체 목록」(../) 링크.
