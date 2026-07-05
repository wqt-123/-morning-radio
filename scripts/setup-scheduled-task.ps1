# ============================================================
# 早安电台每日自动播报定时任务配置（本地开发机）
# 使用 Windows 计划任务，每天凌晨 6:00 自动触发生成
# ============================================================
param(
    [string]$ProjectPath = "D:\Projects\morning-radio",
    [switch]$Remove
)

$TASK_NAME = "MorningRadio-Daily-Broadcast"
$SCRIPT_PATH = "$ProjectPath\scripts\daily-broadcast.ps1"

if ($Remove) {
    Write-Host "删除定时任务..." -ForegroundColor Yellow
    schtasks /delete /tn $TASK_NAME /f 2>&1
    Write-Host "已删除" -ForegroundColor Green
    exit 0
}

# 创建每日播报脚本
@"
# ============================================================
# 每日自动播报脚本
# ============================================================
`$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
`$logFile = "$ProjectPath\backend\logs\daily_broadcast.log"

function Write-Log(`$msg) {
    `$line = "`$timestamp - `$msg"
    Add-Content -Path `$logFile -Value `$line
    Write-Host `$line
}

Write-Log "===== 每日播报开始 ====="

try {
    # 1. 抓取最新新闻
    Write-Log "[1/3] 抓取新闻..."
    `$r = Invoke-RestMethod -Method POST "http://localhost:8000/api/news/fetch" -TimeoutSec 120
    Write-Log "  结果: code=`$(`$r.code), message=`$(`$r.message)"
    
    # 2. 触发生成播报
    Write-Log "[2/3] 生成播报..."
    `$r = Invoke-RestMethod -Method POST "http://localhost:8000/api/radio/generate" -TimeoutSec 1800
    Write-Log "  结果: code=`$(`$r.code), status=`$(`$r.data.status), duration=`$(`$r.data.duration)s"
    
    # 3. 验证结果
    Write-Log "[3/3] 验证结果..."
    `$r = Invoke-RestMethod "http://localhost:8000/api/radio/today" -TimeoutSec 10
    
    # 交叉验证
    `$data = `$r.data
    `$hasAudio = [bool]`$data.audio_url
    `$hasVideo = [bool]`$data.video_url
    `$hasScript = `$data.broadcast_text.Length -gt 100
    
    # 查询数据库中的新闻数
    `$newsResp = Invoke-RestMethod "http://localhost:8000/api/news/today?limit=5" -TimeoutSec 10
    `$newsCount = `$newsResp.data.total
    
    Write-Log "  验证: 音频=`$hasAudio, 视频=`$hasVideo, 稿件=`$hasScript, 新闻数=`$newsCount"
    
    if (`$hasAudio -and `$hasVideo -and `$hasScript -and `$newsCount -gt 0) {
        Write-Log "  [PASS] 全部验证通过"
    } else {
        Write-Log "  [WARN] 部分验证未通过，请检查"
    }
    
    Write-Log "===== 每日播报完成 ====="
    
} catch {
    Write-Log "  [ERROR] 失败: `$_"
    Write-Log "===== 每日播报异常终止 ====="
}
"@ | Set-Content -Path $SCRIPT_PATH -Encoding UTF8

Write-Host "创建定时任务..." -ForegroundColor Yellow

# 删除旧任务
schtasks /delete /tn $TASK_NAME /f 2>$null

# 创建每天 6:00 执行的任务
$action = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SCRIPT_PATH`""
schtasks /create /tn $TASK_NAME /tr $action /sc daily /st 06:00 /ru SYSTEM /f 2>&1

Write-Host "定时任务已创建: 每天 06:00 自动生成播报" -ForegroundColor Green
Write-Host ""
Write-Host "管理命令:" -ForegroundColor Cyan
Write-Host "  查看任务:  schtasks /query /tn $TASK_NAME" -ForegroundColor White
Write-Host "  手动运行:  schtasks /run /tn $TASK_NAME" -ForegroundColor White
Write-Host "  删除任务:  .\scripts\setup-scheduled-task.ps1 -Remove" -ForegroundColor White
Write-Host "  查看日志:  $ProjectPath\backend\logs\daily_broadcast.log" -ForegroundColor White
