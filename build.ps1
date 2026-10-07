# AI 탐험대 로컬 앱 빌드. 사용: powershell -ExecutionPolicy Bypass -File build.ps1 [-SkipPackage]
param([switch]$SkipPackage)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$AppName = 'AI탐험대'
$Version = '1.0'
$Out = Join-Path $Repo "dist\$AppName"
$Exe = Join-Path $Out "$AppName.exe"
$Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $Csc)) { $Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe' }

# 지난 빌드 찌꺼기가 zip에 섞이지 않게 비우고 시작 (dist의 exe가 실행 중이면 여기서 멈춤 → 트레이에서 종료 후 다시)
if (Test-Path $Out) { Remove-Item -Recurse -Force $Out }
New-Item -ItemType Directory -Force $Out | Out-Null
$sources = Get-ChildItem (Join-Path $Repo 'launcher') -Filter *.cs | ForEach-Object { $_.FullName }
& $Csc /nologo /target:winexe /codepage:65001 /optimize+ "/out:$Exe" "/win32icon:$(Join-Path $Repo 'brand\app.ico')" `
  /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $sources
if ($LASTEXITCODE -ne 0) { throw "csc failed ($LASTEXITCODE)" }
Write-Host "built $Exe"

if ($SkipPackage) { return }
$App = Join-Path $Out 'app'
if (Test-Path $App) { Remove-Item -Recurse -Force $App }
New-Item -ItemType Directory -Force $App | Out-Null
Copy-Item (Join-Path $Repo 'index.html') $App
14..25 | ForEach-Object { Copy-Item -Recurse (Join-Path $Repo "$_") (Join-Path $App "$_") }
Copy-Item -Recurse (Join-Path $Repo 'assets') (Join-Path $App 'assets')
Get-ChildItem $App -Recurse -Filter .gitkeep | Remove-Item -Force
Copy-Item (Join-Path $Repo 'package\사용법.txt') $Out

$Zip = Join-Path $Repo "dist\${AppName}_v$Version.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($Out, $Zip, [IO.Compression.CompressionLevel]::Optimal, $true, [Text.Encoding]::UTF8)
Write-Host ("packaged {0} ({1:N1} MB)" -f $Zip, ((Get-Item $Zip).Length / 1MB))
