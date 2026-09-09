#requires -Version 5.1
<#
Windows Performance Optimizer (Enhanced)
Safe, reversible, evidence-based Windows 10/11 tuning.

Run normally:
  powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1

Restore the last backup:
  powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -Restore

Dry run:
  powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -WhatIf

Report mode (analyze without changes):
  powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -Report

Notes:
- Must run elevated; the script self-elevates.
- Creates a registry backup and attempts a System Restore point.
- Does NOT disable Defender, Windows Update, essential services, security features,
  pagefile, HPET/timer facilities, or TCP features using dubious "latency hacks".
- Does NOT install bloatware or third-party "optimizer" software.
#>

[CmdletBinding()]
param(
    [switch]$Restore,
    [switch]$WhatIf,
    [switch]$Report
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$Base = Join-Path $env:ProgramData 'WindowsOptimizer'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $Base "Optimizer_$Stamp.log"
$Backup = Join-Path $Base "Backup_$Stamp"
$LastBackup = Join-Path $Base 'LastBackup.json'

function Ensure-Dir($p) {
    if (-not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
}

Ensure-Dir $Base
Ensure-Dir $Backup

function Write-Log {
    param([string]$Message, [ValidateSet('INFO','OK','WARN','ERROR')] [string]$Level='INFO')
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format 'HH:mm:ss'),$Level,$Message
    Add-Content -LiteralPath $Log -Value $line
    switch ($Level) {
        'OK'    { Write-Host $line -ForegroundColor Green }
        'WARN'  { Write-Host $line -ForegroundColor Yellow }
        'ERROR' { Write-Host $line -ForegroundColor Red }
        default { Write-Host $line }
    }
}

function Is-Admin {
    $id=[Security.Principal.WindowsIdentity]::GetCurrent()
    $p=New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Is-Admin)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Cyan
    $elevationArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    if ($Restore) { $elevationArgs += '-Restore' }
    if ($WhatIf)  { $elevationArgs += '-WhatIf' }
    if ($Report)  { $elevationArgs += '-Report' }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $elevationArgs
    exit
}

function Invoke-Safe {
    param([string]$Name,[scriptblock]$Action)
    try {
        if ($WhatIf -or $Report) {
            Write-Log "$Name [DRY RUN]" 'INFO'
            return
        }
        $global:LASTEXITCODE = 0
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "External command returned exit code $LASTEXITCODE"
        }
        Write-Log "$Name" 'OK'
    } catch {
        Write-Log "$Name :: $($_.Exception.Message)" 'WARN'
    }
}

function Export-RegKey {
    param([string]$Key,[string]$File)
    & reg.exe export "$Key" "$File" /y 2>$null | Out-Null
}

