# ============================================================
# 早安电台 NSSM 服务注册脚本（本地开发机）
# ============================================================
param(
    [string]$ProjectPath = "D:\Projects\morning-radio",
    [switch]$Uninstall
)

$NSSM_URL = "https://nssm.cc/release/nssm-2.24.zip"
$NSSM_DIR = "C:\nssm"
$NSSM_EXE = "$NSSM_DIR\nssm.exe"

# 下载 NSSM
if (!(Test-Path $NSSM_EXE)) {
    Write-Host "[0] 下载 NSSM..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $NSSM_DIR -Force | Out-Null
    $zip = "$env:TEMP\nssm.zip"
    try {
        Invoke-WebRequest -Uri $NSSM_URL -OutFile $zip -TimeoutSec 30
        Expand-Archive -Path $zip -DestinationPath "$env:TEMP\nssm_extract" -Force
        Copy-Item "$env:TEMP\nssm_extract\nssm-2.24\win64\nssm.exe" $NSSM_EXE -Force
        Write-Host "  NSSM 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] 下载失败: $_. 请手动下载 nssm.exe 放到 C:\nssm\" -ForegroundColor Red
        exit 1
    }
}

$env:Path = "$NSSM_DIR;$env:Path"

$API_SERVICE = "MorningRadio-API-Local"
$CELERY_SERVICE = "MorningRadio-Celery-Local"

if ($Uninstall) {
    Write-Host "卸载服务..." -ForegroundColor Yellow
    nssm stop $API_SERVICE 2>$null
    nssm remove $API_SERVICE confirm 2>$null
    nssm stop $CELERY_SERVICE 2>$null
    nssm remove $CELERY_SERVICE confirm 2>$null
    Write-Host "已卸载所有服务" -ForegroundColor Green
    exit 0
}

# 创建日志目录
$logDir = "$ProjectPath\backend\logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "[1] 注册 FastAPI 服务..." -ForegroundColor Yellow

# 停止旧服务
nssm stop $API_SERVICE 2>$null
nssm remove $API_SERVICE confirm 2>$null

# 安装
nssm install $API_SERVICE "python" "run.py"
nssm set $API_SERVICE AppDirectory "$ProjectPath\backend"
nssm set $API_SERVICE DisplayName "MorningRadio API (Local)"
nssm set $API_SERVICE Description "早安电台 - FastAPI 后端服务（本地开发机）"
nssm set $API_SERVICE Start SERVICE_AUTO_START
nssm set $API_SERVICE AppStdout "$logDir\api_out.log"
nssm set $API_SERVICE AppStderr "$logDir\api_err.log"
nssm set $API_SERVICE AppRestartDelay 5000
nssm set $API_SERVICE AppThrottle 15000

nssm start $API_SERVICE
Write-Host "  $API_SERVICE 已注册并启动" -ForegroundColor Green

Write-Host "[2] 注册 Celery Worker 服务..." -ForegroundColor Yellow

nssm stop $CELERY_SERVICE 2>$null
nssm remove $CELERY_SERVICE confirm 2>$null

nssm install $CELERY_SERVICE "celery" "-A app.tasks.celery_app worker --pool=solo --loglevel=info"
nssm set $CELERY_SERVICE AppDirectory "$ProjectPath\backend"
nssm set $CELERY_SERVICE DisplayName "MorningRadio Celery (Local)"
nssm set $CELERY_SERVICE Description "早安电台 - Celery Worker（本地开发机）"
nssm set $CELERY_SERVICE Start SERVICE_AUTO_START
nssm set $CELERY_SERVICE AppStdout "$logDir\celery_out.log"
nssm set $CELERY_SERVICE AppStderr "$logDir\celery_err.log"
nssm set $CELERY_SERVICE AppRestartDelay 5000

nssm start $CELERY_SERVICE
Write-Host "  $CELERY_SERVICE 已注册并启动" -ForegroundColor Green

Write-Host ""
Write-Host "===== 服务注册完成 =====" -ForegroundColor Cyan
Write-Host "  FastAPI:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API文档:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "管理命令:" -ForegroundColor Cyan
Write-Host "  查看状态:  nssm status $API_SERVICE" -ForegroundColor White
Write-Host "  重启:      nssm restart $API_SERVICE" -ForegroundColor White
Write-Host "  停止:      nssm stop $API_SERVICE" -ForegroundColor White
Write-Host "  卸载:      .\scripts\nssm-register.ps1 -Uninstall" -ForegroundColor White
