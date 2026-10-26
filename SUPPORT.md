# Support

## Before opening an issue

1. Confirm you are running Windows 10 or 11.
2. Note whether you used the release executable or `python windows_optimizer.pyw`.
3. Use **Preview selected** and record the action name, without including personal paths or machine-identifying output.
4. Try the corresponding Windows tool from Start. If Windows itself cannot open or run it, the problem may be with Windows, policy, or an organization-managed device.
5. Check existing issues before creating a new one.

Use the [bug report form](https://github.com/Kartik13-op/windows-system-optimizer/issues/new?template=bug_report.yml) for reproducible application defects and the action proposal form for new Windows-supported maintenance ideas.

## Common situations

### Windows shows a UAC prompt

The selected action is marked as requiring administrator privileges. Choose **No** to cancel it. The app does not bypass UAC.

### SmartScreen warns about the executable

The project does not currently publish a code-signed executable. Verify the artifact came from this repository, compare its SHA-256 checksum with the release description, or build it from source.

### Defender actions are unavailable

Microsoft Defender Antivirus may be disabled by organization policy or replaced by another security provider. Use the controls provided by the active security product.

### WinGet is unavailable or prompts for agreements

Windows Package Manager must be installed and registered for the current user. Windows Optimizer deliberately does not force source/package agreement acceptance. Follow the visible WinGet prompt or cancel the console.

### A long-running command appears stuck

DISM, SFC, CHKDSK scans, Defender full scans, drive optimization, and energy reports can remain at one percentage for a long time. The optimizer does not estimate progress. Read the Windows output before interrupting it. For Defender, use **Cancel Defender scan**; for other attached console commands, Ctrl+C requests interruption.

### Closing the optimizer did not stop maintenance

The GUI hands commands to Windows and does not own their lifetime. This is intentional. Closing the GUI does not terminate tasks already accepted by Windows.

## Privacy when sharing diagnostics

System reports, Event Viewer entries, network configuration, Wi-Fi reports, startup commands, and screenshots can reveal names, paths, IP addresses, hardware identifiers, installed software, and organization details. Redact them before posting publicly.

Suspected vulnerabilities belong in the private process described by [SECURITY.md](./SECURITY.md), not a public support issue.
