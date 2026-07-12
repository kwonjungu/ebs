# EBS AI 탐험대 중급 — 디자인 시스템

EBS 초등 AI 체험 웹의 시각 언어를 정의하는 문서이다. 모든 토큰은 CSS 커스텀 프로퍼티로 선언되어 HTML `<style>` 블록에 인라인 삽입된다. 외부 리소스(CDN·폰트 파일)를 사용하지 않는 자급 방식이다.

---

## 1. 팔레트

| 토큰 | 값 | 라이트 토큰 | 라이트 값 | 용도 |
|---|---|---|---|---|
| `--sky` | `#5B9CF6` | `--sky-light` | `#EBF3FF` | 기본 액센트, 버튼, 칩 |
| `--mint` | `#34D399` | `--mint-light` | `#D1FAE5` | 완료·성공 상태 |
| `--amber` | `#FBBF24` | `--amber-light` | `#FEF3C7` | 안내·경고 배너 |
| `--coral` | `#F87171` | `--coral-light` | `#FEE2E2` | 오류·실패 상태 |
| `--purple` | `#A78BFA` | `--purple-light` | `#EDE9FE` | 서브 액센트 |
| `--bg` | `#F0F7FF` | — | — | 페이지 배경 |
| `--card` | `#FFFFFF` | — | — | 카드 배경 |
| `--text` | `#1E293B` | — | — | 본문 |
| `--text-muted` | `#64748B` | — | — | 보조 텍스트 |
| `--border` | `#E2E8F0` | — | — | 구분선·비활성 |

---

## 2. 타이포그래피

| 역할 | 크기 | 굵기 | 비고 |
|---|---|---|---|
| 페이지 제목 `h1` | 26–30px | 900 | `letter-spacing: -0.02em` |
| 카드 제목 `h2` | 15.5–17px | 800 | `letter-spacing: -0.01em` |
| 서브 텍스트 | 13.5–15px | 400 | `color: var(--text-muted)` |
| 강 배지 | 11.5–13px | 800 | `letter-spacing: .06em` 대문자 |
| 상태 레이블 | 11–13px | 700 | 라운드 필 배지 |

폰트 스택: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` (시스템 폰트, 외부 요청 없음)

---

## 3. Radius / Shadow 토큰

| 토큰 | 값 | 사용처 |
|---|---|---|
| `--radius` | `20px` | 카드, 모달, 섹션 컨테이너 |
| `--radius-sm` | `12px` | 내부 요소, 배너, 인풋, 테이블 |
| `--shadow` | `0 4px 20px rgba(91,156,246,.12)` | 카드 기본 그림자 |
| `--shadow-lg` | `0 8px 40px rgba(91,156,246,.2)` | 카드 호버 그림자 |

---

## 4. 강별 포인트 컬러 매핑

| 강 | 포인트 컬러 | 주제 |
|---|---|---|
| 15강 | `--sky` | 소리 크기 반응 VS 음성 인식 |
| 16강 | `--purple` | 얼굴 탐지 — 고양이 귀 AR |
| 17강 | `--mint` | 얼굴 인식 문지기 |
| 18강 | `--coral` | 감정 분석 AI DJ |
| 20강 | `--amber` | 프롬프트 마스코트 |
| 21강 | `--sky` | AI 기사 편집장 |
| 22강 | `--coral` | 팩트체크 탐정 |
| 23강 | `--mint` | 객체 탐지 네모 박스 |
| 24강 | `--amber` | AI 편향 탐정 |
| 25강 | `--purple` | AI 탐험가 라이선스 발급 |

포인트 컬러는 CSS 커스텀 프로퍼티 `--accent`로 카드에 `style="--accent:var(--sky)"` 형태로 주입된다.

---

## 5. 컴포넌트 목록

| 파일 | 그룹 | 이름 | 설명 |
|---|---|---|---|
| `hub/lesson-grid.html` | Hub | 강별 카드 그리드 | 포인트 컬러 상단 보더 5px, 강 배지, 이모지 우상단 |
| `components/pipeline-node.html` | Components | 파이프라인 노드 | 번호 원 + 텍스트, 기본/진행/완료/실패 상태 4종 |
| `foundations/colors.html` | Foundations | 컬러 팔레트 | 색상 토큰 스와치 전체 |

---

## 6. 시그니처 패턴

| 패턴 | 상세 |
|---|---|
| 허브 헤더 배경 | 점선 나침반 경로 SVG (`stroke-dasharray:6 5`, opacity 0.18) repeat-x |
| 파형(waveform) 모티프 | 9개 `span` 막대 + `@keyframes waverise`, `.active` 클래스로만 애니메이션 발동 |
| 안전 배너 | `--amber-light` 배경 라운드 박스, 🛡️ 아이콘, 개인정보 안내 문구 필수 |
| 카드 호버 | `translateY(-4px)` + `--shadow-lg` 전환, 이모지 `rotate(12deg)` |
| 상태 배지 | 라운드 필(border-radius:999px), 상태별 라이트 배경 + 포인트 텍스트 |

---

## 7. 콘텐츠·톤 원칙

- **하우영 톤 ~해요체**: 모든 UI 텍스트는 "~해요" 종결어미 사용. 명령어가 아닌 안내 말투.
- **개인정보 안내 필수**: 카메라·마이크를 사용하는 모든 강(15, 16, 17, 23강 등)에는 "내 목소리/얼굴은 화면에만 쓰이고 저장되지 않아요." 문구를 `safe` 배너로 표시해야 한다.
- **외부 리소스 0**: 각 HTML은 단일 문서로 완결. CDN·외부 폰트 금지.
- **접근성**: 인터랙티브 요소에 `focus-visible` 아웃라인, `prefers-reduced-motion` 미디어 쿼리 대응 필수.
