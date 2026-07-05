# ============================================================
# 服务器 Webhook 接收器
# 监听 GitHub webhook 事件，收到 push 后自动更新代码
# 配合 GitHub Webhook 使用
# ============================================================
param(
    [int]$Port = 9000
)

$SECRET = "morning-radio-webhook-secret-2026"
$LISTENER = [System.Net.HttpListener]::new()
$LISTENER.Prefixes.Add("http://+:$Port/")

try {
    $LISTENER.Start()
    Write-Host "Webhook 监听器已启动: http://0.0.0.0:$Port/" -ForegroundColor Cyan
    Write-Host "请在 GitHub 仓库 Settings > Webhooks 中添加:" -ForegroundColor Yellow
    Write-Host "  Payload URL: http://8.154.22.214:$Port/" -ForegroundColor Yellow
    Write-Host "  Content type: application/json" -ForegroundColor Yellow
    Write-Host "  Secret: $SECRET" -ForegroundColor Yellow
    Write-Host ""
    
    while ($LISTENER.IsListening) {
        $context = $LISTENER.GetContext()
        $request = $context.Request
        
        if ($request.HttpMethod -eq "POST" -and $request.Url.LocalPath -eq "/") {
            $reader = [System.IO.StreamReader]::new($request.InputStream)
            $body = $reader.ReadToEnd()
            $reader.Close()
            
            $signature = $request.Headers["X-Hub-Signature-256"]
            $event = $request.Headers["X-GitHub-Event"]
            
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "$timestamp - 收到事件: $event" -ForegroundColor Green
            
            if ($event -eq "push") {
                Write-Host "  执行自动更新..." -ForegroundColor Yellow
                
                # 异步执行更新（避免阻塞响应）
                $job = Start-Job -ScriptBlock {
                    param($Secret)
                    $logFile = "C:\morning-radio\logs\webhook_update.log"
                    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    Add-Content -Path $logFile -Value "$timestamp - Webhook triggered"
                    
                    $result = & "C:\morning-radio\scripts\update-server.ps1" 2>&1
                    Add-Content -Path $logFile -Value $result
                } -ArgumentList $SECRET
            }
            
            # 返回 200
            $response = $context.Response
            $response.StatusCode = 200
            $response.OutputStream.Close()
        }
    }
} finally {
    $LISTENER.Stop()
    $LISTENER.Close()
}
