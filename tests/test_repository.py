"""Repository-level checks for documentation and GitHub project metadata."""

from pathlib import Path
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_all_inline_relative_markdown_links_resolve(self):
        failures = []
        for document in ROOT.rglob("*.md"):
            if any(part.startswith(".") for part in document.relative_to(ROOT).parts):
                continue
            text = document.read_text(encoding="utf-8")
            for raw_target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
                target = raw_target.split("#", 1)[0].strip()
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / unquote(target)).resolve()
                if not resolved.exists():
                    failures.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(failures, [])

    def test_readme_embeds_the_checked_in_png(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("![Windows Optimizer maintenance dashboard](./image.png)", readme)
        self.assertEqual((ROOT / "image.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_action_reference_covers_every_catalog_title(self):
        from maintenance import ACTIONS

        reference = (ROOT / "docs" / "ACTIONS.md").read_text(encoding="utf-8")
        missing = [action.title for action in ACTIONS.values() if action.title not in reference]
        self.assertEqual(missing, [])


class RepositoryMetadataTests(unittest.TestCase):
    def test_expected_community_and_github_files_exist(self):
        expected = (
            "SECURITY.md",
            "CONTRIBUTING.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "docs/ACTIONS.md",
            "docs/releases/Windows Optimizer V1.md",
            ".github/CODEOWNERS",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/dependabot.yml",
            ".github/release.yml",
            ".github/workflows/ci.yml",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/action_proposal.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
        )
        self.assertEqual([name for name in expected if not (ROOT / name).is_file()], [])

    def test_local_release_template_workspace_is_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("/Release Templates/", ignore)
        self.assertTrue((ROOT / "Release Templates").is_dir())


if __name__ == "__main__":
    unittest.main()
