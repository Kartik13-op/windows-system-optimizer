# Windows Performance Optimizer

I built this lightweight, transparent Windows 10/11 system tuning utility to safely optimize performance without installing background bloatware or running persistent "booster" services.

Unlike third-party optimization tools that consume system resources in the background or apply snake-oil registry tweaks, this script uses evidence-based native configurations, creates complete backups, and is fully reversible.

## What It Does

- **Power Management:** Automatically selects the High Performance power plan and optimizes idle sleep timeouts.
- **Visual & UI Responsiveness:** Reduces compositor overhead by disabling non-essential transparency and visual effects.
- **Gaming & Multimedia:** Tunes Multimedia SystemProfile foreground responsiveness and task scheduling priority hints.
- **Network Stack:** Configures TCP receive-window autotuning to Normal, enables Receive Side Scaling (RSS), and disables deprecated NetDMA.
- **Storage & NTFS:** Verifies and enables TRIM, runs system volume retrim, disables legacy 8.3 DOS filename generation, and reclaims space via safe Windows volume compaction.
- **Input Latency:** Optimizes keyboard data queue size and input delay.
- **Safe Cleanup:** Cleans user temporary files, Windows Update cache, and Delivery Optimization cache.

## What It Intentionally DOES NOT Touch

- Windows Defender and core security features
- Windows Update and essential operating system services
- Pagefile sizing (left to Windows dynamic management)
- HPET, timers, MTU, DNS, or random network latency hacks
- CPU parking, core affinity, or aggressive thermal controls

---

## Safety & Data Loss Guarantee

Your data and system stability are the top priorities:
- **Automatic Registry Backups:** Before making any change, the script exports every registry key it touches into a local backup folder (`C:\ProgramData\WindowsOptimizer`).
- **System Restore Point:** Automatically attempts to create a Windows System Restore point before applying modifications.
- **Zero Data Loss:** The script never deletes personal files, documents, photos, or app data. File cleanup is restricted strictly to standard temporary directories (`%TEMP%`, `C:\Windows\Temp`, and Delivery Optimization cache).
- **Fully Reversible:** You can restore your previous system state at any time with a single command.

---

## Installation & Running Guide (For Beginners)

You do not need any technical knowledge to run this utility. Just follow these 4 simple steps:

### Step 1: Download
Download `Windows-Performance-Optimizer.ps1` and save it to your computer (e.g., Desktop, Downloads, or any folder).

### Step 2: Right-Click and Run with PowerShell
Locate the downloaded file, right-click on it, and select **"Run with PowerShell"**.

### Step 3: Tap Yes If Prompts Appear
If any permission prompts appear on your screen, click **"Yes"** to allow the script to run with administrator privileges.

### Step 4: Wait
The script will now run automatically. Just wait for it to complete—it will optimize your system, create backups, and apply all performance improvements. Once finished, your system is ready!

---

## Advanced Usage & Commands

### Report Mode (Analyze without making changes)
If you want to inspect your current system configuration and performance state without applying any modifications:
```powershell
powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -Report
```

### Restore Mode (Revert all changes)
If you ever want to revert your system back to its original state using the automatic backup:
```powershell
powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -Restore
```

### Dry Run / WhatIf Mode
To preview what actions the script would take:
```powershell
powershell -ExecutionPolicy Bypass -File .\Windows-Performance-Optimizer.ps1 -WhatIf
```

---

## Logs and Backups
All action logs and registry backups are safely stored locally at:
`C:\ProgramData\WindowsOptimizer\`
