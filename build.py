"""PyBuilder task that packages the Tkinter app with PyInstaller."""

from pathlib import Path
import subprocess
import sys

from pybuilder.core import task


name = "windows-optimizer"
version = "1.1.0"
default_task = "exe"


@task(description="Build dist/WindowsOptimizer.exe with PyInstaller")
def exe(project, logger):
    root = Path(project.basedir)
    logger.info("Packaging the Tkinter app as a Windows executable")
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onefile", "--windowed",
            "--name", "WindowsOptimizer",
            "--distpath", str(root / "dist"),
            "--workpath", str(root / ".build" / "pyinstaller"),
            "--specpath", str(root / ".build"),
            str(root / "windows_optimizer.pyw"),
        ],
        cwd=root,
        check=True,
    )
