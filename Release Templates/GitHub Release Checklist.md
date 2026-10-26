# Local GitHub Release Checklist

This local drafting folder is ignored by Git. Canonical, reviewable release notes belong under `docs/releases/`.

- Copy the canonical release notes into the GitHub release description.
- Build from a clean tagged checkout on Windows.
- Use the CI artifact or document why a local artifact is used.
- Calculate `Get-FileHash .\WindowsOptimizer.exe -Algorithm SHA256`.
- Add the exact checksum to the release description.
- Confirm the tag matches `build.py`.
- Attach only reviewed release assets.
- Test the downloaded asset on a supported Windows machine.
