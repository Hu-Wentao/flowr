#!/usr/bin/env python3
"""Tests for config-aware OpenAPI Retrofit generation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from openapi_to_retrofit import (  # noqa: E402
    build_wrapper_models,
    render_document,
)
from resolve import DartGenericWrapperRule, ResolveError, dart_generic_wrapper_rules  # noqa: E402


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
                        fixed_name="tenant", payload={"$ref": "#/components/schemas/LoginReq"}
                    ),
                    "StandardRequestReset": wrapper_schema(
                        fixed_name="tenant", payload={"$ref": "#/components/schemas/ResetReq"}
                    ),
                    "ResponseLogin": wrapper_schema(
                        fixed_name="code", payload={"$ref": "#/components/schemas/LoginRsp"}
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

        source = render_document(document, Path("docs/openapi/auth.openapi.json"), rules)

        self.assertEqual(source.count("class ReqWrapper<T>"), 1)
        self.assertEqual(source.count("class RspWrapper<T>"), 1)
        self.assertIn("@Body() ReqWrapper<LoginReq> body", source)
        self.assertIn("Future<RspWrapper<LoginRsp>>", source)
        self.assertNotIn("class StandardRequestLogin", source)
        self.assertNotIn("class ResponseString", source)
        self.assertIn("final String? tenant;", source)
        self.assertIn("final String? code;", source)

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
