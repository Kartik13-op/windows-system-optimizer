# Action Reference

This document describes every action exposed by Windows Optimizer v1.1.0. The application is a transparent launcher: an “automatic” action means that it starts the listed Windows command in a visible console after the user selects **Run**. It does not monitor the command, suppress its errors, or infer success.

The source links below favor Microsoft documentation. Custom behavior, such as the seven-day Temp cleanup boundary, is linked to its implementation in [`maintenance.py`](../maintenance.py).

## Reading the tables

| Label | Meaning |
| --- | --- |
| Automatic | Starts the documented command directly in a visible PowerShell console. |
| Windows UI | Opens a Windows control where the user chooses what happens. |
| Admin | Displays the normal Windows UAC prompt before launch. |
| Servicing | Runs sequentially with other selected DISM/SFC servicing actions. |
| Diagnostic | Intended to report state; it does not request a configuration change. |

## Cleanup and optimization

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Clean old user temporary files | Automatic | No | Deletes files older than seven days under the current user’s resolved `%LOCALAPPDATA%\Temp`. It preserves directories and recent files, skips reparse points/links, and prints failures for locked files. | [Local bounded implementation](../maintenance.py) |
| Clean old Windows temporary files | Automatic | Yes | Applies the same bounded policy to `%SystemRoot%\Temp`. It does not recursively delete the Temp directory or follow links. | [Local bounded implementation](../maintenance.py) |
| Refresh DNS cache | Automatic | Yes | Runs `ipconfig /flushdns` to clear cached DNS resolver entries. It does not change configured DNS servers or network adapters. | [ipconfig][ipconfig] |
| Optimize the system drive | Automatic | Yes | Runs `defrag %SystemDrive% /O /U /V`; `/O` asks Windows to choose the proper operation for the media type, including retrim where appropriate. | [defrag][defrag] |
| Analyze the system drive | Automatic, diagnostic | Yes | Runs `defrag %SystemDrive% /A /V` to report optimization information without requesting optimization. | [defrag][defrag] |
| Analyze the component store | Automatic, diagnostic, servicing | Yes | Runs DISM `/AnalyzeComponentStore` and displays the component-store report and cleanup recommendation. | [WinSxS/component cleanup][component-cleanup] |
| Clean superseded Windows components | Automatic, servicing | Yes | Runs DISM `/StartComponentCleanup`. Microsoft notes that this can remove superseded component versions immediately rather than waiting for scheduled cleanup. It does not use `/ResetBase`. | [WinSxS/component cleanup][component-cleanup] |
| Clear Delivery Optimization cache | Automatic | Yes | Calls the supported `Delete-DeliveryOptimizationCache -Force` cmdlet for update-delivery cache data. | [Delivery Optimization cache][delivery-cache] |
| Disk Cleanup window | Windows UI | Yes | Opens `cleanmgr.exe`; Windows asks the user to select a drive and cleanup categories. | [cleanmgr][cleanmgr] |
| Storage settings | Windows UI | No | Opens `ms-settings:storagesense` for Windows storage usage and cleanup controls. | [Settings URI reference][settings-uri] |

## Security

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Update Defender and run a quick scan | Automatic | Yes | Runs `Update-MpSignature`, then `Start-MpScan -ScanType QuickScan`. Defender chooses remediation according to its policy; the app does not alter exclusions or protection settings. | [Update-MpSignature][update-mp], [Start-MpScan][start-mp] |
| Update Defender and run a full scan | Automatic | Yes | Updates signatures and starts Defender’s full scan. It can take hours and can outlive its console. | [Start-MpScan][start-mp] |
| Update Defender security intelligence | Automatic | Yes | Runs `Update-MpSignature` using the update sources configured for Microsoft Defender. | [Update-MpSignature][update-mp] |
| Cancel an active Defender scan | Automatic | Yes | Finds the newest installed Defender platform command and runs `MpCmdRun -Scan -Cancel`, which Microsoft documents as an attempt to cancel quick or full scans. | [Defender command line][defender-cli] |
| Show Defender protection status | Automatic, diagnostic | No | Displays antivirus, real-time protection, signature version/update time, and recent quick/full scan times with `Get-MpComputerStatus`. | [Get-MpComputerStatus][mp-status] |
| Show Defender detection history | Automatic, diagnostic | Yes | Displays recorded Defender detections with `Get-MpThreatDetection`. It does not restore or delete quarantine items. | [Get-MpThreatDetection][mp-threat] |
| Review firewall profiles | Automatic, diagnostic | No | Displays Domain, Private, and Public firewall enablement/default actions with `Get-NetFirewallProfile`. It does not change rules. | [Get-NetFirewallProfile][firewall-profile] |
| Show drive encryption status | Automatic, diagnostic | Yes | Runs `manage-bde -status` to report BitLocker state. It does not enable, disable, suspend, or decrypt a volume. | [manage-bde status][manage-bde] |
| Windows Security settings | Windows UI | No | Opens the documented Windows Security Settings page. The user remains responsible for reviewing detections and controls. | [Settings URI reference][settings-uri] |

