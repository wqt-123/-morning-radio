# ============================================================
# 服务器 SSH Key 配置脚本
# 用于：服务器首次从 GitHub 拉取代码时配置 SSH 密钥
# ============================================================
param(
    [string]$ServerIP = "8.154.22.214",
    [string]$ServerUser = "Administrator",
    [string]$ServerPass = "Wqt158205"
)

$publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIjAlu1L6lF43KiO83/GhW5P5d4V9+XPnWFJ1gfE+ZM1 WQT-123@github"

$secPass = ConvertTo-SecureString $ServerPass -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($ServerUser, $secPass)

$session = New-PSSession -ComputerName $ServerIP -Credential $cred

Invoke-Command -Session $session -ScriptBlock {
    param($pubKey)
    
    $sshDir = "$env:USERPROFILE\.ssh"
    if (!(Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }
    
    # 生成 SSH 密钥
    if (!(Test-Path "$sshDir\id_ed25519")) {
        ssh-keygen -t ed25519 -C "morning-radio-server" -f "$sshDir\id_ed25519" -N '""' 2>&1
        Write-Host "SSH 密钥已生成"
    }
    
    # 配置 SSH config (GitHub 443 端口)
    @"
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519
"@ | Out-File -FilePath "$sshDir\config" -Encoding ASCII -Force
    
    # 添加 GitHub to known_hosts
    ssh-keyscan -p 443 ssh.github.com >> "$sshDir\known_hosts" 2>$null
    
    # 输出公钥（需要添加到 GitHub）
    Write-Host "===== 服务器公钥（请添加到 GitHub Deploy Keys）====="
    Get-Content "$sshDir\id_ed25519.pub"
    Write-Host "====================================================="
    
} -ArgumentList $publicKey

Remove-PSSession $session
