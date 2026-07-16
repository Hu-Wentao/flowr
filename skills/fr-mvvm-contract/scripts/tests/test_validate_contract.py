#!/usr/bin/env python3
"""Regression tests for generated JSON contract validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
VALIDATOR = SCRIPTS / "validate_contract.py"


class ValidateContractTest(unittest.TestCase):
    def write_fixture(
        self,
        root: Path,
        *,
        annotation: str = "FrState",
        include_g_part: bool = True,
        include_json_serializable: bool = True,
        handwritten_suffix: str | None = None,
        handwritten_body: str = (
            "Map<String, dynamic> _$OrderContentModelToJson(\n"
            "  OrderContentModel instance,\n"
            ") => <String, dynamic>{};\n"
        ),
    ) -> Path:
        dev_dependencies = (
            "  json_serializable: any\n" if include_json_serializable else ""
        )
        (root / "pubspec.yaml").write_text(
            "name: validator_fixture\n"
            "environment:\n"
            "  sdk: ^3.7.0\n"
            "dev_dependencies:\n"
            f"{dev_dependencies}",
            encoding="utf-8",
        )
        source_dir = root / "lib/order_content"
        source_dir.mkdir(parents=True)
        component = source_dir / "order_content.dart"
        g_part = "part 'order_content.g.dart';\n" if include_g_part else ""
        component.write_text(
            "part 'order_content.c.dart';\n"
            "part 'order_content.v.dart';\n"
            "part 'order_content.vm.dart';\n"
            "part 'order_content.freezed.dart';\n"
            f"{g_part}",
            encoding="utf-8",
        )
        (source_dir / "order_content.c.dart").write_text(
            "part of 'order_content.dart';\n\n"
            "/// Events: [OrderContentStarted]\n"
            "/// ViewModels: [OrderContentViewModel]\n"
            "/// Models: [OrderContentModel]\n"
            "class OrderContentView {\n"
            "  Object build() => FrProvider;\n"
            "}\n\n"
            f"@{annotation}\n"
            "class OrderContentModel {}\n",
            encoding="utf-8",
        )
        for suffix in ("v", "vm"):
            body = handwritten_body if handwritten_suffix == suffix else ""
            (source_dir / f"order_content.{suffix}.dart").write_text(
                "part of 'order_content.dart';\n" + body,
                encoding="utf-8",
            )
        if handwritten_suffix in {"c", "srv"}:
            target = source_dir / f"order_content.{handwritten_suffix}.dart"
            if handwritten_suffix == "c":
                target.write_text(
                    target.read_text(encoding="utf-8") + handwritten_body,
                    encoding="utf-8",
                )
            else:
                target.write_text(
                    "part of 'order_content.dart';\n" + handwritten_body,
                    encoding="utf-8",
                )
        return component

    def validate(self, component: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--component-file", str(component)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fr_state_contract_with_g_part_and_dependency_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(self.write_fixture(Path(temporary)))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fr_state_and_fr_state_json_require_g_part(self) -> None:
        for annotation in ("FrState", "FrStateJson"):
            with self.subTest(annotation=annotation):
                with tempfile.TemporaryDirectory() as temporary:
                    result = self.validate(
                        self.write_fixture(
                            Path(temporary),
                            annotation=annotation,
                            include_g_part=False,
                        )
                    )

                self.assertEqual(result.returncode, 2)
                self.assertIn("order_content.g.dart", result.stderr)
                self.assertIn("build_runner", result.stderr)

    def test_fr_state_requires_direct_json_serializable_dev_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), include_json_serializable=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("json_serializable", result.stderr)
        self.assertIn("dev_dependencies", result.stderr)
        self.assertIn("build_runner", result.stderr)

    def test_runtime_dependency_does_not_satisfy_direct_dev_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root, include_json_serializable=False)
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text(encoding="utf-8")
                + "dependencies:\n  json_serializable: any\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("dev_dependencies", result.stderr)

    def test_source_parts_must_not_define_generated_json_functions(self) -> None:
        bodies = {
            "ToJson": (
                "Map<String, dynamic> _$OrderContentModelToJson(\n"
                "  OrderContentModel instance,\n"
                ") => <String, dynamic>{};\n"
            ),
            "FromJson": (
                "OrderContentModel _$OrderContentModelFromJson(\n"
                "  Map<String, dynamic> json,\n"
                ") { return OrderContentModel(); }\n"
            ),
        }
        for suffix in ("c", "v", "vm", "srv"):
            for function_kind, body in bodies.items():
                with self.subTest(suffix=suffix, function_kind=function_kind):
                    with tempfile.TemporaryDirectory() as temporary:
                        result = self.validate(
                            self.write_fixture(
                                Path(temporary),
                                handwritten_suffix=suffix,
                                handwritten_body=body,
                            )
                        )

                    self.assertEqual(result.returncode, 2)
                    self.assertIn(f"order_content.{suffix}.dart", result.stderr)
                    self.assertIn(".g.dart", result.stderr)
                    self.assertIn("build_runner", result.stderr)
                    self.assertIn("must not be handwritten", result.stderr)

    def test_generated_json_function_call_is_not_mistaken_for_definition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            vm = component.with_name("order_content.vm.dart")
            vm.write_text(
                vm.read_text(encoding="utf-8")
                + "Map<String, dynamic> snapshot(OrderContentModel value) "
                "=> _$OrderContentModelToJson(value);\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
