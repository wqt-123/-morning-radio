# ============================================================
# 早安电台 - 云服务器一键部署脚本
# 目标: 阿里云 ECS Windows Server 2022 (8.154.22.214)
# ============================================================
param(
    [string]$ServerIP = "8.154.22.214",
    [string]$ServerUser = "Administrator",
    [string]$ServerPass = "Wqt158205",
    [string]$ProjectPath = "C:\morning-radio",
    [switch]$SkipFirewall,
    [switch]$SkipNginx,
    [switch]$SkipServices
)

$ErrorActionPreference = "Stop"
Write-Host "===== 早安电台云服务器部署 =====" -ForegroundColor Cyan
Write-Host "目标服务器: $ServerIP" -ForegroundColor Cyan

# ============================================================
# Step 1: 建立远程会话
# ============================================================
Write-Host "[1/8] 建立远程连接..." -ForegroundColor Yellow
$secPass = ConvertTo-SecureString $ServerPass -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($ServerUser, $secPass)

try {
    $session = New-PSSession -ComputerName $ServerIP -Credential $cred -ErrorAction Stop
    Write-Host "  [OK] 远程连接成功" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] 远程连接失败: $_" -ForegroundColor Red
    Write-Host "  尝试使用 WinRM 快速配置..." -ForegroundColor Yellow
    # 尝试自动启用 WinRM
    try {
        $enableWinRM = {
            winrm quickconfig -q -force 2>$null
            winrm set winrm/config/service '@{AllowUnencrypted="true"}' 2>$null
            winrm set winrm/config/service/auth '@{Basic="true"}' 2>$null
            netsh advfirewall firewall add rule name="WinRM" dir=in protocol=TCP localport=5985 action=allow 2>$null
        }
        # 无法远程启用，需要用户手动
        Write-Host "  [提示] 请在服务器上以管理员运行: winrm quickconfig -q -force" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# Step 2: 环境检查与依赖安装
# ============================================================
Write-Host "[2/8] 检查服务器环境..." -ForegroundColor Yellow

$checkEnv = {
    $results = @{}
    
    # Python
    try { $pyVer = (python --version 2>&1).ToString(); $results.Python = $pyVer } catch { $results.Python = "NOT_FOUND" }
    
    # Git
    try { $gitVer = (git --version 2>&1).ToString(); $results.Git = $gitVer } catch { $results.Git = "NOT_FOUND" }
    
    # Node.js
    try { $nodeVer = (node --version 2>&1).ToString(); $results.Node = $nodeVer } catch { $results.Node = "NOT_FOUND" }
    
    # Nginx
    $nginxPath = "C:\nginx"
    if (Test-Path $nginxPath) { $results.Nginx = "INSTALLED" } else { $results.Nginx = "NOT_FOUND" }
    
    # Redis
    try { 
        $redisService = Get-Service "Redis" -ErrorAction SilentlyContinue
        if ($redisService.Status -eq "Running") { $results.Redis = "RUNNING" } else { $results.Redis = "STOPPED" }
    } catch { $results.Redis = "NOT_FOUND" }
    
    # MySQL
    try {
        $mysqlService = Get-Service "MySQL*" -ErrorAction SilentlyContinue
        $results.MySQL = if ($mysqlService) { $mysqlService.Name } else { "NOT_FOUND" }
    } catch { $results.MySQL = "NOT_FOUND" }
    
    $results | ConvertTo-Json
}

$envResult = Invoke-Command -Session $session -ScriptBlock $checkEnv
Write-Host "  服务器环境: $envResult"

$envObj = $envResult | ConvertFrom-Json

# 安装缺失依赖
if ($envObj.Python -eq "NOT_FOUND") {
    Write-Host "  [安装] Python 3.11..." -ForegroundColor Yellow
    Invoke-Command -Session $session -ScriptBlock {
        $pythonInstaller = "C:\Temp\python-3.11.8-amd64.exe"
        if (!(Test-Path C:\Temp)) { New-Item -ItemType Directory -Path C:\Temp -Force | Out-Null }
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe" -OutFile $pythonInstaller
        Start-Process $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Write-Host "Python 安装完成"
    }
}

if ($envObj.Git -eq "NOT_FOUND") {
    Write-Host "  [安装] Git..." -ForegroundColor Yellow
    Invoke-Command -Session $session -ScriptBlock {
        $gitInstaller = "C:\Temp\Git-2.44.0-64-bit.exe"
        Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe" -OutFile $gitInstaller
        Start-Process $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    }
}

# ============================================================
# Step 3: 安装 Nginx
# ============================================================
if (-not $SkipNginx -and $envObj.Nginx -eq "NOT_FOUND") {
    Write-Host "[3/8] 安装 Nginx..." -ForegroundColor Yellow
    Invoke-Command -Session $session -ScriptBlock {
        $nginxZip = "C:\Temp\nginx.zip"
        Invoke-WebRequest -Uri "https://nginx.org/download/nginx-1.24.0.zip" -OutFile $nginxZip
        Expand-Archive -Path $nginxZip -DestinationPath "C:\" -Force
        Rename-Item "C:\nginx-1.24.0" "C:\nginx" -Force -ErrorAction SilentlyContinue
        Write-Host "Nginx 安装完成: C:\nginx"
    }
}

# ============================================================
# Step 4: 配置阿里云防火墙
# ============================================================
if (-not $SkipFirewall) {
    Write-Host "[4/8] 配置 Windows 防火墙..." -ForegroundColor Yellow
    Invoke-Command -Session $session -ScriptBlock {
        $ports = @(80, 443, 8000, 3306, 6379, 5985, 5986)
        foreach ($port in $ports) {
            $ruleName = "MorningRadio_Port_$port"
            $existing = netsh advfirewall firewall show rule name="$ruleName" 2>$null
            if ($existing -match "找不到") {
                netsh advfirewall firewall add rule name="$ruleName" dir=in protocol=TCP localport=$port action=allow 2>&1 | Out-Null
                Write-Host "  防火墙规则已添加: 端口 $port"
            } else {
                Write-Host "  防火墙规则已存在: 端口 $port"
            }
        }
    }
    Write-Host "  [提示] 还需要在阿里云控制台安全组中放行端口: 80, 443, 8000" -ForegroundColor Cyan
}

# ============================================================
# Step 5: 克隆项目
# ============================================================
Write-Host "[5/8] 部署项目代码..." -ForegroundColor Yellow
Invoke-Command -Session $session -ScriptBlock {
    param($ProjectPath)
    
    if (Test-Path $ProjectPath) {
        Remove-Item -Recurse -Force $ProjectPath
    }
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
    
    cd $ProjectPath
    git clone https://github.com/WQT-123/morning-radio.git .
} -ArgumentList $ProjectPath

# ============================================================
# Step 6: 安装项目依赖
# ============================================================
Write-Host "[6/8] 安装项目依赖..." -ForegroundColor Yellow
Invoke-Command -Session $session -ScriptBlock {
    param($ProjectPath)
    
    # Python 依赖
    cd "$ProjectPath\backend"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    # 前端构建
    cd "$ProjectPath\frontend"
    npm install
    npm run build
} -ArgumentList $ProjectPath

# ============================================================
# Step 7: 配置 Nginx
# ============================================================
Write-Host "[7/8] 配置 Nginx..." -ForegroundColor Yellow
$nginxConfig = @'
worker_processes 1;
events { worker_connections 1024; }
http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    server {
        listen 80;
        server_name 8.154.22.214;
        
        # 前端静态文件
        location / {
            root C:/morning-radio/frontend/dist;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
        
        # API 反向代理
        location /api {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        
        # 媒体文件
        location /media {
            proxy_pass http://127.0.0.1:8000/media;
            proxy_set_header Host $host;
            add_header Cache-Control "public, max-age=3600";
        }
    }
}
'@

Invoke-Command -Session $session -ScriptBlock {
    param($nginxConfig)
    $configPath = "C:\nginx\conf\nginx.conf"
    $backup = "C:\nginx\conf\nginx.conf.bak"
    if (Test-Path $configPath) {
        Copy-Item $configPath $backup -Force
    }
    Set-Content -Path $configPath -Value $nginxConfig -Encoding UTF8
    
    # 重启 Nginx
    cd C:\nginx
    .\nginx.exe -s stop 2>$null
    Start-Sleep 1
    .\nginx.exe
    Write-Host "Nginx 已重启"
} -ArgumentList $nginxConfig

# ============================================================
# Step 8: NSSM 注册 Windows 服务
# ============================================================
Write-Host "[8/8] 注册 Windows 服务 (NSSM)..." -ForegroundColor Yellow
Invoke-Command -Session $session -ScriptBlock {
    param($ProjectPath)
    
    # 下载 NSSM
    $nssmPath = "C:\nssm\nssm.exe"
    if (!(Test-Path $nssmPath)) {
        New-Item -ItemType Directory -Path "C:\nssm" -Force | Out-Null
        $nssmZip = "C:\Temp\nssm.zip"
        Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath "C:\Temp\nssm_extract" -Force
        Copy-Item "C:\Temp\nssm_extract\nssm-2.24\win64\nssm.exe" $nssmPath -Force
    }
    
    $env:Path = "C:\nssm;$env:Path"
    
    # FastAPI 服务
    $serviceName1 = "MorningRadio-API"
    nssm stop $serviceName1 2>$null
    nssm remove $serviceName1 confirm 2>$null
    nssm install $serviceName1 "python" "$ProjectPath\backend\run.py"
    nssm set $serviceName1 AppDirectory "$ProjectPath\backend"
    nssm set $serviceName1 DisplayName "MorningRadio API Service"
    nssm set $serviceName1 Description "早安电台 - FastAPI 后端服务"
    nssm set $serviceName1 Start SERVICE_AUTO_START
    nssm set $serviceName1 AppStdout "$ProjectPath\backend\logs\api_out.log"
    nssm set $serviceName1 AppStderr "$ProjectPath\backend\logs\api_err.log"
    nssm start $serviceName1
    Write-Host "  服务 $serviceName1 已注册并启动"
    
    # Celery Worker 服务
    $serviceName2 = "MorningRadio-Celery"
    nssm stop $serviceName2 2>$null
    nssm remove $serviceName2 confirm 2>$null
    nssm install $serviceName2 "celery" "-A app.tasks.celery_app worker --pool=solo --loglevel=info"
    nssm set $serviceName2 AppDirectory "$ProjectPath\backend"
    nssm set $serviceName2 DisplayName "MorningRadio Celery Worker"
    nssm set $serviceName2 Description "早安电台 - Celery 异步任务 Worker"
    nssm set $serviceName2 Start SERVICE_AUTO_START
    nssm set $serviceName2 AppStdout "$ProjectPath\backend\logs\celery_out.log"
    nssm set $serviceName2 AppStderr "$ProjectPath\backend\logs\celery_err.log"
    nssm start $serviceName2
    Write-Host "  服务 $serviceName2 已注册并启动"
    
} -ArgumentList $ProjectPath

# ============================================================
# 清理
# ============================================================
Remove-PSSession $session
Write-Host "===== 部署完成 =====" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址: http://8.154.22.214" -ForegroundColor Cyan
Write-Host "API 文档: http://8.154.22.214/api/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "[重要提醒] 请在阿里云控制台安全组中放行以下端口:" -ForegroundColor Yellow
Write-Host "  - 80 (HTTP)" -ForegroundColor Yellow
Write-Host "  - 443 (HTTPS)" -ForegroundColor Yellow
Write-Host "  - 8000 (API)" -ForegroundColor Yellow
Write-Host "  - 3306 (MySQL)" -ForegroundColor Yellow
Write-Host "  - 6379 (Redis)" -ForegroundColor Yellow
