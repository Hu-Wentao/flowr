#!/usr/bin/env python3
"""Regression tests for deterministic BFF archive packaging."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
PACKAGER = SCRIPTS / "package_bff.py"


class PackageBffTest(unittest.TestCase):
    def run_packager(
        self, root: Path, *extra: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(PACKAGER),
                "--project-root",
                str(root),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_contract(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_collects_contracts_with_project_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_contract(root, "lib/app/orders/orders.bff.md", "orders\n")
            self.write_contract(
                root,
                "packages/account/lib/profile/profile.bff.md",
                "profile\n",
            )
            self.write_contract(root, "build/ignored.bff.md", "ignored\n")
            self.write_contract(
                root,
                "packages/account/.dart_tool/ignored.bff.md",
                "ignored\n",
            )

            result = self.run_packager(root)
            archive_path = root / "build/bff-contracts.zip"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("contracts: 2", result.stdout)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [
                        "lib/app/orders/orders.bff.md",
                        "packages/account/lib/profile/profile.bff.md",
                    ],
                )
                self.assertEqual(
                    archive.read("lib/app/orders/orders.bff.md"), b"orders\n"
                )

    def test_archive_is_reproducible_and_supports_project_excludes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_contract(root, "lib/a/a.bff.md", "a\n")
            self.write_contract(root, "examples/demo/demo.bff.md", "demo\n")
            command = ("--exclude", "examples/**")

            first = self.run_packager(root, *command)
            first_bytes = (root / "build/bff-contracts.zip").read_bytes()
            second = self.run_packager(root, *command)
            second_bytes = (root / "build/bff-contracts.zip").read_bytes()

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first_bytes, second_bytes)
            with zipfile.ZipFile(root / "build/bff-contracts.zip") as archive:
                self.assertEqual(archive.namelist(), ["lib/a/a.bff.md"])

    def test_empty_project_fails_without_replacing_existing_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "build/bff-contracts.zip"
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b"known-good")

            result = self.run_packager(root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("no *.bff.md", result.stderr)
            self.assertEqual(archive.read_bytes(), b"known-good")

    def test_symlinked_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = self.write_contract(root, "source/real.bff.md", "real\n")
            link = root / "lib/linked.bff.md"
            link.parent.mkdir(parents=True)
            try:
                link.symlink_to(target)
            except OSError as error:  # pragma: no cover - platform permission
                self.skipTest(f"symlinks unavailable: {error}")

            result = self.run_packager(root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("symlinked BFF contract", result.stderr)

    def test_output_must_be_a_zip_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_contract(root, "lib/a.bff.md", "a\n")

            result = self.run_packager(root, "--output", "build/contracts.tar")

            self.assertEqual(result.returncode, 2)
            self.assertIn("must use the .zip suffix", result.stderr)
            self.assertFalse((root / "build/contracts.tar").exists())


if __name__ == "__main__":
    unittest.main()
