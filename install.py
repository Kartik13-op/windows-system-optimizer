"""Replace the old optimizer in the user's original project folder."""

from pathlib import Path
import shutil


SOURCE = Path(__file__).resolve().parent
TARGET = Path(r"D:\Kartik\windows-optimizer")
APP_FILES = (
    "windows_optimizer.pyw", "Start.cmd", "README.md", ".gitignore",
    "build.ps1", "build.py", "requirements-build.txt", "tests/test_app.py",
    "tests/test_repository.py",
    "maintenance.py", "launcher.py", "image.png", ".gitattributes", ".editorconfig",
    "SECURITY.md", "CONTRIBUTING.md", "SUPPORT.md", "CHANGELOG.md",
    "CODE_OF_CONDUCT.md", "docs/ACTIONS.md",
    "docs/releases/Windows Optimizer V1.md",
    ".github/CODEOWNERS", ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/dependabot.yml", ".github/release.yml", ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/action_proposal.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    "Release Templates/GitHub Release Checklist.md",
)
LEGACY_FILES = (
    "Windows-Performance-Optimizer.ps1",
    "Windows-Maintenance-Menu.ps1",
    "Start-Windows-Maintenance.cmd",
    "Windows-Maintenance-Menu.zip",
    "START-HERE.txt",
    "_verify-menu.ps1",
)


def install():
    TARGET.mkdir(parents=True, exist_ok=True)
    # Copy the replacement first. Leave .git and unrelated files alone.
    if SOURCE != TARGET:
        for name in APP_FILES:
            (TARGET / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, TARGET / name)
        executable = SOURCE / "dist" / "WindowsOptimizer.exe"
        if executable.is_file():
            (TARGET / "dist").mkdir(exist_ok=True)
            shutil.copyfile(executable, TARGET / "dist" / executable.name)
    for name in LEGACY_FILES:
        (TARGET / name).unlink(missing_ok=True)
    print(f"Installed the Tkinter app in {TARGET}")
    print("Open Start.cmd in that folder to run it.")


if __name__ == "__main__":
    try:
        install()
    except OSError as error:
        print(f"Installation failed: {error}")
        raise SystemExit(1)