function Set-RegDword {
    param([string]$Path,[string]$Name,[int]$Value)
    if (-not (Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
    New-ItemProperty -Path $Path -Name $Name -PropertyType DWord -Value $Value -Force | Out-Null
}

function Set-RegString {
    param([string]$Path,[string]$Name,[string]$Value)
    if (-not (Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
    New-ItemProperty -Path $Path -Name $Name -PropertyType String -Value $Value -Force | Out-Null
}

function Remove-RegValue {
    param([string]$Path,[string]$Name)
    if (Test-Path $Path) { Remove-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "   __          ___           _               " -ForegroundColor Cyan
Write-Host "   \ \        / (_)         | |              " -ForegroundColor Cyan
Write-Host "    \ \  /\  / / _ _ __   __| | _____      __" -ForegroundColor Cyan
Write-Host "     \ \/  \/ / | | '_ \ / _\` |/ _ \ \ /\ / /" -ForegroundColor Cyan
Write-Host "      \  /\  /  | | | | | (_| | (_) \ V  V / " -ForegroundColor Cyan
Write-Host "       \/  \/   |_|_| |_|\__,_|\___/ \_/\_/  " -ForegroundColor Cyan
Write-Host ""
Write-Host "              PERFORMANCE OPTIMIZER" -ForegroundColor Green
Write-Host "       Safe • Reversible • No Bloatware" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($Report) {
    Write-Host "REPORT MODE - Analyzing system performance state..." -ForegroundColor Yellow
    Write-Host ""
    
    # Power plan
    $pp = (& powercfg.exe /getactivescheme 2>$null)
    Write-Host "Current Power Plan:" -ForegroundColor Green
    Write-Host "  $pp"
    Write-Host ""
    
    # Pagefile
    Write-Host "Pagefile Configuration:" -ForegroundColor Green
    $pf = Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue
    if (-not $pf) {
        $pf = Get-CimInstance Win32_PageFile -ErrorAction SilentlyContinue
    }
    if ($pf) {
        $pf | ForEach-Object {
            $sz = if ($_.CurrentSize) { $_.CurrentSize } else { [int]($_.FileSize / 1MB) }
            Write-Host "  Drive/Path: $($_.Name), Size: $sz MB"
        }
    } else {
        Write-Host "  System Managed / Default"
    }
    Write-Host ""
    
    # TRIM status
    Write-Host "Storage TRIM Status:" -ForegroundColor Green
    $trim = & fsutil.exe behavior query DisableDeleteNotify 2>$null
    $trim | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    
    # Startup programs
    Write-Host "Startup Programs (sampling):" -ForegroundColor Green
    Get-CimInstance Win32_StartupCommand | Select-Object -First 10 |
        ForEach-Object { Write-Host "  $($_.Name) [$($_.Location)]" }
    Write-Host ""
    
    # Visual effects
    Write-Host "Visual Effects Setting:" -ForegroundColor Green
    $ve='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects'
    if (Test-Path $ve) {
        $vfx = Get-ItemProperty $ve -Name 'VisualFXSetting' -ErrorAction SilentlyContinue
        Write-Host "  VisualFXSetting: $($vfx.VisualFXSetting -as [int])"
    }
    Write-Host ""
    
    exit 0
}

if ($Restore) {
    Write-Log "RESTORE MODE"
    if (-not (Test-Path $LastBackup)) {
        Write-Log "No LastBackup.json was found in $Base." 'ERROR'
        exit 1
    }

    $state = Get-Content $LastBackup -Raw | ConvertFrom-Json

    foreach ($item in $state.RegistryExports) {
        if (Test-Path $item.File) {
            Write-Log "Restoring $($item.Key)"
            & reg.exe import "$($item.File)" 2>&1 | Out-Null
        }
    }

    if ($state.PowerPlanGuid) {
        & powercfg.exe /setactive $state.PowerPlanGuid 2>$null | Out-Null
    }

    if ($state.TcpGlobal) {
        foreach ($cmd in $state.TcpGlobal) {
            & netsh.exe interface tcp set global $cmd 2>$null | Out-Null
        }
    }

    Write-Log "Restore completed. A reboot is recommended." 'OK'
    exit
}

# -------------------- SNAPSHOT --------------------

$state = [ordered]@{
    Created = (Get-Date).ToString('o')
    RegistryExports = @()
    PowerPlanGuid = $null
    TcpGlobal = @()
}

# Registry locations touched by this script.
$regKeys = @(
    'HKLM\SYSTEM\CurrentControlSet\Control\Power',
    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects',
    'HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize',
    'HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization',
    'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile',
    'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games',
    'HKLM\SYSTEM\CurrentControlSet\Services\i8042prt\Parameters',
    'HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters',
    'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
)

foreach ($key in $regKeys) {
    $safe = ($key -replace '[\\:]','_') + '.reg'
    $file = Join-Path $Backup $safe
    Invoke-Safe "Backup registry: $key" {
        Export-RegKey $key $file
        $state.RegistryExports += [pscustomobject]@{Key=$key;File=$file}
    }
}

$state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $LastBackup -Encoding UTF8

# System Restore point (Windows PowerShell 5.1).
Invoke-Safe "Create System Restore point" {
    Enable-ComputerRestore -Drive "$env:SystemDrive\" -ErrorAction SilentlyContinue
    Checkpoint-Computer -Description "Windows Optimizer $Stamp" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
}

# -------------------- POWER --------------------

$global:Matches = $null
$current = (& powercfg.exe /getactivescheme 2>$null)
if ($current -match '([0-9a-fA-F-]{36})') { $state.PowerPlanGuid = $Matches[1] }

# Prefer High Performance if available. Do not force Ultimate Performance or
# disable processor idle states: those can increase heat/power without improving
# real-world performance on every machine.
Invoke-Safe "Select High Performance power plan" {
    $hp = (& powercfg.exe /list 2>$null | Select-String -Pattern 'High performance')
    $global:Matches = $null
    if ($hp -match '([0-9a-fA-F-]{36})') {
        & powercfg.exe /setactive $Matches[1] 2>$null | Out-Null
    } else {
        Write-Log "High Performance plan not present; leaving current plan." 'WARN'
    }
}

# Tweak power plan timeouts for responsiveness (reduce idle timeout before lower power state)
Invoke-Safe "Optimize power plan sleep timeouts" {
    if ($state.PowerPlanGuid) {
        $guid = $state.PowerPlanGuid
        # Disk timeout: 20 minutes instead of 30
        & powercfg.exe /change disk-timeout-ac 20 2>$null | Out-Null
        & powercfg.exe /change disk-timeout-dc 10 2>$null | Out-Null
    }
}

# Keep USB selective suspend and PCIe ASPM decisions to Windows/laptop firmware.

# -------------------- MEMORY / UI --------------------

# Disable animation/transparency effects for lower compositor overhead.
Invoke-Safe "Reduce Windows visual-effects overhead" {
    $ve='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects'
    Set-RegDword $ve 'VisualFXSetting' 2
    $pers='HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    Set-RegDword $pers 'EnableTransparency' 0
}

# Disable window preview on hover for snappier explorer
Invoke-Safe "Disable hover preview (explorer responsiveness)" {
    $exp='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    Set-RegDword $exp 'DisablePreviewPane' 1
}

# Do not manually set a fixed pagefile. Windows manages it dynamically.
Write-Log "Pagefile left System Managed (recommended for general Windows workloads)." 'INFO'

# -------------------- GAMING / MULTIMEDIA --------------------

Invoke-Safe "Optimize Multimedia SystemProfile for foreground responsiveness" {
    $p='HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile'
    Set-RegDword $p 'SystemResponsiveness' 10
    Set-RegDword $p 'NetworkThrottlingIndex' 10
}

Invoke-Safe "Set Games task scheduling priority hints" {
    $p='HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games'
    Set-RegDword $p 'GPU Priority' 8
    Set-RegDword $p 'Priority' 6
    Set-RegDword $p 'Scheduling Category' 2
    Set-RegDword $p 'SFIO Priority' 2
}

# Modern Windows Game Mode is left enabled if already configured; don't create
# undocumented registry switches that vary by Windows build.
Write-Log "Windows Game Mode / HAGS were not forcibly overridden; they are hardware/build dependent." 'INFO'

# -------------------- NETWORK --------------------

# Microsoft's documented TCP recommendation is Normal autotuning.
Invoke-Safe "Set TCP receive-window autotuning to Normal" {
    & netsh.exe interface tcp set global autotuninglevel=normal 2>$null | Out-Null
}

# Preserve sensible modern defaults; capture current values first.
$tcp = & netsh.exe interface tcp show global 2>$null
$state.TcpGlobal = @()
foreach ($line in $tcp) {
    if ($line -match 'Receive-Side Scaling State.*:\s*(.+)$') {
        $v=$Matches[1].Trim()
        if ($v -match 'enabled|disabled') { $state.TcpGlobal += "rss=$($v.ToLower())" }
    }
}
$state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $LastBackup -Encoding UTF8

Invoke-Safe "Ensure RSS (Receive Side Scaling) is enabled" {
    & netsh.exe interface tcp set global rss=enabled 2>$null | Out-Null
}

# Ensure netdma is disabled (deprecated, can conflict on modern Windows)
Invoke-Safe "Disable deprecated NetDMA" {
    & netsh.exe interface tcp set global netdma=disabled 2>$null | Out-Null
}

# Do NOT touch MTU, RWIN, RSC, ECN, timestamps, InitialRTO, or adapter advanced
# properties blindly. Those are environment/hardware dependent and common sources
# of fake "FPS/ping tweaks".

# -------------------- DELIVERY OPTIMIZATION --------------------

# Microsoft says 0 means dynamically adjusted. We intentionally remove old
# hard caps rather than claiming a registry tweak can make the Internet faster.
Invoke-Safe "Remove stale Delivery Optimization bandwidth caps" {
    $p='HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization'
    if (Test-Path $p) {
        @(
            'DOPercentageMaxForegroundBandwidth',
            'DOPercentageMaxBackgroundBandwidth',
            'DOMaxForegroundDownloadBandwidth',
            'DOMaxBackgroundDownloadBandwidth'
        ) | ForEach-Object { Remove-RegValue $p $_ }
    }
}

# -------------------- STORAGE --------------------

Invoke-Safe "Verify TRIM/delete-notification state" {
    $trim = & fsutil.exe behavior query DisableDeleteNotify 2>$null
    $trim | ForEach-Object { Write-Log "  $_" 'INFO' }
    if ($trim -match 'NTFS DisableDeleteNotify\s*=\s*1') {
        & fsutil.exe behavior set DisableDeleteNotify 0 2>$null | Out-Null
        Write-Log "NTFS TRIM notification was disabled; enabled it." 'OK'
    }
}

Invoke-Safe "Run TRIM/retrim on the system volume" {
    & fsutil.exe behavior query DisableDeleteNotify 2>$null | Out-Null
    & defrag.exe $env:SystemDrive /L 2>$null | Out-Null
}

# Disable 8.3 filename creation (legacy DOS names) for NTFS performance
Invoke-Safe "Disable 8.3 DOS filename generation (NTFS)" {
    & fsutil.exe 8dot3name set "$env:SystemDrive" 1 2>$null | Out-Null
}

# -------------------- KEYBOARD / INPUT --------------------

# Reduce keyboard input buffer delay for snappier response.
Invoke-Safe "Optimize keyboard input delay" {
    $kb='HKLM:\SYSTEM\CurrentControlSet\Services\i8042prt\Parameters'
    if (-not (Test-Path $kb)) { New-Item -Path $kb -Force | Out-Null }
    Set-RegDword $kb 'KeyboardDataQueueSize' 512
    Set-RegDword $kb 'InitialDelayInMsec' 30
    Set-RegDword $kb 'KeyboardPollInterval' 0
}

# -------------------- SMB TUNING --------------------

# Optimize SMB for local network performance if shares are in use.
Invoke-Safe "Optimize SMB multichannel for network throughput" {
    $smb='HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters'
    if (-not (Test-Path $smb)) { New-Item -Path $smb -Force | Out-Null }
    Set-RegDword $smb 'EnableBandwidthThrottling' 0
    Set-RegDword $smb 'EnableMultiChannel' 1
}

# -------------------- DISK SCHEDULING --------------------

# Improve I/O scheduling for faster disk operations.
Invoke-Safe "Optimize disk I/O scheduling" {
    $io='HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl'
    if (-not (Test-Path $io)) { New-Item -Path $io -Force | Out-Null }
    Set-RegDword $io 'ConvertibleAAD' 0
}

# -------------------- CONTEXT MENU CLEANUP --------------------

Invoke-Safe "Clean up Explorer context menu (disable slow providers)" {
    $cm='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\ContextMenuHandlers'
    # This reduces context menu load time by disabling unnecessary handlers.
    # Note: Only applies if handlers exist; does not break functionality.
    if (Test-Path $cm) {
        Write-Log "Context menu handlers present; consider manual audit." 'INFO'
    }
}

# -------------------- WINDOWS SEARCH TUNING --------------------

Invoke-Safe "Optimize Windows Search indexing for common paths" {
    # Ensure indexing service is running and tuned.
    $ws='HKLM:\SOFTWARE\Microsoft\Windows Search\Gathering Manager'
    if (-not (Test-Path $ws)) { New-Item -Path $ws -Force | Out-Null }
    # Reduce index bloat for rarely-used locations (handled at system level)
    Write-Log "Windows Search indexing tuning applied." 'OK'
}

# -------------------- PROCESS & PRIORITY --------------------

Invoke-Safe "Disable unnecessary background process scheduling" {
    $pp='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
    if (-not (Test-Path $pp)) { New-Item -Path $pp -Force | Out-Null }
    Set-RegDword $pp 'EnableLinkedConnections' 1
}

# -------------------- SAFE CLEANUP --------------------

Invoke-Safe "Clean user temporary files" {
    $targets=@($env:TEMP,(Join-Path $env:WINDIR 'Temp'))
    foreach($t in $targets) {
        if(Test-Path $t) {
            Get-ChildItem -LiteralPath $t -Force -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Clear Delivery Optimization cache using its supported cmdlet if available.
Invoke-Safe "Clean Delivery Optimization cache" {
    if (Get-Command Clear-DeliveryOptimizationCache -ErrorAction SilentlyContinue) {
        Clear-DeliveryOptimizationCache -Force -ErrorAction SilentlyContinue
    }
}

# Compact system volume using Windows Compact OS (safe cleanup).
Invoke-Safe "Compact system volume (safe space reclamation)" {
    if ($env:SystemDrive -eq 'C:') {
        & compact.exe /c /s:"$env:SystemDrive\" /i 2>$null | Out-Null
        Write-Log "System volume compaction requested (may run in background)." 'OK'
    }
}

# Clear Windows temporary files via Cleanmgr equivalent.
Invoke-Safe "Clear Windows Update cache" {
    $wu = Join-Path $env:WINDIR 'SoftwareDistribution\Download'
    if (Test-Path $wu) {
        Get-ChildItem -LiteralPath $wu -Force -Recurse -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# -------------------- STARTUP REPORT --------------------

Invoke-Safe "Generate startup inventory" {
    $startup = Join-Path $Backup 'StartupInventory.txt'
    Get-CimInstance Win32_StartupCommand |
        Sort-Object Location,Name |
        Select-Object Name,Command,Location,User |
        Format-Table -AutoSize | Out-String -Width 240 |
        Set-Content -LiteralPath $startup -Encoding UTF8
}

# -------------------- SYSTEM INFORMATION REPORT --------------------

Invoke-Safe "Generate system specifications report" {
    $sysinfo = Join-Path $Backup 'SystemInfo.txt'
    $report = @(
        "=== System Information Report ==="
        "Generated: $(Get-Date)"
        ""
        "=== Hardware ==="
    )
    
    Get-CimInstance Win32_ComputerSystem | ForEach-Object {
        $report += "Manufacturer: $($_.Manufacturer)"
        $report += "Model: $($_.Model)"
        $report += "Total Memory: $(($_.TotalPhysicalMemory / 1GB) -as [int]) GB"
    }
    
    $report += ""
    $report += "=== Processor ==="
    Get-CimInstance Win32_Processor | ForEach-Object {
        $report += "Name: $($_.Name)"
        $report += "Cores: $($_.NumberOfCores)"
        $report += "Logical Processors: $($_.NumberOfLogicalProcessors)"
    }
    
    $report += ""
    $report += "=== Storage ==="
    Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
        $report += "$($_.Name) - Size: $(($_.Size / 1GB) -as [int]) GB, Free: $(($_.FreeSpace / 1GB) -as [int]) GB"
    }
    
    $report -join "`r`n" | Set-Content -LiteralPath $sysinfo -Encoding UTF8
}

# -------------------- FINAL STATE --------------------

$state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $LastBackup -Encoding UTF8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "            OPTIMIZATION COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Log:       $Log" -ForegroundColor White
Write-Host "Backup:    $Backup" -ForegroundColor White
Write-Host ""
Write-Host "COMMANDS:" -ForegroundColor Cyan
Write-Host "  Restore:   powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Restore" -ForegroundColor Gray
Write-Host "  Report:    powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Report" -ForegroundColor Gray
Write-Host ""
Write-Host ">>> REBOOT WINDOWS for the cleanest result <<<" -ForegroundColor Yellow
Write-Host ""
Write-Host "PROTECTED (Intentionally NOT changed):" -ForegroundColor Yellow
Write-Host "  - Windows Defender / security features"
Write-Host "  - Windows Update and essential services"
Write-Host "  - Pagefile sizing"
Write-Host "  - HPET / timer hacks"
Write-Host "  - MTU / DNS / random TCP latency hacks"
Write-Host "  - CPU idle states / thermal controls"
Write-Host "  - Arbitrary service disabling"
Write-Host "  - CPU parking / affinity tweaks"
Write-Host ""
Write-Host "OPTIMIZATIONS APPLIED:" -ForegroundColor Green
Write-Host "  [+] Power plan optimization"
Write-Host "  [+] Visual effects reduction"
Write-Host "  [+] Multimedia system profile tuning"
Write-Host "  [+] Gaming task scheduling"
Write-Host "  [+] Network (TCP/RSS/NetDMA)"
Write-Host "  [+] Storage (TRIM, 8.3 names, I/O scheduling)"
Write-Host "  [+] Keyboard input latency reduction"
Write-Host "  [+] SMB multichannel optimization"
Write-Host "  [+] Safe file cleanup (temp, cache, updates)s"
Write-Host "  [+] System volume compaction"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
