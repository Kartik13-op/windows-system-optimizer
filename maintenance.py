"""Action catalog. Commands run only when the user explicitly selects Run."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    title: str
    description: str
    script: str = ""
    target: str = ""
    arguments: tuple = ()
    admin: bool = False
    servicing: bool = False


TEMP_CLEANER = r"""
function Remove-AgedTempFiles([string]$Folder) {
    $expected = [IO.Path]::GetFullPath($Folder)
    $root = Get-Item -LiteralPath $expected -ErrorAction Stop
    if (-not ($root -is [IO.DirectoryInfo]) -or
        ($root.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        $root.FullName.TrimEnd('\') -ne $expected.TrimEnd('\')) {
        throw 'The temporary directory must be a real directory at the expected path.'
    }
    $cutoff = (Get-Date).AddDays(-7)
    $pending = New-Object 'System.Collections.Generic.Stack[System.IO.DirectoryInfo]'
    $pending.Push($root)
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        try { $entries = $directory.GetFileSystemInfos() }
        catch { Write-Error $_; continue }
        foreach ($entry in $entries) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                Write-Host "Skipped link: $($entry.FullName)"
            } elseif ($entry -is [IO.DirectoryInfo]) {
                $pending.Push($entry)
            } elseif ($entry.LastWriteTime -lt $cutoff) {
                try {
                    $entry.Delete()
                    Write-Host "Deleted: $($entry.FullName)"
                } catch { Write-Error $_ }
            }
        }
    }
}
"""

DEFENDER_CANCEL = r"""
$platform = Join-Path $env:ProgramData 'Microsoft\Windows Defender\Platform'
$mp = $null
if (Test-Path -LiteralPath $platform) {
    $mp = Get-ChildItem -LiteralPath $platform -Directory |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $mp) { $mp = Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe' }
& $mp -Scan -Cancel
"""

REPORT_FOLDER = r"""
$reports = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'WindowsOptimizer\Reports'
New-Item -ItemType Directory -Path $reports -Force
"""

ACTIONS = {
    "user_temp": Action("Clean old user temporary files", "Deletes files older than 7 days in your local Temp folder. Keeps folders, recent files, and links; shows locked-file errors.", TEMP_CLEANER + "\nRemove-AgedTempFiles (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Temp')"),
    "windows_temp": Action("Clean old Windows temporary files", "Deletes files older than 7 days in Windows\\Temp. Keeps folders, recent files, and links; shows locked-file errors.", TEMP_CLEANER + "\nRemove-AgedTempFiles (Join-Path $env:SystemRoot 'Temp')", admin=True),
    "dns_flush": Action("Refresh DNS cache", "Clears cached DNS answers to help resolve stale name lookups.", "ipconfig.exe /flushdns", admin=True),
    "optimize": Action("Optimize the system drive", "Runs Windows' media-appropriate optimization: HDD optimization or SSD retrim. This can take time.", "defrag.exe $env:SystemDrive /O /U /V", admin=True),
    "drive_analysis": Action("Analyze the system drive", "Displays fragmentation and optimization information without requesting optimization.", "defrag.exe $env:SystemDrive /A /V", admin=True),
    "component_cleanup": Action("Clean superseded Windows components", "DISM removes older component versions immediately, without the scheduled task's 30-day grace period. Can take time.", "DISM.exe /Online /Cleanup-Image /StartComponentCleanup", admin=True, servicing=True),
    "component_analysis": Action("Analyze the component store", "Reports the Windows component store size and cleanup recommendation.", "DISM.exe /Online /Cleanup-Image /AnalyzeComponentStore", admin=True, servicing=True),
    "delivery_cache": Action("Clear Delivery Optimization cache", "Uses Windows' supported cmdlet to remove cached update-delivery files.", "Delete-DeliveryOptimizationCache -Force", admin=True),
    "quick_scan": Action("Update Defender and run a quick scan", "Downloads security intelligence, then starts a Defender quick scan. Review detections in Windows Security.", "Update-MpSignature\nStart-MpScan -ScanType QuickScan", admin=True),
    "full_scan": Action("Update Defender and run a full scan", "Downloads security intelligence, then scans all files and programs with Defender. Can take hours.", "Update-MpSignature\nStart-MpScan -ScanType FullScan", admin=True),
    "signature_update": Action("Update Defender security intelligence", "Downloads the latest signatures using Microsoft's configured update sources.", "Update-MpSignature", admin=True),
    "cancel_scan": Action("Cancel an active Defender scan", "Asks Defender to cancel an active quick or full scan. Closing a console alone may leave the scan running.", DEFENDER_CANCEL, admin=True),
    "protection_status": Action("Show Defender protection status", "Displays antivirus, real-time protection, signature versions, and recent scan dates.", "Get-MpComputerStatus | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureVersion,AntivirusSignatureLastUpdated,QuickScanEndTime,FullScanEndTime | Format-List"),
    "threat_history": Action("Show Defender detection history", "Lists recorded detections and actions taken by Defender.", "Get-MpThreatDetection | Format-List", admin=True),
    "firewall_status": Action("Review firewall profiles", "Displays whether Domain, Private, and Public firewall profiles are enabled and their default actions.", "Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction | Format-Table -AutoSize"),
    "encryption_status": Action("Show drive encryption status", "Reports BitLocker encryption and protection status for local volumes.", "manage-bde.exe -status", admin=True),
    "dism_check": Action("Quick Windows image check", "Checks whether the component store has already recorded corruption.", "DISM.exe /Online /Cleanup-Image /CheckHealth", admin=True, servicing=True),
    "dism_scan": Action("Deep Windows image scan", "Scans the component store for corruption without requesting repairs.", "DISM.exe /Online /Cleanup-Image /ScanHealth", admin=True, servicing=True),
    "dism_repair": Action("Repair the Windows image", "Repairs the component store, using Windows Update as needed. Can take time.", "DISM.exe /Online /Cleanup-Image /RestoreHealth", admin=True, servicing=True),
    "sfc_verify": Action("Verify protected system files", "Scans protected Windows files without requesting repairs.", "sfc.exe /verifyonly", admin=True, servicing=True),
    "sfc_repair": Action("Repair protected system files", "Runs System File Checker to find and repair damaged protected Windows files.", "sfc.exe /scannow", admin=True, servicing=True),
    "restore_point": Action("Create a system restore point", "Requests a restore point. Windows may reject it if protection is off or another point was created recently.", "Checkpoint-Computer -Description 'Windows Optimizer manual restore point' -RestorePointType MODIFY_SETTINGS", admin=True),
    "disk_scan": Action("Scan the system filesystem online", "Runs CHKDSK /scan on the system drive; requests no forced dismount or restart.", "chkdsk.exe $env:SystemDrive /scan", admin=True),
    "disk_health": Action("Show physical disk health", "Displays physical disk health, operational state, media type, and size.", "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,Size | Format-Table -AutoSize"),
    "disk_space": Action("Show volume space", "Lists local volumes, filesystems, total size, and remaining free space.", "Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,HealthStatus,Size,SizeRemaining | Format-Table -AutoSize"),
    "trim_status": Action("Show TRIM notification settings", "Queries Windows' NTFS/ReFS delete-notification configuration.", "fsutil.exe behavior query DisableDeleteNotify", admin=True),
    "network_config": Action("Show full network configuration", "Displays adapter, DHCP, gateway, and DNS configuration.", "ipconfig.exe /all"),
    "network_test": Action("Test HTTPS connectivity", "Tests DNS and TCP connectivity to www.microsoft.com on port 443.", "Test-NetConnection -ComputerName www.microsoft.com -Port 443 -InformationLevel Detailed"),
    "wifi_info": Action("Show Wi-Fi connection details", "Displays wireless interface and connection information.", "netsh.exe wlan show interfaces"),
    "wifi_report": Action("Generate a Wi-Fi diagnostics report", "Writes Windows' recent Wi-Fi session report. The console displays its local file path.", "netsh.exe wlan show wlanreport", admin=True),
    "winsock_reset": Action("Reset Winsock catalog", "Resets socket providers to help repair network faults. A restart is needed; VPN/network software may be affected.", "netsh.exe winsock reset", admin=True),
    "power_status": Action("Show power plans", "Lists available power plans and the active plan.", "powercfg.exe /list\npowercfg.exe /getactivescheme"),
    "balanced": Action("Use the Balanced power plan", "Switches to Windows' Balanced power scheme. This changes your current power plan.", "powercfg.exe /setactive SCHEME_BALANCED", admin=True),
    "high_performance": Action("Use the High performance plan", "Switches power plans if available. Can increase power consumption, heat, and battery use.", "powercfg.exe /setactive SCHEME_MIN", admin=True),
    "battery_report": Action("Generate and open a battery report", "Creates an HTML battery-history report in your local WindowsOptimizer\\Reports folder and opens it.", REPORT_FOLDER + "\n$report = Join-Path $reports 'battery-report.html'\npowercfg.exe /batteryreport /output $report\nInvoke-Item -LiteralPath $report"),
    "energy_report": Action("Generate and open an energy report", "Analyzes energy efficiency for 60 seconds, writes an HTML report, and opens it. Keep the computer idle during capture.", REPORT_FOLDER + "\n$report = Join-Path $reports 'energy-report.html'\npowercfg.exe /energy /duration 60 /output $report\nInvoke-Item -LiteralPath $report", admin=True),
    "sleep_blockers": Action("Show sleep blockers", "Displays active processes or drivers requesting that Windows remain awake.", "powercfg.exe /requests", admin=True),
    "wake_history": Action("Show wake history and timers", "Displays the last wake source and scheduled wake timers.", "powercfg.exe /lastwake\npowercfg.exe /waketimers", admin=True),
    "app_updates": Action("Find available app updates", "Uses WinGet to list available updates. Source agreement prompts remain visible.", "winget.exe upgrade"),
    "upgrade_apps": Action("Install all available app updates", "Runs winget upgrade --all. Installer, license, and elevation prompts remain interactive; running apps may need to close.", "winget.exe upgrade --all"),
    "installed_apps": Action("List installed applications", "Displays applications recognized by Windows Package Manager.", "winget.exe list"),
    "hotfixes": Action("List installed Windows hotfixes", "Lists installed hotfixes by installation date.", "Get-HotFix | Sort-Object InstalledOn -Descending | Format-Table -AutoSize"),
    "system_info": Action("Show a system summary", "Displays Windows version, processor, memory, and boot information.", "Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsName,OsVersion,OsLastBootUpTime,CsManufacturer,CsModel,CsTotalPhysicalMemory,CsProcessors | Format-List"),
    "startup_inventory": Action("List startup commands", "Displays startup program names, commands, locations, and users.", "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User | Format-Table -AutoSize"),
    "recent_errors": Action("Show recent system errors", "Displays up to 30 error events from the last 7 days in the System event log.", "Get-WinEvent -FilterHashtable @{LogName='System';Level=2;StartTime=(Get-Date).AddDays(-7)} -MaxEvents 30 | Select-Object TimeCreated,ProviderName,Message | Format-List", admin=True),
    "drives": Action("Optimize Drives window", "Choose drives and inspect Windows' scheduled optimization settings.", target="dfrgui.exe"),
    "power": Action("Power settings", "Open modern Windows power and sleep settings.", target="ms-settings:powersleep"),
    "startup": Action("Startup apps settings", "Choose which apps start when you sign in.", target="ms-settings:startupapps"),
    "cleanup": Action("Disk Cleanup window", "Choose a drive and cleanup categories in Windows' interactive cleanup tool.", target="cleanmgr.exe", admin=True),
    "storage": Action("Storage settings", "Review storage use and additional cleanup options.", target="ms-settings:storagesense"),
    "security": Action("Windows Security settings", "Open Windows Security to review detections and manage scans.", target="ms-settings:windowsdefender"),
    "updates": Action("Windows Update settings", "Choose Windows updates and restart timing.", target="ms-settings:windowsupdate"),
    "task_manager": Action("Task Manager", "Inspect running apps, startup load, and resource usage.", target="taskmgr.exe"),
    "resources": Action("Resource Monitor", "Inspect CPU, memory, storage, and network activity.", target="resmon.exe"),
    "reliability": Action("Reliability Monitor", "View the timeline of app failures, crashes, and updates.", target="perfmon.exe", arguments=("/rel",)),
    "events": Action("Event Viewer", "Browse Windows application and system event logs.", target="eventvwr.exe"),
    "memory_test": Action("Windows Memory Diagnostic", "Windows asks whether to restart now or check memory on the next restart.", target="mdsched.exe"),
    "restore_ui": Action("System Restore", "Choose a restore point using the Windows restore wizard.", target="rstrui.exe"),
    "system_ui": Action("System Information", "Inspect hardware resources, components, and the software environment.", target="msinfo32.exe"),
    "directx": Action("DirectX Diagnostic Tool", "Inspect display, audio, and DirectX driver information.", target="dxdiag.exe"),
}

# Category: (description, action IDs in display order, preselected action IDs).
CATEGORIES = {
    "Fast Optimize": ("Run focused maintenance, or inspect what is slowing your PC down.", ("user_temp", "dns_flush", "optimize", "startup_inventory", "task_manager", "resources", "power", "startup"), ("user_temp", "dns_flush")),
    "Deep Cleaning": ("Review the scope below, then run cleanup directly.", ("user_temp", "windows_temp", "delivery_cache", "component_analysis", "component_cleanup", "cleanup", "storage"), ("user_temp", "windows_temp")),
    "Fast Security check": ("Start a quick Defender scan and inspect protection directly.", ("quick_scan", "signature_update", "protection_status", "firewall_status", "cancel_scan", "security"), ("quick_scan",)),
    "Deep Security check": ("Run a full scan and review threats, firewall, and encryption.", ("full_scan", "threat_history", "firewall_status", "encryption_status", "cancel_scan", "security", "updates"), ("full_scan",)),
    "System Repair": ("DISM and SFC tasks selected together run in one console, in this order. Ctrl+C stops that batch.", ("restore_point", "dism_check", "dism_scan", "dism_repair", "sfc_verify", "sfc_repair", "memory_test", "restore_ui"), ("dism_check",)),
    "Storage & Disks": ("Analyze, optimize, or inspect the system drive and storage health.", ("disk_space", "disk_health", "drive_analysis", "optimize", "disk_scan", "trim_status", "component_analysis", "drives"), ("disk_space", "disk_health")),
    "Network Tools": ("Diagnose connectivity or choose a targeted network repair.", ("dns_flush", "network_config", "network_test", "wifi_info", "wifi_report", "winsock_reset"), ("network_config", "network_test")),
    "Power & Battery": ("Inspect energy use, generate reports, or change power plans.", ("power_status", "battery_report", "energy_report", "sleep_blockers", "wake_history", "balanced", "high_performance", "power"), ("power_status",)),
    "Apps & Updates": ("Find or install app updates using WinGet, with its normal prompts.", ("app_updates", "upgrade_apps", "installed_apps", "hotfixes", "updates"), ("app_updates",)),
    "Diagnostics": ("Explore Windows health, logs, hardware, and resource usage.", ("system_info", "startup_inventory", "recent_errors", "reliability", "events", "resources", "task_manager", "system_ui", "directx"), ("system_info",)),
}
