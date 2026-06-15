import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "new_page.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "fr_mvvm_contract_new_page",
    SCRIPT_PATH,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
new_page = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(new_page)


def build_page(theme: dict[str, object] | None) -> dict[str, object]:
    return new_page.parse_page(
        {
            "name": "demo_page",
            "figmaUrl": "https://www.figma.com/file/example/demo-page",
            "api": "NONE",
            "state_ownership": [
                "[DemoPageViewModel]: page-private, owns [DemoPageModel]"
            ],
            "widget_tree": ["[DemoPageScaffold]"],
            "theme": theme,
        }
    )


def build_contract(
    theme: dict[str, object] | None,
    *,
    model_preset: str = "state",
) -> str:
    page = build_page(theme)
    models = new_page.parse_models(
        [
            {
                "name": "DemoPageModel",
                "description": "primary page state",
                "preset": model_preset,
                "fields": [],
            }
        ],
        page["primary_model_name"],
    )
    events = new_page.parse_events(
        [
            {
                "name": "DemoPageStarted",
                "description": "bootstrap the page",
            }
        ],
        page["event_base_name"],
    )
    view_model = new_page.parse_view_model(
        {
            "description": "primary page view model",
            "event_handlers": [],
        },
        page["primary_vm_name"],
        page["primary_model_name"],
    )
    return new_page.render_contract_file(page, models, events, view_model)


class NewPageThemeTests(unittest.TestCase):
    def test_parse_theme_preserves_declaration(self) -> None:
        page = build_page(
            {
                "declaration": "\n@JsonSerializable()\n",
                "fields": [
                    {
                        "name": "seedColor",
                        "type": "Color",
                    }
                ],
            }
        )

        self.assertEqual(page["theme"]["declaration"], "@JsonSerializable()")

    def test_render_contract_includes_generated_part_for_json_theme(self) -> None:
        contract = build_contract(
            {
                "declaration": "@JsonSerializable()",
                "fields": [
                    {
                        "name": "seedColor",
                        "type": "Color",
                    }
                ],
                "members": [
                    "factory DemoPageTheme.fromJson(Map<String, dynamic> json) => _$DemoPageThemeFromJson(json);",
                    "Map<String, dynamic> toJson() => _$DemoPageThemeToJson(this);",
                ],
            },
            model_preset="plain",
        )

        self.assertIn("part 'demo_page.g.dart';", contract)
        self.assertIn("@JsonSerializable()", contract)
        self.assertIn(
            "factory DemoPageTheme.fromJson(Map<String, dynamic> json)",
            contract,
        )
        self.assertIn(
            "Map<String, dynamic> toJson() => _$DemoPageThemeToJson(this);",
            contract,
        )

    def test_render_contract_includes_generated_part_for_theme_json_members(self) -> None:
        contract = build_contract(
            {
                "fields": [
                    {
                        "name": "seedColor",
                        "type": "Color",
                    }
                ],
                "members": [
                    "factory DemoPageTheme.fromJson(Map<String, dynamic> json) => _$DemoPageThemeFromJson(json);",
                ],
            },
            model_preset="plain",
        )

        self.assertIn("part 'demo_page.g.dart';", contract)

    def test_render_contract_skips_generated_part_for_plain_theme(self) -> None:
        contract = build_contract(
            {
                "fields": [
                    {
                        "name": "seedColor",
                        "type": "Color",
                    }
                ],
            },
            model_preset="plain",
        )

        self.assertNotIn("part 'demo_page.g.dart';", contract)

    def test_render_contract_uses_fr_state_by_default(self) -> None:
        contract = build_contract(None)

        self.assertIn("part 'demo_page.g.dart';", contract)
        self.assertIn("@FrState", contract)
        self.assertNotIn("const FrState = Freezed(", contract)
        self.assertNotIn(
            "factory DemoPageModel.fromJson(Map<String, dynamic> json) => _$DemoPageModelFromJson(json);",
            contract,
        )

    def test_render_contract_supports_restorable_state_preset(self) -> None:
        contract = build_contract(None, model_preset="state_json")

        self.assertIn("part 'demo_page.g.dart';", contract)
        self.assertIn("@FrStateJson", contract)
        self.assertIn(
            "factory DemoPageModel.fromJson(Map<String, dynamic> json) => _$DemoPageModelFromJson(json);",
            contract,
        )

    def test_render_contract_allows_plain_model_opt_out(self) -> None:
        contract = build_contract(None, model_preset="plain")

        self.assertNotIn("@FrState", contract)
        self.assertNotIn("@FrStateJson", contract)
        self.assertNotIn("part 'demo_page.g.dart';", contract)
        self.assertIn("@Freezed(", contract)
        self.assertIn("  toJson: false,", contract)


if __name__ == "__main__":
    unittest.main()
