$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Stop-LocalPort {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($processId in $processIds) {
        if ($processId -and $processId -ne 0) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
}

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}

Stop-LocalPort -Port 5500
Stop-LocalPort -Port 8000
Start-Sleep -Milliseconds 500

Start-Process `
    -FilePath $Python `
    -ArgumentList "review_api.py" `
    -WorkingDirectory $BackendDir `
    -WindowStyle Hidden

Start-Process `
    -FilePath $Python `
    -ArgumentList "-m http.server 5500 --bind 127.0.0.1 --directory `"$FrontendDir`"" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden

Start-Sleep -Seconds 2

$frontendStatus = (Invoke-WebRequest -Uri "http://127.0.0.1:5500/index.html" -UseBasicParsing).StatusCode
$reviewStatus = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing).StatusCode

Write-Host ""
Write-Host "Local services started."
Write-Host "Frontend status: $frontendStatus"
Write-Host "Review API status: $reviewStatus"
Write-Host ""
Write-Host "Main page:   http://127.0.0.1:5500/index.html"
Write-Host "Review page: http://127.0.0.1:5500/review.html"
