# Saves every change in this folder to GitHub in one go: stage, commit, push.
# Run it from the repo folder:  .\save-to-github.ps1 "what changed"
# (or with no message and it will ask for one).
param([string]$Message = "")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# An unfinished commit (editor closed, terminal killed) leaves this lock behind and blocks git.
# Only remove it when no git is running.
if ((Test-Path ".git\index.lock") -and -not (Get-Process git -ErrorAction SilentlyContinue)) {
    Remove-Item ".git\index.lock" -Force
    Write-Host "Removed a stale .git\index.lock from an unfinished commit." -ForegroundColor Yellow
}
Remove-Item ".git\.COMMIT_EDITMSG.swp" -Force -ErrorAction SilentlyContinue

Write-Host "1/4 Getting anything new from GitHub..." -ForegroundColor Cyan
git pull --ff-only
if ($LASTEXITCODE -ne 0) { Write-Host "GitHub has commits this folder doesn't, and they clash. Stop here and ask." -ForegroundColor Red; exit 1 }

Write-Host "2/4 Staging every change (new, edited and deleted files)..." -ForegroundColor Cyan
git add -A
git status --short
if (-not (git status --porcelain)) { Write-Host "Nothing to save." -ForegroundColor Green; exit 0 }

if (-not $Message) { $Message = Read-Host "One line describing what changed" }
if (-not $Message) { $Message = "Update " + (Get-Date -Format "yyyy-MM-dd HH:mm") }

Write-Host "3/4 Committing..." -ForegroundColor Cyan
git commit -m $Message          # -m means no text editor opens
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "4/4 Pushing to GitHub..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Saved and pushed." -ForegroundColor Green
git log --oneline -3
