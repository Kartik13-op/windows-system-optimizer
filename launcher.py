"""Visible Windows tool and command launching; no maintenance-result monitoring."""

import base64
import ctypes
import os
from pathlib import Path
import subprocess
import sys

from maintenance import ACTIONS


WINDOWS = Path(os.environ.get("SystemRoot", r"C:\Windows"))
SYSTEM = WINDOWS / ("Sysnative" if os.environ.get("PROCESSOR_ARCHITEW6432") else "System32")
POWERSHELL = SYSTEM / "WindowsPowerShell" / "v1.0" / "powershell.exe"


def quote_ps(text):
    return "'" + text.replace("'", "''") + "'"


def command_script(action_ids):
    actions = [ACTIONS[action_id] for action_id in action_ids]
    lines = [
        "$ErrorActionPreference = 'Continue'",
        "$ProgressPreference = 'Continue'",
        "$Host.UI.RawUI.WindowTitle = " + quote_ps("Windows Optimizer - " + actions[0].title),
        "Write-Host 'Output stays visible. Ctrl+C stops this console command; close the window when you are done.' -ForegroundColor Cyan",
        "Write-Host 'For Defender scans, use Cancel scan in the app or Windows Security; scans can outlive their console.' -ForegroundColor Yellow",
    ]
    for action in actions:
        lines += ["Write-Host " + quote_ps("\n--- " + action.title + " ---") + " -ForegroundColor Cyan", action.script]
    return "\n".join(lines)


def launch_process(executable, arguments=(), admin=False, console=False):
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    try:
        if admin:
            params = subprocess.list2cmdline(list(arguments))
            os.startfile(str(executable), "runas", arguments=params, show_cmd=1)
        else:
            flags = subprocess.CREATE_NEW_CONSOLE if console else 0
            try:
                subprocess.Popen([str(executable), *arguments], creationflags=flags)
            except OSError as error:
                if getattr(error, "winerror", None) != 740:
                    raise
                os.startfile(str(executable), "runas", arguments=subprocess.list2cmdline(list(arguments)), show_cmd=1)
    finally:
        if bundle:
            ctypes.windll.kernel32.SetDllDirectoryW(str(bundle))


def launch_commands(action_ids):
    if not action_ids or any(not ACTIONS[key].script for key in action_ids):
        raise ValueError("Choose at least one command action.")
    script = command_script(action_ids)
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    launch_process(
        POWERSHELL,
        ("-NoLogo", "-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded),
        admin=any(ACTIONS[key].admin for key in action_ids),
        console=True,
    )


def launch_action(action_id):
    action = ACTIONS[action_id]
    if action.script:
        launch_commands([action_id])
    elif action.target.startswith("ms-settings:"):
        launch_process(WINDOWS / "explorer.exe", (action.target,))
    else:
        launch_process(SYSTEM / action.target, action.arguments, admin=action.admin)