## Windows repair and recovery

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Quick Windows image check | Automatic, diagnostic, servicing | Yes | Runs DISM `/CheckHealth` to report corruption already recorded for the online image. | [Repair a Windows image][dism-repair] |
| Deep Windows image scan | Automatic, diagnostic, servicing | Yes | Runs DISM `/ScanHealth` to scan the online component store without requesting repair. | [Repair a Windows image][dism-repair] |
| Repair the Windows image | Automatic, servicing | Yes | Runs DISM `/RestoreHealth`; Windows may use its configured repair source, including Windows Update. | [Repair a Windows image][dism-repair] |
| Verify protected system files | Automatic, diagnostic, servicing | Yes | Runs `sfc /verifyonly`, which verifies protected system files without requesting repair. | [sfc][sfc] |
| Repair protected system files | Automatic, servicing | Yes | Runs `sfc /scannow`, which verifies protected files and attempts replacement when possible. | [sfc][sfc] |
| Create a system restore point | Automatic | Yes | Requests `Checkpoint-Computer` with `MODIFY_SETTINGS`. Windows can reject the request when System Protection is disabled or restore-point frequency rules apply. | [Checkpoint-Computer][checkpoint] |
| Windows Memory Diagnostic | Windows UI | No | Opens `mdsched.exe`; Windows lets the user choose whether and when to restart for a memory test. The app never triggers the restart itself. | [Windows Memory Diagnostic][memory-diagnostic] |
| System Restore | Windows UI | No | Opens `rstrui.exe`; the user chooses a restore point and confirms restoration in Windows. | [Windows recovery options][recovery-options] |

## Storage and disks

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Show volume space | Automatic, diagnostic | No | Displays drive letter, filesystem, health, size, and free space from `Get-Volume`. | [Get-Volume][get-volume] |
| Show physical disk health | Automatic, diagnostic | No | Displays physical disk media type, health, operational status, and size from `Get-PhysicalDisk`. | [Get-PhysicalDisk][get-physical-disk] |
| Scan the system filesystem online | Automatic, diagnostic | Yes | Runs `chkdsk %SystemDrive% /scan`. It does not use `/F`, `/R`, `/X`, force a dismount, or schedule a restart repair. | [chkdsk][chkdsk] |
| Show TRIM notification settings | Automatic, diagnostic | Yes | Queries `fsutil behavior query DisableDeleteNotify` for NTFS/ReFS delete-notification state. It does not change the setting. | [fsutil behavior][fsutil-behavior] |
| Optimize Drives window | Windows UI | No | Opens `dfrgui.exe` for Windows drive analysis, optimization, and scheduled-optimization settings. | [Windows drive optimization][drive-optimize-support] |

The Optimize, Analyze, and component-store actions also appear in this category; their behavior is documented under Cleanup and optimization above.

