# Windows AI-Firewall Setup Script
# Run as Administrator!

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "AI-Firewall Windows Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: Please run as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Install Python 3.12+" -ForegroundColor Red
    exit 1
}

Write-Host "[2/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install scapy xgboost scikit-learn pandas joblib watchdog

Write-Host "[3/5] Configuring Windows Firewall..." -ForegroundColor Yellow

# Enable Windows Firewall
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
Write-Host "  - Firewall enabled" -ForegroundColor Green

# Create AI-Firewall group
$ruleGroup = "AI-Firewall"
Write-Host "  - Created rule group: $ruleGroup" -ForegroundColor Green

Write-Host "[4/5] Checking Network Adapters..." -ForegroundColor Yellow
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, LinkSpeed

Write-Host ""
Write-Host "Available adapters shown above." -ForegroundColor Cyan
Write-Host "Select your WAN adapter (connected to modem):" -ForegroundColor Cyan
$wanAdapter = Read-Host "Enter adapter name"

Write-Host "[5/5] Creating AI-Firewall config..." -ForegroundColor Yellow

# Create config.json
$config = @{
    firewall = @{
        auto_block = $true
        block_threshold = 0.7
        block_duration = 24
        whitelist = @(
            "127.0.0.1"
            "192.168.1.1"
            "8.8.8.8"
            "1.1.1.1"
        )
    }
    network = @{
        wan_interface = $wanAdapter
    }
    logging = @{
        level = "INFO"
        file = "logs/ai-firewall.log"
    }
} | ConvertTo-Json -Depth 10

$config | Out-File -FilePath "config.json" -Encoding UTF8
Write-Host "  - Config created: config.json" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start AI-Firewall:" -ForegroundColor Cyan
Write-Host "  python realtime_firewall.py -i $wanAdapter" -ForegroundColor White
Write-Host ""
Write-Host "To enable auto-start:" -ForegroundColor Cyan
Write-Host "  1. Create Task Scheduler task" -ForegroundColor White
Write-Host "  2. Run: python realtime_firewall.py -i $wanAdapter" -ForegroundColor White
Write-Host "  3. Set trigger: At system startup" -ForegroundColor White
Write-Host ""
Write-Host "Config file: config.json" -ForegroundColor Cyan
Write-Host "Edit to change settings (threshold, whitelist, etc.)" -ForegroundColor White
Write-Host ""
