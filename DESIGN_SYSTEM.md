# EBS AI 탐험대 체험 웹 — 디자인 언어 v2 (뉴트로 팝 / MZ)

기준 구현: **/15/index.html** — 모든 강·허브가 이 디자인 언어를 따른다.

## 핵심 원칙 (AI 템플릿 룩 금지)
- **이모지를 아이콘으로 쓰지 않는다.** 아이콘·그래픽은 인라인 SVG(먹색 아웃라인 스타일)로 직접 그린다. 본문 안 강조용 이모지 1~2개는 허용하되 UI 요소(버튼·헤더·배지)엔 금지.
- **색을 절제한다.** 크림 베이스 + 먹색(잉크) + 강별 포인트 1색. 파스텔 다색 남발 금지. 보조색(성공 그린·경고 레드·강조 앰버)은 상태 표현에만.
- **둥근 그림자 카드 반복 금지.** 모든 면은 먹색 아웃라인 + 하드 오프셋 섀도우.

## 토큰 (:root, 전 페이지 공통)
```css
--ink:#141414; --paper:#FBF7EC; --surface:#FFFFFF;
--amber:#FFB800; --amber-soft:#FFF0C7;
--green:#12B76A; --red:#FF4D4D; --muted:#6B6B6B;
--r:20px; --r-sm:13px;
--hard:5px 5px 0 var(--ink); --hard-sm:3px 3px 0 var(--ink);
/* 강별 포인트(--point, --point-soft)만 교체 */
```
강별 포인트 컬러(비비드):
15 코발트 `#3D5AFE`/`#E4E8FF` · 16 퍼플 `#7C3AED`/`#EDE7FF` · 17 그린 `#12B76A`/`#D6F5E6` ·
18 코랄 `#FF5A5F`/`#FFE3E4` · 20 앰버 `#F59E0B`/`#FFF0C7` · 21 코발트 `#3D5AFE`/`#E4E8FF` ·
22 코랄 `#FF5A5F`/`#FFE3E4` · 23 그린 `#12B76A`/`#D6F5E6` · 24 앰버 `#F59E0B`/`#FFF0C7` · 허브 코발트.

## 필수 요소 (모든 페이지)
1. **배경**: `--paper` + 미세 도트 그리드 `radial-gradient(var(--ink) .5px, transparent .5px); background-size:22px 22px`.
2. **상단 nav**: 왼쪽 `← 전체 목록`(아웃라인 pill), 오른쪽 강 배지(포인트색 pill). 둘 다 hover 시 `translate(-1px,-1px)`+섀도우 커짐, active 시 눌림.
3. **히어로**: kicker(앰버 아웃라인 라벨, uppercase 트래킹) → H1 `clamp(30px,7vw,52px)` weight 900 자간 -0.035em → lead(muted, 600).
4. **면(패널·카드·표·박스)**: `border:2.5~3px solid var(--ink)` + `box-shadow:var(--hard)` + radius. 흰/크림/포인트-soft 배경.
5. **버튼**: 아웃라인 + `--hard-sm`, hover 뜸/active 눌림(`translate(3px,3px);box-shadow:0`). 주버튼 앰버 또는 포인트색. 녹음/진행 중 red `.rec`.
6. **아이콘**: SVG, `stroke:var(--ink) stroke-width:2~3`, 채움은 포인트/앰버.
7. **관찰 박스**: 먹색 배경(`--ink`) + 크림 텍스트 반전, 앰버 강조 `b`.
8. **표**: 먹색 헤더 반전, 셀 먹색 구분선, 포인트-soft 강조열.
9. **footer**: 아웃라인 pill `← AI 탐험대 체험 전체 목록`.

## 접근성 (유지)
- 모든 애니메이션 `@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}`.
- `:focus-visible{outline:3px solid var(--point);outline-offset:3px}`.
- 진행바 role=progressbar/meter + aria-valuenow, 상호작용 요소 aria-label, 장식 aria-hidden. 터치 44px+.

## 절대 금지
- 기능(JS 로직·카메라·마이크·MediaPipe)·안내 문구 의미 변경 금지. id·함수 시그니처 유지.
- 버튼 라벨을 JS가 textContent로 바꾸는 경우, 그 문자열의 이모지도 함께 제거(SVG 아이콘은 버튼 텍스트 밖에 배치).
