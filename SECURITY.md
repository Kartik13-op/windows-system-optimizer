# Security Policy

Windows Optimizer launches maintenance commands with the current user's authority and, for marked actions, the normal Windows UAC elevation flow. A security issue can therefore have meaningful local impact. Please report suspected vulnerabilities privately.

## Supported versions

| Version | Security updates |
| --- | --- |
| 1.x | Supported |
| Earlier PowerShell prototypes | Unsupported |

Only artifacts attached to this repository's GitHub Releases page and source built from the current default branch are considered project distributions.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/Kartik13-op/windows-system-optimizer/security/advisories/new). Do not include a proof of concept, machine logs, usernames, paths containing personal information, or other sensitive data in a public issue.

Include:

- A concise description and the affected version or commit.
- The Windows edition/build and whether the packaged executable or source was used.
- Reproduction steps that avoid unrelated user data.
- Expected impact, required privileges, and whether user interaction is required.
- Any proposed fix or relevant Microsoft documentation.

The maintainer will acknowledge reports on a best-effort basis. This project does not promise a fixed response SLA. Valid reports will be investigated before public disclosure, and reporters will be credited when requested.

## Issues considered security-sensitive

- Command or argument injection from application-controlled data.
- Cleanup escaping the documented Temp roots or following reparse points.
- Elevation that bypasses, obscures, or misrepresents the Windows UAC boundary.
- An executable artifact that does not correspond to the published source/build process.
- Unexpected persistence, telemetry, credential access, or transmission of local data.
- A preview that materially differs from the command launched for an action.

Windows defects, expected UAC prompts, documented behavior of Microsoft tools, detections made by Defender, and prompts from third-party WinGet installers are normally outside this project's vulnerability scope unless Windows Optimizer changes their security boundary.

## Artifact verification

Release publishers should provide a SHA-256 checksum beside each executable. Users can calculate it with:

```powershell
Get-FileHash .\WindowsOptimizer.exe -Algorithm SHA256
```

The project is not currently code-signed. Building from source is the strongest available verification method until a signing process is established.
