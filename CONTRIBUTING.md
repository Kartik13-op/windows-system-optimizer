# Contributing

Thank you for helping improve Windows Optimizer. The project values transparent, documented Windows maintenance over broad “tweak packs.” Contributions should make behavior easier to inspect, safer to run, or more useful to diagnose.

## Development setup

Requirements:

- Windows 10 or 11.
- Python 3.10 or later with Tkinter.
- PowerShell 5.1 for command compatibility.
- Internet access on the first executable build to install pinned build tools.

Run from source:

```powershell
python .\windows_optimizer.pyw
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Build the executable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

The build runs the tests before PyBuilder invokes PyInstaller. Generated environments, caches, specs, `dist/`, and the local `Release Templates/` workspace must remain uncommitted.

## Proposing a maintenance action

A new action should:

1. Solve a concrete Windows maintenance or diagnostic need.
2. Use a documented Windows command, cmdlet, Settings URI, or inbox executable.
3. Prefer reporting/analysis before mutation when both are useful.
4. State whether it changes configuration, deletes data, installs software, restarts, or requires elevation.
5. Keep prompts and output visible; do not add `SilentlyContinue`, hidden consoles, forced agreement acceptance, or fabricated completion messages.
6. Be represented declaratively in `maintenance.py` and launched through `launcher.py`.
7. Remain previewable through the GUI.
8. Add a primary Microsoft source and an entry to `docs/ACTIONS.md`.
9. Add focused tests for routing, boundaries, conflicts, and command construction.

Actions that disable security, blindly alter services/registry keys, apply undocumented networking/timer tweaks, remove recovery options, or use universal “performance” claims will not be accepted.

## Pull requests

- Keep each pull request focused and explain the user-visible change.
- Describe privilege, data-loss, reboot, privacy, and compatibility implications.
- Include the exact validation performed.
- Update README, action reference, changelog, and release notes when behavior changes.
- Do not commit compiled executables, virtual environments, local reports, user logs, screenshots containing personal data, or release-drafting files.

The pull request template contains the final review checklist. Maintainers may ask for a smaller scope or a safer Windows-supported alternative.

## Code style

- Prefer the Python standard library and native `ttk` controls.
- Keep the action catalog readable and explicit.
- Use active, factual descriptions without marketing claims.
- Preserve visible Windows errors and UAC prompts.
- Keep irreversible behavior out of presets.
- Write tests that verify meaningful safety and launch boundaries rather than restating implementation details.
