# AI 탐험대 로컬 앱 빌드. 사용: powershell -ExecutionPolicy Bypass -File build.ps1 [-SkipPackage]
param([switch]$SkipPackage)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$AppName = 'AI탐험대'
$Version = '1.0'
$Out = Join-Path $Repo "dist\$AppName"
$Exe = Join-Path $Out "$AppName.exe"
$Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

New-Item -ItemType Directory -Force $Out | Out-Null
$sources = Get-ChildItem (Join-Path $Repo 'launcher') -Filter *.cs | ForEach-Object { $_.FullName }
& $Csc /nologo /target:winexe /codepage:65001 /optimize+ "/out:$Exe" "/win32icon:$(Join-Path $Repo 'brand\app.ico')" `
  /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $sources
if ($LASTEXITCODE -ne 0) { throw "csc failed ($LASTEXITCODE)" }
Write-Host "built $Exe"

if ($SkipPackage) { return }
# 패키징 단계는 Task 7에서 추가
