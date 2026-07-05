@echo off
REM ============================================================
REM 早安电台 - 服务器端独立部署脚本
REM 使用方法：将此文件放到服务器上，右键"以管理员身份运行"
REM ============================================================
title 早安电台服务器部署
echo ===== 早安电台服务器部署 =====
echo.

REM ---- 0. 安装 Chocolatey (包管理器) ----
echo [0] 检查 Chocolatey...
where choco >nul 2>&1
if %errorlevel% neq 0 (
    echo   安装 Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
)

REM ---- 1. 安装 Git ----
echo [1] 检查 Git...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo   安装 Git...
    choco install git -y --no-progress
)
git --version

REM ---- 2. 安装 Python 3.11 ----
echo [2] 检查 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   安装 Python 3.11...
    choco install python311 -y --no-progress
)
python --version

REM ---- 3. 配置 SSH Key (用于 GitHub) ----
echo [3] 配置 GitHub SSH 连接...
if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"

REM 生成 SSH 密钥（如不存在）
if not exist "%USERPROFILE%\.ssh\id_ed25519" (
    ssh-keygen -t ed25519 -C "morning-radio-server" -f "%USERPROFILE%\.ssh\id_ed25519" -N ""
    echo   SSH 密钥已生成
    echo.
    echo   ==============================================================
    echo   [重要] 请将此公钥添加到 GitHub Deploy Keys:
    echo   https://github.com/WQT-123/morning-radio/settings/keys
    echo.
    type "%USERPROFILE%\.ssh\id_ed25519.pub"
    echo   ==============================================================
    echo.
    pause
)

REM 配置 SSH 走 443 端口（绕过 GFW）
echo Host github.com > "%USERPROFILE%\.ssh\config"
echo   HostName ssh.github.com >> "%USERPROFILE%\.ssh\config"
echo   Port 443 >> "%USERPROFILE%\.ssh\config"
echo   User git >> "%USERPROFILE%\.ssh\config"

REM 添加 known_hosts
ssh-keyscan -p 443 ssh.github.com >> "%USERPROFILE%\.ssh\known_hosts" 2>nul

REM ---- 4. 克隆项目 ----
echo [4] 克隆项目代码...
cd C:\
if exist "C:\morning-radio" (
    echo   备份旧项目...
    move "C:\morning-radio" "C:\morning-radio.bak.%date:~0,4%%date:~5,2%%date:~8,2%" >nul 2>&1
)
git clone git@github.com:WQT-123/morning-radio.git C:\morning-radio
if %errorlevel% neq 0 (
    echo   [FAIL] 克隆失败，请检查 SSH 密钥配置
    pause
    exit /b 1
)
echo   克隆完成

REM ---- 5. 安装后端依赖 ----
echo [5] 安装 Python 依赖...
cd C:\morning-radio\backend
python -m pip install --upgrade pip
pip install -r requirements.txt

REM ---- 6. 安装 Nginx ----
echo [6] 检查 Nginx...
if not exist "C:\nginx\nginx.exe" (
    echo   下载 Nginx...
    choco install nginx -y --no-progress
    REM 如果 choco 失败，手动下载
    if not exist "C:\nginx\nginx.exe" (
        powershell -Command "Invoke-WebRequest -Uri 'https://nginx.org/download/nginx-1.24.0.zip' -OutFile 'C:\nginx.zip'"
        powershell -Command "Expand-Archive -Path 'C:\nginx.zip' -DestinationPath 'C:\' -Force"
        rename "C:\nginx-1.24.0" "nginx" 2>nul
    )
)
echo   Nginx 就绪

REM ---- 7. 配置 Nginx 反向代理 ----
echo [7] 配置 Nginx...
copy /Y "C:\morning-radio\deploy\nginx.conf" "C:\nginx\conf\nginx.conf"
cd C:\nginx
start nginx.exe
echo   Nginx 已启动

REM ---- 8. 下载 NSSM ----
echo [8] 下载 NSSM...
if not exist "C:\nssm\nssm.exe" (
    mkdir C:\nssm 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'C:\nssm.zip'"
    powershell -Command "Expand-Archive -Path 'C:\nssm.zip' -DestinationPath 'C:\nssm_tmp' -Force"
    copy "C:\nssm_tmp\nssm-2.24\win64\nssm.exe" "C:\nssm\nssm.exe"
)
echo   NSSM 就绪

REM ---- 9. 注册 Windows 服务 ----
echo [9] 注册 Windows 服务...
C:\nssm\nssm.exe stop MorningRadio-API 2>nul
C:\nssm\nssm.exe remove MorningRadio-API confirm 2>nul
C:\nssm\nssm.exe install MorningRadio-API python "C:\morning-radio\backend\run.py"
C:\nssm\nssm.exe set MorningRadio-API AppDirectory "C:\morning-radio\backend"
C:\nssm\nssm.exe set MorningRadio-API DisplayName "MorningRadio API Service"
C:\nssm\nssm.exe set MorningRadio-API Start SERVICE_AUTO_START
C:\nssm\nssm.exe start MorningRadio-API

echo   ==== 部署完成 ====
echo.
echo   访问地址: http://8.154.22.214
echo   API 文档: http://8.154.22.214/api/docs
echo.
pause
