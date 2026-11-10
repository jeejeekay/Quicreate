# Builds Quicreate and installs the jar into the pack.
#
#   .\build-and-install.ps1
#   .\build-and-install.ps1 -Instance "C:\...\instances\My Test Copy\minecraft"
#
# 1. Finds a Java 17 JDK (Forge 1.20.1 needs it), only for this window.
# 2. Runs the Gradle build.
# 3. Removes any old quicreate-*.jar from the instance's mods folder and copies the new one in.

param(
    [string]$Instance = "C:\Users\Owner\AppData\Roaming\PrismLauncher\instances\Quicreate Skyblock RFA  0.9.0\minecraft"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# --- 1. Java 17 ---------------------------------------------------------------
if (-not ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe") -and ((Split-Path $env:JAVA_HOME -Leaf) -match '17'))) {
    $jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium", "C:\Program Files\Java", "C:\Program Files\Microsoft", "C:\Program Files\Zulu" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '17' -and (Test-Path "$($_.FullName)\bin\javac.exe") } |
        Select-Object -First 1
    if (-not $jdk) {
        throw "No Java 17 JDK found. Install one with:  winget install EclipseAdoptium.Temurin.17.JDK"
    }
    $env:JAVA_HOME = $jdk.FullName
}
Write-Host "Java: $env:JAVA_HOME" -ForegroundColor Cyan

# --- 2. Build -----------------------------------------------------------------
& .\gradlew.bat build
if ($LASTEXITCODE -ne 0) {
    throw "Build failed. Scroll up to the first error (lines starting with 'error:')."
}

# --- 3. Install ---------------------------------------------------------------
$jar = Get-ChildItem "build\libs\quicreate-*.jar" |
    Where-Object { $_.Name -notmatch 'sources|slim|dev' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$mods = Join-Path $Instance "mods"
if (-not (Test-Path $mods)) {
    throw "Mods folder not found: $mods"
}
Get-ChildItem $mods -Filter "quicreate-*.jar" | Remove-Item
Copy-Item $jar.FullName $mods
Write-Host "Installed $($jar.Name) into $mods" -ForegroundColor Green
