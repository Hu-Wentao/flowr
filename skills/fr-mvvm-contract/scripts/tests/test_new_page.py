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
    def test_minimal_spec_uses_default_generation_values(self) -> None:
        page = new_page.parse_page(
            {
                "name": "minimal_page",
                "figmaUrl": "https://www.figma.com/file/example/minimal-page",
                "api": "NONE",
            }
        )
        models = new_page.parse_models(None, page["primary_model_name"])
        events = new_page.parse_events(None, page["event_base_name"])
        view_model = new_page.parse_view_model(
            None,
            page["primary_vm_name"],
            page["primary_model_name"],
        )
        view = new_page.parse_view(None, page["entry_widget_name"])

        contract = new_page.render_contract_file(page, models, events, view_model)
        view_file = new_page.render_view_file(page, view)
        vm_file = new_page.render_vm_file(page, events, view_model)

        self.assertIn("class MinimalPage extends StatelessWidget", contract)
        self.assertIn("@FrState", contract)
        self.assertIn("const factory MinimalPageModel() = _MinimalPageModel;", contract)
        self.assertIn("MinimalPageStarted", vm_file)
        self.assertIn("return const SizedBox.shrink();", view_file)

    def test_contract_overrides_customize_generated_contract(self) -> None:
        page = new_page.parse_page(
            {
                "name": "adapted_page",
                "figmaUrl": "https://www.figma.com/file/example/adapted-page",
                "api": "BFF-JSON",
                "apiContract": ["GET <BASE>/detail\n[AdaptedDetailReq], [AdaptedDetailModel]"],
                "state_ownership": "none",
                "widget_tree": ["[AdaptedPage]"],
                "contract": {
                    "sectionOrder": [
                        "figma",
                        "bff_api",
                        "state_ownership",
                        "route",
                        "reused_widgets",
                        "widget_tree",
                        "theme",
                        "events",
                        "view_models",
                        "models",
                        "notes",
                    ],
                    "sections": [
                        {
                            "id": "bff_api",
                            "label": "API refs",
                            "style": "list",
                            "lines": [
                                "- api: detail",
                                "request:",
                                "- locale: 当前语言。",
                                "response:",
                                "- title: 标题。",
                            ],
                        },
                        {
                            "id": "notes",
                            "label": "Notes",
                            "style": "list",
                            "lines": ["- breaking behavior is explicit."],
                        },
                    ],
                    "rootAnnotations": ["@DemoRoot()"],
                    "extraDeclarations": ["enum AdaptedTab { detail }"],
                },
            }
        )
        models = new_page.parse_models(
            [
                {
                    "name": "AdaptedPageModel",
                    "description": "primary page state",
                    "fields": [],
                },
                {
                    "name": "AdaptedDetailModel",
                    "description": "backend DTO",
                    "annotations": ["@DemoDto()", "@FrAcddFreezedJSON"],
                    "fromJson": True,
                    "fields": [
                        {
                            "name": "title",
                            "type": "String",
                            "default": "''",
                            "annotation": "@DemoField()",
                        }
                    ],
                },
            ],
            page["primary_model_name"],
        )
        events = new_page.parse_events(None, page["event_base_name"])
        view_model = new_page.parse_view_model(
            None,
            page["primary_vm_name"],
            page["primary_model_name"],
        )
        contract = new_page.render_contract_file(page, models, events, view_model)

        self.assertIn("/// API refs:", contract)
        self.assertIn("/// - request:", contract)
        self.assertIn("@DemoRoot()", contract)
        self.assertIn("enum AdaptedTab { detail }", contract)
        self.assertIn("@DemoDto()", contract)
        self.assertIn("@DemoField()", contract)
        self.assertIn("factory AdaptedDetailModel.fromJson", contract)
        self.assertIn("/// Notes:", contract)

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

    def test_parse_models_rejects_model_members(self) -> None:
        page = build_page(None)

        with self.assertRaisesRegex(
            new_page.SpecError,
            r"models\[0\]\.members is not supported; move model helper methods",
        ):
            new_page.parse_models(
                [
                    {
                        "name": "DemoPageModel",
                        "description": "primary page state",
                        "fields": [],
                        "members": ["String get label => 'demo';"],
                    }
                ],
                page["primary_model_name"],
            )

    def test_parse_view_rejects_widget_members(self) -> None:
        page = build_page(None)

        with self.assertRaisesRegex(
            new_page.SpecError,
            r"view\.widgets\[0\]\.members is not supported; move view helper methods",
        ):
            new_page.parse_view(
                {
                    "entry": {
                        "build": "return const SizedBox.shrink();",
                    },
                    "widgets": [
                        {
                            "name": "DemoBody",
                            "fields": [],
                            "members": ["String _label() => 'demo';"],
                            "build": "return const SizedBox.shrink();",
                        }
                    ],
                },
                page["entry_widget_name"],
            )


if __name__ == "__main__":
    unittest.main()
