# Unpacks orefishfarm-project.zip (Jake's Ore Fish Farm, from Claude) into ..\JakesOreFishFarm, builds it and
# installs the jar into the pack. Run from the Quicreate folder:
#   powershell -ExecutionPolicy Bypass -File .\build-orefishfarm.ps1
# The Gradle output is saved to orefishfarm-build-log.txt here, so Claude can read it if the build fails.

param(
    [string]$Instance = "C:\Users\Owner\AppData\Roaming\PrismLauncher\instances\Quicreate Skyblock RFA  0.9.0\minecraft"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$zip = Join-Path $PSScriptRoot 'orefishfarm-project.zip'
$dest = Join-Path (Split-Path $PSScriptRoot -Parent) 'JakesOreFishFarm'
$log = Join-Path $PSScriptRoot 'orefishfarm-build-log.txt'

if (Test-Path $zip) {
    Write-Host "1/4 Unpacking into $dest ..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -Path $zip -DestinationPath $dest -Force
} elseif (-not (Test-Path (Join-Path $dest 'build.gradle'))) {
    throw "orefishfarm-project.zip not found and $dest has no project"
}

if (-not ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe") -and ((Split-Path $env:JAVA_HOME -Leaf) -match '17'))) {
    $jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium", "C:\Program Files\Java", "C:\Program Files\Microsoft", "C:\Program Files\Zulu" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '17' -and (Test-Path "$($_.FullName)\bin\javac.exe") } |
        Select-Object -First 1
    if (-not $jdk) { throw "No Java 17 JDK found. Install one with:  winget install EclipseAdoptium.Temurin.17.JDK" }
    $env:JAVA_HOME = $jdk.FullName
}
Write-Host "Java: $env:JAVA_HOME"

Write-Host "2/4 Building (the first build downloads Minecraft and takes a few minutes)..." -ForegroundColor Cyan
Push-Location $dest
cmd /c "gradlew.bat build --console=plain > `"$log`" 2>&1"
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) {
    Write-Host ""
    Write-Host "BUILD FAILED. The errors:" -ForegroundColor Red
    Select-String -Path $log -Pattern 'error:|FAILURE|What went wrong' -Context 0,3 | Select-Object -First 15 | ForEach-Object { $_.ToString() }
    Write-Host "The full output is in orefishfarm-build-log.txt. Nothing was installed." -ForegroundColor Red
    exit 1
}

Write-Host "3/4 Finding the jar..." -ForegroundColor Cyan
$jar = Get-ChildItem (Join-Path $dest "build\libs\orefishfarm-*.jar") |
    Where-Object { $_.Name -notmatch 'sources|slim|dev' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $jar) { throw "No jar was built. Send orefishfarm-build-log.txt to Claude." }

Write-Host "4/4 Installing..." -ForegroundColor Cyan
$mods = Join-Path $Instance "mods"
Get-ChildItem $mods -Filter "orefishfarm-*.jar" | Remove-Item
Copy-Item $jar.FullName $mods
Write-Host "Installed $($jar.Name) into the pack." -ForegroundColor Green
if (Test-Path $zip) { Remove-Item -Force $zip }
Write-Host "Now run update-and-build.ps1 too if there is a quicreate-update.zip (it has the obsidian rod and lava fishing)." -ForegroundColor Green
