#!/usr/bin/env python3
"""Tests for config-aware OpenAPI Retrofit generation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from openapi_to_retrofit import (  # noqa: E402
    BUILD_RUNNER_MARKER,
    MARKER,
    build_wrapper_models,
    generate,
    render_document,
)
from resolve import (
    DartGenericWrapperRule,
    ResolveError,
    dart_generic_wrapper_rules,
)  # noqa: E402


def wrapper_schema(*, fixed_name: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            fixed_name: {"type": "string", "description": "project-owned"},
            "data": payload,
        },
        "required": [fixed_name],
    }


class OpenApiToRetrofitTest(unittest.TestCase):
    def test_renders_multipart_binary_request_as_retrofit_part(self) -> None:
        document = {
            "openapi": "3.0.1",
            "paths": {
                "/app/file/upload": {
                    "post": {
                        "parameters": [
                            {
                                "name": "objectType",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "files": {
                                                "type": "string",
                                                "format": "binary",
                                            },
                                            "caption": {"type": "string"},
                                        },
                                        "required": ["files"],
                                    }
                                }
                            }
                        },
                        "responses": {},
                    }
                }
            },
            "components": {"schemas": {}},
        }

        source = render_document(document, Path("docs/openapi/upload.openapi.json"), ())

        self.assertIn("@MultiPart()", source)
        self.assertIn(
            '@Part(name: "files") MultipartFile files',
            source,
        )
        self.assertIn(
            '@Part(name: "caption") String? caption',
            source,
        )
        self.assertNotIn("@Body()", source)

    def test_preserves_openapi_schema_and_field_names_except_wrappers(self) -> None:
        rules = (
            DartGenericWrapperRule(
                rule_name="request",
                dart_name="ReqWrapper",
                schema_glob="StandardRequest*",
                type_parameter_field="data",
            ),
        )
        document = {
            "openapi": "3.0.1",
            "paths": {
                "/apply": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/StandardRequestTransAuthNoLoginApplyReq"
                                    }
                                }
                            }
                        },
                        "responses": {},
                    }
                }
            },
            "components": {
                "schemas": {
                    "StandardRequestTransAuthNoLoginApplyReq": wrapper_schema(
                        fixed_name="system",
                        payload={
                            "$ref": "#/components/schemas/TransAuthNoLoginApplyReq"
                        },
                    ),
                    "TransAuthNoLoginApplyReq": {
                        "type": "object",
                        "properties": {
                            "loginId": {"type": "string"},
                            "authType": {"type": "string"},
                        },
                    },
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/auth.openapi.json"), rules
        )

        self.assertIn("class TransAuthNoLoginApplyReq", source)
        self.assertIn("final String? loginId;", source)
        self.assertNotIn("username", source)
        self.assertIn(
            "@Body() ReqWrapper<TransAuthNoLoginApplyReq> body",
            source,
        )
        self.assertNotIn(
            "class StandardRequestTransAuthNoLoginApplyReq",
            source,
        )

    def test_required_model_fields_are_non_nullable_constructor_parameters(
        self,
    ) -> None:
        document = {
            "openapi": "3.0.1",
            "paths": {},
            "components": {
                "schemas": {
                    "LoginReq": {
                        "type": "object",
                        "properties": {
                            "loginId": {"type": "string"},
                            "isReinstall": {"type": "string"},
                        },
                        "required": ["loginId"],
                    }
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/login.openapi.json"), ()
        )

        self.assertIn("required this.loginId,", source)
        self.assertIn("this.isReinstall,", source)
        self.assertIn("final String loginId;", source)
        self.assertIn("final String? isReinstall;", source)

    def test_required_wrapper_fields_preserve_requiredness(self) -> None:
        rules = (
            DartGenericWrapperRule(
                rule_name="request",
                dart_name="ReqWrapper",
                schema_glob="StandardRequest*",
                type_parameter_field="data",
            ),
        )
        document = {
            "openapi": "3.0.1",
            "paths": {},
            "components": {
                "schemas": {
                    "StandardRequestLoginReq": {
                        "type": "object",
                        "properties": {
                            "system": {"type": "string"},
                            "data": {"$ref": "#/components/schemas/LoginReq"},
                        },
                        "required": ["data"],
                    },
                    "LoginReq": {
                        "type": "object",
                        "properties": {"loginId": {"type": "string"}},
                        "required": ["loginId"],
                    },
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/login.openapi.json"), rules
        )

        self.assertIn("required this.data,", source)
        self.assertIn("this.system,", source)
        self.assertIn("final T data;", source)
        self.assertIn("final String? system;", source)

    def test_required_fields_are_collected_from_all_of(self) -> None:
        document = {
            "openapi": "3.0.1",
            "paths": {},
            "components": {
                "schemas": {
                    "LoginReq": {
                        "allOf": [
                            {
                                "type": "object",
                                "properties": {"loginId": {"type": "string"}},
                                "required": ["loginId"],
                            },
                            {
                                "type": "object",
                                "properties": {"authType": {"type": "string"}},
                                "required": ["authType"],
                            },
                        ]
                    }
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/login.openapi.json"), ()
        )

        self.assertIn("required this.loginId,", source)
        self.assertIn("required this.authType,", source)
        self.assertIn("final String loginId;", source)
        self.assertIn("final String authType;", source)

    def test_free_form_component_schema_renders_as_map_alias(self) -> None:
        document = {
            "openapi": "3.0.1",
            "paths": {},
            "components": {
                "schemas": {
                    "MapString": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    "Rule": {
                        "type": "object",
                        "properties": {
                            "variables": {
                                "$ref": "#/components/schemas/MapString"
                            }
                        },
                    },
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/rules.openapi.json"), ()
        )

        self.assertIn(
            "typedef MapString = Map<String, String>;",
            source,
        )
        self.assertNotIn("class MapString", source)
        self.assertIn("final MapString? variables;", source)

    def test_directory_generation_detects_and_removes_stale_sdk_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "openapi"
            output = root / "lib/api/gen"
            source.mkdir()
            output.mkdir(parents=True)
            (source / "current.openapi.json").write_text(
                '{"openapi":"3.0.1","paths":{},"components":{"schemas":{}}}',
                encoding="utf-8",
            )
            stale = output / "renamed_api.dart"
            stale_part = output / "renamed_api.g.dart"
            stale.write_text(f"{MARKER}\n", encoding="utf-8")
            stale_part.write_text(
                f"{BUILD_RUNNER_MARKER}\n\npart of 'renamed_api.dart';\n",
                encoding="utf-8",
            )
            handwritten = output / "handwritten_api.dart"
            handwritten.write_text("// project code\n", encoding="utf-8")

            with patch(
                "openapi_to_retrofit.format_dart", side_effect=lambda value: value
            ):
                drift = generate(source, output, check=True, rules=())

            self.assertIn(output / "current_api.dart", drift)
            self.assertIn(stale, drift)
            self.assertIn(stale_part, drift)
            self.assertTrue(stale.exists())
            self.assertTrue(stale_part.exists())

            with patch(
                "openapi_to_retrofit.format_dart", side_effect=lambda value: value
            ):
                generate(source, output, check=False, rules=())

            self.assertFalse(stale.exists())
            self.assertFalse(stale_part.exists())
            self.assertTrue(handwritten.exists())

    def test_single_file_generation_does_not_prune_other_sdks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "current.openapi.json"
            output = root / "lib/api/gen"
            output.mkdir(parents=True)
            source.write_text(
                '{"openapi":"3.0.1","paths":{},"components":{"schemas":{}}}',
                encoding="utf-8",
            )
            other = output / "other_api.dart"
            other.write_text(f"{MARKER}\n", encoding="utf-8")

            with patch(
                "openapi_to_retrofit.format_dart", side_effect=lambda value: value
            ):
                generate(source, output, check=False, rules=())

            self.assertTrue(other.exists())

    def test_project_config_defines_wrappers_without_fixed_fields(self) -> None:
        rules = dart_generic_wrapper_rules(
            {
                "transport": {
                    "backend_openapi": {
                        "dart_codegen": {
                            "generic_wrappers": {
                                "request": {
                                    "dart_name": "ReqWrapper",
                                    "schema_glob": "StandardRequest*",
                                    "type_parameter_field": "data",
                                },
                                "response": {
                                    "dart_name": "RspWrapper",
                                    "schema_glob": "Response*",
                                    "type_parameter_field": "data",
                                },
                            }
                        }
                    }
                }
            }
        )

        self.assertEqual(
            [(rule.dart_name, rule.schema_glob) for rule in rules],
            [
                ("ReqWrapper", "StandardRequest*"),
                ("RspWrapper", "Response*"),
            ],
        )

    def test_renders_one_generic_class_for_each_configured_wrapper(self) -> None:
        rules = (
            DartGenericWrapperRule(
                rule_name="request",
                dart_name="ReqWrapper",
                schema_glob="StandardRequest*",
                type_parameter_field="data",
            ),
            DartGenericWrapperRule(
                rule_name="response",
                dart_name="RspWrapper",
                schema_glob="Response*",
                type_parameter_field="data",
            ),
        )
        document = {
            "openapi": "3.0.1",
            "paths": {
                "/login": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/StandardRequestLogin"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ResponseLogin"
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "StandardRequestLogin": wrapper_schema(
                        fixed_name="tenant",
                        payload={"$ref": "#/components/schemas/LoginReq"},
                    ),
                    "StandardRequestReset": wrapper_schema(
                        fixed_name="tenant",
                        payload={"$ref": "#/components/schemas/ResetReq"},
                    ),
                    "ResponseLogin": wrapper_schema(
                        fixed_name="code",
                        payload={"$ref": "#/components/schemas/LoginRsp"},
                    ),
                    "ResponseString": wrapper_schema(
                        fixed_name="code", payload={"type": "string"}
                    ),
                    "LoginReq": {"type": "object", "properties": {}},
                    "ResetReq": {"type": "object", "properties": {}},
                    "LoginRsp": {"type": "object", "properties": {}},
                }
            },
        }

        source = render_document(
            document, Path("docs/openapi/auth.openapi.json"), rules
        )

        self.assertEqual(source.count("class ReqWrapper<T>"), 1)
        self.assertEqual(source.count("class RspWrapper<T>"), 1)
        self.assertIn("@Body() ReqWrapper<LoginReq> body", source)
        self.assertIn("Future<RspWrapper<LoginRsp>>", source)
        self.assertNotIn("class StandardRequestLogin", source)
        self.assertNotIn("class ResponseString", source)
        self.assertIn("required this.tenant,", source)
        self.assertIn("required this.code,", source)
        self.assertIn("final String tenant;", source)
        self.assertIn("final String code;", source)

    def test_rejects_drift_outside_the_generic_field(self) -> None:
        schemas = {
            "ResponseOne": wrapper_schema(
                fixed_name="code", payload={"type": "string"}
            ),
            "ResponseTwo": wrapper_schema(
                fixed_name="message", payload={"type": "boolean"}
            ),
        }
        rule = DartGenericWrapperRule(
            rule_name="response",
            dart_name="RspWrapper",
            schema_glob="Response*",
            type_parameter_field="data",
        )

        with self.assertRaisesRegex(ValueError, "differ outside property 'data'"):
            build_wrapper_models(schemas, (rule,))

    def test_rejects_unsupported_wrapper_config(self) -> None:
        with self.assertRaisesRegex(ResolveError, "unsupported fields"):
            dart_generic_wrapper_rules(
                {
                    "transport": {
                        "backend_openapi": {
                            "dart_codegen": {
                                "generic_wrappers": {
                                    "response": {
                                        "dart_name": "RspWrapper",
                                        "schema_glob": "Response*",
                                        "type_parameter_field": "data",
                                        "fixed_fields": "code,message",
                                    }
                                }
                            }
                        }
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