## Network

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Show full network configuration | Automatic, diagnostic | No | Runs `ipconfig /all` to display adapter, DHCP, gateway, and DNS configuration. | [ipconfig][ipconfig] |
| Test HTTPS connectivity | Automatic, diagnostic | No | Runs `Test-NetConnection` to `www.microsoft.com` on TCP 443 and displays DNS/TCP diagnostics. | [Test-NetConnection][test-network] |
| Show Wi-Fi connection details | Automatic, diagnostic | No | Runs `netsh wlan show interfaces` to display current wireless interface state. | [netsh wlan][netsh-wlan] |
| Generate a Wi-Fi diagnostics report | Automatic, diagnostic | Yes | Runs `netsh wlan show wlanreport`; Windows generates a local HTML history report and prints its path. | [Wireless network report][wlan-report] |
| Reset Winsock catalog | Automatic, configuration change | Yes | Runs `netsh winsock reset`. Microsoft describes this as resetting the Winsock catalog; a restart is normally required and custom network providers can be affected. | [netsh winsock][winsock] |

The DNS refresh action is documented under Cleanup and optimization above.

## Power and battery

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Show power plans | Automatic, diagnostic | No | Runs `powercfg /list` and `/getactivescheme`. | [powercfg][powercfg] |
| Use the Balanced power plan | Automatic, configuration change | Yes | Runs `powercfg /setactive SCHEME_BALANCED`. It changes only the active power scheme. | [powercfg][powercfg] |
| Use the High performance plan | Automatic, configuration change | Yes | Runs `powercfg /setactive SCHEME_MIN`, if available. It can increase heat, power use, and battery drain. | [powercfg][powercfg] |
| Generate and open a battery report | Automatic, diagnostic | No | Runs `powercfg /batteryreport` and writes `battery-report.html` under `%LOCALAPPDATA%\WindowsOptimizer\Reports`, then opens it. | [powercfg battery report][powercfg] |
| Generate and open an energy report | Automatic, diagnostic | Yes | Runs `powercfg /energy /duration 60`, writes a local report, and opens it. The 60-second capture works best while the PC is idle. | [powercfg energy report][powercfg] |
| Show sleep blockers | Automatic, diagnostic | Yes | Runs `powercfg /requests` to display processes or drivers asking Windows to stay awake. | [powercfg requests][powercfg] |
| Show wake history and timers | Automatic, diagnostic | Yes | Runs `powercfg /lastwake` and `/waketimers`. It does not remove timers or change device permissions. | [powercfg wake tools][powercfg] |
| Power settings | Windows UI | No | Opens `ms-settings:powersleep`, avoiding the legacy Control Panel shell route that failed on the original test machine. | [Settings URI reference][settings-uri] |

## Applications and updates

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Find available app updates | Automatic, diagnostic | No | Runs `winget upgrade` to list detected upgrades. Source or agreement prompts remain visible. | [WinGet upgrade][winget-upgrade] |
| Install all available app updates | Automatic, software change | No* | Runs `winget upgrade --all`. WinGet and individual installers control prompts, licenses, elevation, closing apps, and results. The optimizer does not add silent agreement flags. | [WinGet upgrade --all][winget-upgrade] |
| List installed applications | Automatic, diagnostic | No | Runs `winget list` for applications recognized by Windows Package Manager. | [WinGet list][winget-list] |
| List installed Windows hotfixes | Automatic, diagnostic | No | Displays `Get-HotFix` results sorted by installation date. | [Get-HotFix][get-hotfix] |
| Windows Update settings | Windows UI | No | Opens `ms-settings:windowsupdate`; the user chooses update and restart actions. | [Settings URI reference][settings-uri] |

\* WinGet or a package installer can independently request UAC.

## Diagnostics and Windows tools

| Action | Type | Admin | What it does and what it does not do | Primary reference |
| --- | --- | --- | --- | --- |
| Show a system summary | Automatic, diagnostic | No | Uses `Get-ComputerInfo` to display Windows, boot, manufacturer, model, memory, and processor information. | [Get-ComputerInfo][computer-info] |
| List startup commands | Automatic, diagnostic | No | Reads `Win32_StartupCommand` and displays names, commands, locations, and users. It does not disable entries. | [Win32_StartupCommand][startup-command] |
| Startup apps settings | Windows UI | No | Opens `ms-settings:startupapps`; the user chooses which startup entries to enable or disable. The optimizer does not change them automatically. | [Settings URI reference][settings-uri] |
| Show recent system errors | Automatic, diagnostic | Yes | Uses `Get-WinEvent` to display up to 30 System log errors from the previous seven days. It does not clear the log. | [Get-WinEvent][get-winevent] |
| Task Manager | Windows UI | No | Opens `taskmgr.exe` for process, performance, service, and startup inspection. | [Task Manager help][task-manager] |
| Resource Monitor | Windows UI | No | Opens `resmon.exe` for CPU, memory, disk, and network activity. | [Resource Monitor][resource-monitor] |
| Reliability Monitor | Windows UI | No | Opens `perfmon /rel` for the Windows reliability timeline. | [Reliability Monitor][reliability-monitor] |
| Event Viewer | Windows UI | No | Opens `eventvwr.exe` for Windows event logs. | [Event Viewer][event-viewer] |
| System Information | Windows UI | No | Opens `msinfo32.exe` for hardware resources, components, and software environment details. | [System Information][msinfo32] |
| DirectX Diagnostic Tool | Windows UI | No | Opens `dxdiag.exe` for display, audio, input, and DirectX driver information. | [DirectX Diagnostic Tool][dxdiag] |

