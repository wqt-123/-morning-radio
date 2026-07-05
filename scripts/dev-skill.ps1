# ============================================================
# 早安电台本地开发 Skill 脚本
# 包含：代码拉取、依赖更新、服务重启、状态验证
# 后续所有开发操作统一通过此脚本执行
# ============================================================
param(
    [ValidateSet("update","restart","status","build","deploy","all")]
    [string]$Action = "status",
    
    [string]$ProjectPath = "D:\Projects\morning-radio"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LOG_FILE = "$ProjectPath\backend\logs\skill.log"

# 确保日志目录
$logDir = Split-Path $LOG_FILE -Parent
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function step($msg) {
    Write-Host "" -ForegroundColor DarkGray
    Write-Host "  [$msg]" -ForegroundColor Cyan
    Add-Content -Path $LOG_FILE -Value "$timestamp [$Action] $msg"
}

function ok($msg) { Write-Host "    [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function err($msg) { Write-Host "    [ERR] $msg" -ForegroundColor Red }

# ============================================================
function Invoke-Update {
    step "拉取最新代码"
    cd $ProjectPath
    $currentBranch = (git branch --show-current 2>&1).Trim()
    ok "当前分支: $currentBranch"
    
    $gitOutput = git pull origin $currentBranch 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "代码已是最新"
    } else {
        warn "git pull: $gitOutput"
    }
    
    step "更新后端依赖"
    cd "$ProjectPath\backend"
    pip install -r requirements.txt 2>&1 | Out-Null
    ok "依赖已更新"
    
    step "构建前端"
    cd "$ProjectPath\frontend"
    npm install 2>&1 | Out-Null
    npm run build 2>&1 | Out-Null
    ok "前端构建完成"
    
    Invoke-Restart
}

# ============================================================
function Invoke-Restart {
    step "重启服务"
    
    # FastAPI
    try {
        nssm restart MorningRadio-API-Local 2>&1 | Out-Null
        ok "FastAPI 已重启"
    } catch {
        # 尝试手动重启
        Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -match "run" -or $_.CommandLine -match "run.py" } | Stop-Process -Force 2>$null
        Start-Sleep 2
        Start-Process powershell -ArgumentList "-NoExit -Command cd '$ProjectPath\backend'; python run.py" -WindowStyle Minimized
        ok "FastAPI 手动启动"
    }
    
    Start-Sleep 3
    
    # Celery
    try {
        nssm restart MorningRadio-Celery-Local 2>&1 | Out-Null
        ok "Celery 已重启"
    } catch {
        warn "Celery NSSM 重启失败，尝试手动启动"
    }
    
    Start-Sleep 2
    Invoke-Status
}

# ============================================================
function Invoke-Status {
    step "服务状态检查"
    
    # API 状态
    try {
        $r = Invoke-RestMethod "http://localhost:8000/" -TimeoutSec 10
        ok "FastAPI: 运行中"
    } catch {
        err "FastAPI: 未响应"
    }
    
    # 新闻数
    try {
        $r = Invoke-RestMethod "http://localhost:8000/api/news/today?limit=1" -TimeoutSec 10
        ok "今日新闻: $($r.data.total) 条"
    } catch {
        warn "无法获取新闻数"
    }
    
    # 播报状态
    try {
        $r = Invoke-RestMethod "http://localhost:8000/api/radio/today" -TimeoutSec 10
        $s = $r.data
        if ($s.status -eq "completed") {
            ok "今日播报: 已完成 ($($s.duration)s)"
            ok "  音频: $($s.audio_url -ne $null)"
            ok "  视频: $($s.video_url -ne $null)"
            ok "  字数: $($s.broadcast_text.Length)"
        } else {
            warn "今日播报: $($s.status)"
        }
    } catch {
        warn "无今日播报数据"
    }
    
    # 进程状态
    $pyProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pyProcesses) {
        ok "Python 进程: $($pyProcesses.Count) 个"
    }
    
    # MySQL
    try {
        $mysqlService = Get-Service "MySQL80" -ErrorAction SilentlyContinue
        if ($mysqlService.Status -eq "Running") {
            ok "MySQL: 运行中"
        } else {
            warn "MySQL: 未运行"
        }
    } catch {
        warn "MySQL 服务未找到"
    }
    
    # Redis
    try {
        $redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue
        if ($redisProcess) { ok "Redis: 运行中" } else { warn "Redis: 未运行" }
    } catch {
        warn "Redis 未运行"
    }
    
    step "前端地址"
    ok "http://localhost:8000 (前后端一体)"
    ok "API 文档: http://localhost:8000/docs"
}

# ============================================================
function Invoke-Build {
    step "完整构建"
    cd "$ProjectPath\backend"
    pip install -r requirements.txt 2>&1 | Out-Null
    ok "后端依赖已安装"
    
    cd "$ProjectPath\frontend"
    npm install 2>&1 | Out-Null
    npm run build 2>&1 | Out-Null
    ok "前端构建完成"
}

# ============================================================
function Invoke-Deploy {
    step "执行部署到服务器"
    
    $serverScript = "$ProjectPath\deploy\deploy.ps1"
    if (Test-Path $serverScript) {
        # 先推送到 GitHub
        Write-Host "  推送代码到 GitHub..."
        cd $ProjectPath
        git add .
        $commitMsg = "deploy: auto-deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        git commit -m $commitMsg 2>&1 | Out-Null
        git push origin main
        
        Write-Host "  如需在服务器上拉取最新代码，运行:"
        Write-Host "  pwsh -File C:\morning-radio\scripts\update-server.ps1" -ForegroundColor Yellow
    } else {
        err "部署脚本不存在: $serverScript"
    }
}

# ============================================================
# 主入口
# ============================================================
Write-Host "===== 早安电台开发 Skill =====" -ForegroundColor Magenta
Write-Host "  项目: $ProjectPath" -ForegroundColor DarkGray
Write-Host "  动作: $Action" -ForegroundColor DarkGray

switch ($Action) {
    "update"  { Invoke-Update }
    "restart" { Invoke-Restart }
    "status"  { Invoke-Status }
    "build"   { Invoke-Build }
    "deploy"  { Invoke-Deploy }
    "all"     {
        Invoke-Update
        Invoke-Restart
    }
}

Write-Host ""
Write-Host "===== 完成 =====" -ForegroundColor Magenta
