# Applies quicreate-update.zip (the latest changes from Claude), builds the mod and installs it into the pack.
# Run from the repo folder:  powershell -ExecutionPolicy Bypass -File .\update-and-build.ps1
# The Gradle output is saved to build-log.txt (Claude can read it if the build fails).

param(
    [string]$Instance = "C:\Users\Owner\AppData\Roaming\PrismLauncher\instances\Quicreate Skyblock RFA  0.9.0\minecraft"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$zip = Join-Path $PSScriptRoot 'quicreate-update.zip'
if (-not (Test-Path $zip)) { throw "quicreate-update.zip not found next to this script" }
$r = Join-Path $PSScriptRoot 'src\main\resources'

# --- 1. Apply the changes --------------------------------------------------------
Write-Host "1/4 Applying the changes..." -ForegroundColor Cyan
# Files or folders the update removes are listed in _delete.txt inside the zip (paths from the repo folder).
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zf = [System.IO.Compression.ZipFile]::OpenRead($zip)
$del = $zf.Entries | Where-Object { $_.FullName -eq '_delete.txt' } | Select-Object -First 1
if ($del) {
    $reader = New-Object System.IO.StreamReader($del.Open())
    $lines = $reader.ReadToEnd() -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
    $reader.Close()
    foreach ($l in $lines) {
        $p = Join-Path $PSScriptRoot ($l.Trim() -replace '/', '\')
        if (Test-Path $p) { Remove-Item -Recurse -Force $p }
    }
}
$zf.Dispose()
Expand-Archive -Path $zip -DestinationPath $PSScriptRoot -Force
$d = Join-Path $PSScriptRoot '_delete.txt'
if (Test-Path $d) { Remove-Item -Force $d }

# --- 2. Java 17 --------------------------------------------------------------------
if (-not ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe") -and ((Split-Path $env:JAVA_HOME -Leaf) -match '17'))) {
    $jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium", "C:\Program Files\Java", "C:\Program Files\Microsoft", "C:\Program Files\Zulu" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '17' -and (Test-Path "$($_.FullName)\bin\javac.exe") } |
        Select-Object -First 1
    if (-not $jdk) { throw "No Java 17 JDK found. Install one with:  winget install EclipseAdoptium.Temurin.17.JDK" }
    $env:JAVA_HOME = $jdk.FullName
}
Write-Host "Java: $env:JAVA_HOME"

# --- 3. Build (output saved to build-log.txt) --------------------------------------
Write-Host "2/4 Building (this takes a minute)..." -ForegroundColor Cyan
$log = Join-Path $PSScriptRoot 'build-log.txt'
cmd /c "gradlew.bat build --console=plain > `"$log`" 2>&1"
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ""
    Write-Host "BUILD FAILED. The errors:" -ForegroundColor Red
    Select-String -Path $log -Pattern 'error:|FAILURE|What went wrong' -Context 0,3 | Select-Object -First 15 | ForEach-Object { $_.ToString() }
    Write-Host ""
    Write-Host "The full output is in build-log.txt. Nothing was installed; the pack still has the old jar." -ForegroundColor Red
    exit 1
}

# --- 4. Check the jar has the new content, then install ------------------------------
Write-Host "3/4 Checking the jar..." -ForegroundColor Cyan
$jar = Get-ChildItem "build\libs\quicreate-*.jar" |
    Where-Object { $_.Name -notmatch 'sources|slim|dev' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$z = [System.IO.Compression.ZipFile]::OpenRead($jar.FullName)
$names = $z.Entries | ForEach-Object { $_.FullName }
$z.Dispose()
$expect = @('IGoByJake/quicreate/worldgen/WedgeFeature.class',
            'data/quicreate/worldgen/structure/mars_quake_wedges.json',
            'data/ad_astra/tags/worldgen/biome/has_acid_rain.json',
            'data/mowziesmobs/structures/umvuthana/umvuthi_throne.nbt')
$missing = $expect | Where-Object { $names -notcontains $_ }
if ($missing) { throw "The built jar is missing: $($missing -join ', '). Send build-log.txt to Claude." }

Write-Host "4/4 Installing..." -ForegroundColor Cyan
$mods = Join-Path $Instance "mods"
if (-not (Test-Path $mods)) { throw "Mods folder not found: $mods" }
Get-ChildItem $mods -Filter "quicreate-*.jar" | Remove-Item
Copy-Item $jar.FullName $mods
Write-Host "Installed $($jar.Name) ($([math]::Round($jar.Length / 1MB, 1)) MB) into the pack." -ForegroundColor Green

# The update is in the source folder now; the zip isn't needed any more.
Remove-Item -Force $zip
foreach ($f in @('quicreate-all-updates-2026-11-12.zip')) { $p = Join-Path $PSScriptRoot $f; if (Test-Path $p) { Remove-Item -Force $p } }
Write-Host ""
Write-Host "Done. New worldgen only shows in chunks that haven't been generated yet: use a new world or fly to unexplored land." -ForegroundColor Green
Write-Host "To find a wedge on Mars:  /locate structure quicreate:mars_quake_wedges"
