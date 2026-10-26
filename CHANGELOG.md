# Changelog

All notable project changes are documented here. Dates use `YYYY-MM-DD`.

## [1.1.0] - 2026-10-26

### Added

- Production Tkinter dashboard with 60 actions across 10 maintenance categories.
- 45 direct commands for cleanup, Defender, repairs, storage, network, power, updates, and diagnostics.
- Conservative presets, filtering, per-action Run/Open controls, multi-selection, and exact command previews.
- Visible elevated PowerShell execution and a dedicated Defender scan cancellation action.
- Sequential grouping for selected DISM and SFC servicing commands.
- Bounded seven-day Temp cleanup that skips directories and reparse points.
- PyBuilder/PyInstaller build pipeline with pinned dependencies and tests before packaging.
- GitHub issue forms, pull request template, CI workflow, security policy, support guide, contribution guide, action reference, and release notes.

### Changed

- Replaced legacy Control Panel Power Options activation with the documented modern Settings URI.
- Replaced direct `windowsdefender:` activation with the documented Windows Security Settings route.
- Expanded regression coverage for catalog integrity, command parsing, launch routing, elevation, cleanup boundaries, filters, presets, conflicts, and servicing batches.

### Removed

- The earlier PowerShell optimizer and automatic registry/network tweak model.
- Hidden/suppressed command output and broad recursive cleanup behavior.

See [Windows Optimizer V1 release notes](./docs/releases/Windows%20Optimizer%20V1.md).

## [0.1.0] - 2026-09-09

- Initial PowerShell prototype.
