# ============================================================
# 服务器代码自动更新脚本
# 用法: 本地 git push 后，在服务器上运行此脚本即可拉取最新代码并重启服务
# 也可配置为 webhook 接收后自动执行
# ============================================================
param(
    [string]$ProjectPath = "C:\morning-radio",
    [string]$LogPath = "C:\morning-radio\logs\update.log",
    [string]$Branch = "main"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logDir = Split-Path $LogPath -Parent

# 确保日志目录存在
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log($Message) {
    $line = "$timestamp - $Message"
    Write-Host $line
    Add-Content -Path $LogPath -Value $line
}

Write-Log "===== 开始更新 ====="

try {
    # 1. 拉取最新代码
    Write-Log "[1/5] 拉取最新代码 (分支: $Branch)..."
    cd $ProjectPath
    $gitOutput = git fetch origin $Branch 2>&1
    Write-Log "  git fetch: $gitOutput"
    
    $gitOutput = git reset --hard origin/$Branch 2>&1
    Write-Log "  git reset: $gitOutput"
    
    # 2. 更新后端依赖
    Write-Log "[2/5] 更新后端依赖..."
    cd "$ProjectPath\backend"
    $pipOutput = pip install -r requirements.txt 2>&1
    Write-Log "  pip install: OK"
    
    # 3. 更新前端
    Write-Log "[3/5] 构建前端..."
    cd "$ProjectPath\frontend"
    npm install 2>&1 | Out-Null
    $buildOutput = npm run build 2>&1
    Write-Log "  npm build: OK"
    
    # 4. 重启服务
    Write-Log "[4/5] 重启服务..."
    
    # 重启 FastAPI
    nssm restart MorningRadio-API 2>&1
    Write-Log "  MorningRadio-API: 已重启"
    Start-Sleep 2
    
    # 重启 Celery
    nssm restart MorningRadio-Celery 2>&1
    Write-Log "  MorningRadio-Celery: 已重启"
    Start-Sleep 1
    
    # 重载 Nginx
    cd C:\nginx
    .\nginx.exe -s reload 2>&1
    Write-Log "  Nginx: 已重载"
    
    # 5. 验证
    Write-Log "[5/5] 验证服务状态..."
    Start-Sleep 3
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/news/today?limit=1" -TimeoutSec 10 -UseBasicParsing
        Write-Log "  API 响应: $($response.StatusCode) - 服务正常"
    } catch {
        Write-Log "  [WARN] API 验证失败: $_"
    }
    
    Write-Log "===== 更新完成 ====="
    
} catch {
    Write-Log "  [ERROR] 更新失败: $_"
    Write-Log "===== 更新异常终止 ====="
    exit 1
}