## Operational model

1. The UI reads action metadata from `maintenance.py`.
2. **Preview selected** renders the same command text used at launch.
3. `launcher.py` shell-activates Settings pages, directly starts native executables, or encodes the selected PowerShell in UTF-16LE for `powershell.exe -EncodedCommand`.
4. Actions marked Admin use the normal Windows `runas` operation and UAC prompt.
5. Selected DISM/SFC servicing commands share one sequential console. Other selected actions launch independently.
6. The app performs no completion polling and stores no task history. Windows owns the command after launch.

## Source index

[checkpoint]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/checkpoint-computer
[chkdsk]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/chkdsk
[cleanmgr]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cleanmgr
[component-cleanup]: https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/clean-up-the-winsxs-folder
[computer-info]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-computerinfo
[defender-cli]: https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus
[defrag]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/defrag
[delivery-cache]: https://learn.microsoft.com/en-us/powershell/module/deliveryoptimization/delete-deliveryoptimizationcache
[dism-repair]: https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/repair-a-windows-image
[drive-optimize-support]: https://support.microsoft.com/en-us/windows/defragment-optimize-your-data-drives-in-windows
[dxdiag]: https://support.microsoft.com/en-au/windows/hardware/display-graphics/which-version-of-directx-is-on-your-pc
[event-viewer]: https://learn.microsoft.com/en-us/shows/inside/event-viewer
[firewall-profile]: https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallprofile
[fsutil-behavior]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-behavior
[get-hotfix]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-hotfix
[get-physical-disk]: https://learn.microsoft.com/en-us/powershell/module/storage/get-physicaldisk
[get-volume]: https://learn.microsoft.com/en-us/powershell/module/storage/get-volume
[get-winevent]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent
[ipconfig]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/ipconfig
[manage-bde]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/manage-bde-status
[memory-diagnostic]: https://support.microsoft.com/en-US/Windows/Experience/Performance-Optimization/how-to-fix-error-0xa-irql-not-less-or-equal
[mp-status]: https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus
[mp-threat]: https://learn.microsoft.com/en-us/powershell/module/defender/get-mpthreatdetection
[msinfo32]: https://support.microsoft.com/en-us/windows/experience/system-configuration-tools-in-windows
[netsh-wlan]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-wlan
[powercfg]: https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options
[recovery-options]: https://support.microsoft.com/en-us/windows/experience/backup-recovery/recovery-options-in-windows
[reliability-monitor]: https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-7/cc722107(v=ws.10)
[resource-monitor]: https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-high-cpu-usage-guidance
[settings-uri]: https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-settings
[sfc]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sfc
[start-mp]: https://learn.microsoft.com/en-us/powershell/module/defender/start-mpscan
[startup-command]: https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-startupcommand
[task-manager]: https://support.microsoft.com/en-us/windows/experience/system-configuration-tools-in-windows
[test-network]: https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection
[update-mp]: https://learn.microsoft.com/en-us/powershell/module/defender/update-mpsignature
[winget-list]: https://learn.microsoft.com/en-us/windows/package-manager/winget/list
[winget-upgrade]: https://learn.microsoft.com/en-us/windows/package-manager/winget/upgrade
[winsock]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-winsock
[wlan-report]: https://support.microsoft.com/en-us/windows/analyzing-the-wireless-network-report
