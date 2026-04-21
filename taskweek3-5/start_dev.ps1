# TLU Smart Tutor - Khoi dong Ha tang (Theo Phuong Phase 1)
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $currentDir

Write-Host ">>> Dang khoi dong Ha tang Docker (Qdrant + RabbitMQ)..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Ha tang da san sang!" -ForegroundColor Green
    Write-Host "-------------------------------------------------------"
    Write-Host "Hay mo Terminal va tu tay nhap cac lenh sau (Giong Phuong):" -ForegroundColor Yellow
    Write-Host "1. SEARCH SERVICE: " -NoNewline; Write-Host "python search-service/main.py" -ForegroundColor Gray
    Write-Host "2. FRONTEND      : " -NoNewline; Write-Host "cd frontend; npm run dev" -ForegroundColor Gray
    Write-Host "-------------------------------------------------------"
}
