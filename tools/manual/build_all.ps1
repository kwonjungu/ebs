# 설명서 한 번에 만들기: 그림 캡처 -> 설명서.html/pdf + 빠른안내.html/pdf -> 검수.
# 사용: powershell -ExecutionPolicy Bypass -File tools\manual\build_all.ps1
# 사전: pip install playwright pillow pypdf  (Edge가 있으면 브라우저 내려받기는 필요 없어요)
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Exe = Join-Path $Repo 'dist\AI탐험대\AI탐험대.exe'
$env:PYTHONIOENCODING = 'utf-8'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'python 이 없어요. Python 3 을 설치해 주세요.' }
python -c "import playwright, PIL" 2>$null
if ($LASTEXITCODE -ne 0) { throw '필요한 패키지가 없어요. 먼저 실행: pip install playwright pillow pypdf' }
if (-not (Test-Path $Exe)) { throw "앱이 아직 없어요 ($Exe). 먼저 build.ps1 을 돌려 주세요: powershell -ExecutionPolicy Bypass -File build.ps1" }

Push-Location $Repo
try {
  python tools\manual\capture.py
  if ($LASTEXITCODE -ne 0) { throw "그림 캡처 실패 ($LASTEXITCODE)" }
  python tools\manual\build_manual.py
  if ($LASTEXITCODE -ne 0) { throw "설명서 만들기/검수 실패 ($LASTEXITCODE)" }
  Write-Host '설명서 완료: package\설명서.html/.pdf, package\빠른안내.html/.pdf, package\manual_img\'
} finally { Pop-Location }
