# Windows Optimizer V1

Release line: **v1.1.0**  
Release date: **2026-10-26**  
Platform: **Windows 10 and Windows 11**

Windows Optimizer V1 is the first production-oriented Tkinter release of the project. It replaces the original single-pass PowerShell optimizer with an inspectable desktop dashboard built around documented Windows maintenance and diagnostic facilities.

## Highlights

- 60 actions organized into 10 categories.
- 45 actions start documented commands directly; the remaining actions open specific Windows controls.
- Fast Optimize, Deep Cleaning, Fast Security check, Deep Security check, System Repair, Storage & Disks, Network Tools, Power & Battery, Apps & Updates, and Diagnostics views.
- Per-action Run/Open buttons, multi-selection, conservative presets, filtering, and exact command previews.
- Normal UAC prompts for administrator actions and visible PowerShell output.
- Direct Defender signature updates, quick/full scans, status, threat history, and scan cancellation.
- DISM/SFC servicing batches run sequentially to avoid competing repairs.
- Media-appropriate drive optimization, component cleanup, online filesystem scanning, disk health, TRIM status, and volume reporting.
- Network, Wi-Fi, battery, energy, sleep, wake, event, startup, and system diagnostics.
- WinGet update discovery and optional `upgrade --all` with normal agreement/installer prompts preserved.

## Safety and transparency

- No background service, startup entry, scheduled task, telemetry, account, or self-updater.
- No Defender/firewall/Windows Update disabling.
- No undocumented timer, HPET, MTU, DNS-server, CPU parking, pagefile, or blanket service tweaks.
- No automatic restart, forced WinGet agreements, Defender remediation choice, or CHKDSK repair scheduling.
- Temp cleanup is limited to files older than seven days under the resolved Temp roots, preserves directories and recent files, and skips reparse points.
- The app does not poll Windows tasks or report them complete merely because they launched.
- Every action and primary reference is documented in [`docs/ACTIONS.md`](../ACTIONS.md).

## Build and verification

The Windows build pipeline:

1. Creates an isolated `.venv-build` environment.
2. Installs pinned PyBuilder and PyInstaller versions.
3. Runs the regression suite.
4. Uses the PyBuilder `exe` task to call PyInstaller.
5. Produces a single-file windowed `WindowsOptimizer.exe` under `dist/`.

The tests validate catalog integrity, Windows PowerShell parsing for every automatic command, cleanup boundaries, native and Settings launch routing, UAC cancellation, frozen-runtime DLL handling, category presets, filtering, conflicts, and sequential servicing.

Release publishers should attach the CI-built executable and publish its SHA-256 checksum. The executable is not currently code-signed; users who need stronger provenance should build from the tagged source.

## Requirements and limitations

- Windows 10 or Windows 11.
- Some actions vary by Windows edition, filesystem, hardware, organization policy, installed antivirus, and available inbox tools.
- Defender automation requires Microsoft Defender Antivirus to be active.
- WinGet automation requires Windows Package Manager.
- DISM, SFC, drive optimization, energy analysis, and full antivirus scans may take a long time.
- Closing the GUI does not stop work already handed to Windows.
- The project cannot guarantee a performance improvement or repair hardware and third-party software failures.

## Upgrade notes

The V1 Tkinter app does not reuse the old PowerShell optimizer's automatic registry/network modifications. Review any legacy backups separately. Running V1 applies only the actions explicitly selected in the dashboard.

## Release checklist

- [ ] Run `python -m unittest discover -s tests -v` on Windows.
- [ ] Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1`.
- [ ] Confirm the packaged GUI starts without running a maintenance action.
- [ ] Calculate and publish the SHA-256 checksum.
- [ ] Review the PyInstaller warnings file.
- [ ] Attach `WindowsOptimizer.exe` to the GitHub release.
- [ ] Confirm README, changelog, action reference, security policy, and known limitations match the tag.
