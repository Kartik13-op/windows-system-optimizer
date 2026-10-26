"""Regression tests for the action catalog, launch routing, and Tkinter controls."""

import base64
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launcher  # noqa: E402
from maintenance import ACTIONS, CATEGORIES  # noqa: E402

APP = runpy.run_path(str(ROOT / "windows_optimizer.pyw"), run_name="test_app")


class CatalogTests(unittest.TestCase):
    def test_catalog_has_valid_unique_category_references(self):
        self.assertGreaterEqual(len(ACTIONS), 60)
        self.assertGreaterEqual(len(CATEGORIES), 10)
        for category, (_, action_ids, preset) in CATEGORIES.items():
            self.assertEqual(len(action_ids), len(set(action_ids)), category)
            self.assertTrue(set(action_ids) <= set(ACTIONS), category)
            self.assertTrue(set(preset) <= set(action_ids), category)
        for action_id, action in ACTIONS.items():
            self.assertNotEqual(bool(action.script), bool(action.target), action_id)

    def test_commands_do_not_hide_errors_or_progress(self):
        scripts = "\n".join(action.script for action in ACTIONS.values())
        self.assertNotIn("SilentlyContinue", scripts)
        self.assertNotIn("$ProgressPreference = 'SilentlyContinue'", scripts)

    def test_temp_cleanup_is_bounded_and_skips_links_recent_files_and_folders(self):
        script = ACTIONS["user_temp"].script
        self.assertIn("LocalApplicationData", script)
        self.assertIn("AddDays(-7)", script)
        self.assertIn("ReparsePoint", script)
        self.assertIn("$entry -is [IO.DirectoryInfo]", script)
        self.assertNotIn("Remove-Item", script)

    def test_all_automatic_commands_parse_in_windows_powershell(self):
        scripts = "\n".join(action.script for action in ACTIONS.values() if action.script)
        result = subprocess.run(
            [
                str(launcher.POWERSHELL),
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "try{[void][ScriptBlock]::Create([Console]::In.ReadToEnd())}catch{Write-Error $_;exit 1}",
            ],
            input=scripts,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class LauncherTests(unittest.TestCase):
    def test_settings_are_shell_activated_through_explorer(self):
        with mock.patch.object(launcher, "launch_process") as launch:
            launcher.launch_action("security")
            launch.assert_called_once_with(
                launcher.WINDOWS / "explorer.exe", ("ms-settings:windowsdefender",)
            )

    def test_native_tool_uses_system_directory_and_arguments(self):
        with mock.patch.object(launcher, "launch_process") as launch:
            launcher.launch_action("reliability")
            launch.assert_called_once_with(
                launcher.SYSTEM / "perfmon.exe", ("/rel",), admin=False
            )

    def test_admin_command_is_utf16_encoded_and_visible(self):
        with mock.patch.object(launcher, "launch_process") as launch:
            launcher.launch_commands(["dism_check"])
            executable, arguments = launch.call_args.args
            self.assertEqual(executable, launcher.POWERSHELL)
            self.assertTrue(launch.call_args.kwargs["admin"])
            self.assertIn("-NoExit", arguments)
            encoded = arguments[arguments.index("-EncodedCommand") + 1]
            decoded = base64.b64decode(encoded).decode("utf-16le")
            self.assertIn("DISM.exe /Online /Cleanup-Image /CheckHealth", decoded)
            self.assertIn("Ctrl+C stops this console command", decoded)
            self.assertNotIn("SilentlyContinue", decoded)

    def test_non_admin_command_opens_a_new_console(self):
        with mock.patch.object(launcher, "launch_process") as launch:
            launcher.launch_commands(["network_config"])
            self.assertFalse(launch.call_args.kwargs["admin"])
            self.assertTrue(launch.call_args.kwargs["console"])

    def test_uac_cancel_is_not_swallowed(self):
        error = OSError(1223, "User canceled elevation", None, 1223)
        with mock.patch.object(launcher.os, "startfile", side_effect=error):
            with self.assertRaises(OSError):
                launcher.launch_process(launcher.POWERSHELL, ("-NoExit",), admin=True)

    def test_frozen_dll_directory_is_restored_after_failure(self):
        with mock.patch.object(launcher.sys, "_MEIPASS", "test-bundle", create=True):
            with mock.patch.object(
                launcher.ctypes.windll.kernel32, "SetDllDirectoryW"
            ) as dll_dir:
                with mock.patch.object(
                    launcher.subprocess, "Popen", side_effect=OSError(5, "Denied")
                ):
                    with self.assertRaises(OSError):
                        launcher.launch_process(launcher.SYSTEM / "dfrgui.exe")
                self.assertEqual(
                    dll_dir.call_args_list,
                    [mock.call(None), mock.call("test-bundle")],
                )


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.window = APP["create_window"]()
        self.window.withdraw()
        self.app = self.window.app

    def tearDown(self):
        self.window.destroy()

    def test_every_category_renders_and_uses_its_preset(self):
        for name, (_, action_ids, preset) in CATEGORIES.items():
            self.app.selected.set(name)
            self.app.show_category()
            self.assertEqual(self.app.title.cget("text"), name)
            self.assertEqual(self.app.visible_ids, list(action_ids))
            self.assertEqual(self.app.chosen_ids(), list(preset))

    def test_filter_does_not_discard_hidden_selection(self):
        self.app.selected.set("Fast Optimize")
        self.app.show_category()
        original = self.app.chosen_ids()
        self.app.filter_text.set("Resource Monitor")
        self.window.update_idletasks()
        self.assertEqual(self.app.visible_ids, ["resources"])
        self.assertEqual(self.app.chosen_ids(), original)

    def test_individual_action_reports_launch_errors(self):
        error = OSError(2, "Missing")
        launch_mock = mock.Mock(side_effect=error)
        with mock.patch.dict(self.app.run_action.__globals__, {"launch_action": launch_mock}):
            with mock.patch.object(APP["messagebox"], "showerror") as show_error:
                self.app.run_action("system_info")
                show_error.assert_called_once()
                self.assertIn("Could not launch", self.app.status.get())

    def test_servicing_actions_are_grouped_and_other_actions_launch_individually(self):
        self.app.selected.set("System Repair")
        self.app.show_category()
        self.app.clear_selection()
        for key in ("restore_point", "dism_check", "sfc_verify"):
            self.app.checked[key].set(True)
        launch_batch = mock.Mock()
        with mock.patch.dict(
            self.app.run_selected.__globals__, {"launch_commands": launch_batch}
        ):
            with mock.patch.object(self.app, "run_action") as run_action:
                self.app.run_selected()
                launch_batch.assert_called_once_with(["dism_check", "sfc_verify"])
                run_action.assert_called_once_with("restore_point")

    def test_conflicting_power_plans_are_rejected(self):
        self.app.selected.set("Power & Battery")
        self.app.show_category()
        self.app.clear_selection()
        self.app.checked["balanced"].set(True)
        self.app.checked["high_performance"].set(True)
        with mock.patch.object(APP["messagebox"], "showinfo") as show_info:
            with mock.patch.object(self.app, "run_action") as run_action:
                self.app.run_selected()
                show_info.assert_called_once()
                run_action.assert_not_called()


if __name__ == "__main__":
    unittest.main()
