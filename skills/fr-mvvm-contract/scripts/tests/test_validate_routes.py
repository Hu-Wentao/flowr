#!/usr/bin/env python3
"""Tests for cross-page module and route-refactor validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
VALIDATOR = SCRIPTS / "validate_routes.py"
UV_RUN_SCRIPT = ("uv", "run", "--script")


class ValidateRoutesTest(unittest.TestCase):
    def write_fixture(
        self,
        root: Path,
        *,
        pages: str = "[LoginPage], [VerifyMobilePage], [SetPasswordPage]",
        flow_fields: str = "loginId, authType, tempAuthId",
        expand_temp_auth_id: bool = True,
        extra_in_page: bool = True,
        plain_page_extra: bool = False,
        include_extra_codec: bool = True,
        codec_covers_verify: bool = True,
        component_uses_own_extra: bool = False,
        navigation: str = "",
    ) -> Path:
        module = root / "lib/app/auth"
        login = module / "login"
        verify = module / "verify_mobile"
        password = module / "set_password"
        for directory in (login, verify, password):
            directory.mkdir(parents=True)

        module_file = module / "auth.dart"
        module_file.write_text(
            f"/// Pages: {pages}\n"
            "/// Page Data Flow:\n"
            "/// - [LoginPage] -> [VerifyMobilePage] via "
            f"[VerifyMobilePageExtra]: {flow_fields}\n"
            "/// - [VerifyMobilePage] -> [SetPasswordPage] via "
            "[SetPasswordPageExtra]: authId\n"
            "export 'login/login.page.dart' hide $appRoutes;\n"
            "export 'verify_mobile/verify_mobile.page.dart' hide $appRoutes;\n"
            "export 'set_password/set_password.page.dart' hide $appRoutes;\n",
            encoding="utf-8",
        )
        (login / "login.page.dart").write_text(
            "@TypedGoRoute<LoginPage>(path: '/login')\n"
            "class LoginPage extends GoRouteData with $LoginPage {}\n",
            encoding="utf-8",
        )
        (login / "login.dart").write_text(
            "import '../verify_mobile/verify_mobile.page.dart';\n"
            "Object next() => const VerifyMobilePageExtra(\n"
            "  loginId: 'id', authType: 'MOBILE', tempAuthId: 'temp');\n",
            encoding="utf-8",
        )
        (login / "login.c.dart").write_text("", encoding="utf-8")
        (login / "login.v.dart").write_text(navigation, encoding="utf-8")

        verify_extra = ""
        if extra_in_page:
            verify_extra = (
                "final class VerifyMobilePageExtra {\n"
                "  const VerifyMobilePageExtra({required this.loginId, "
                "required this.authType, required this.tempAuthId});\n"
                "  final String loginId;\n"
                "  final String authType;\n"
                "  final String tempAuthId;\n"
                "}\n"
                if plain_page_extra
                else (
                    "@FrAcddFreezedJSON\n"
                    "sealed class VerifyMobilePageExtra "
                    "with _$VerifyMobilePageExtra {\n"
                    "  const factory VerifyMobilePageExtra({\n"
                    "    required String loginId,\n"
                    "    required String authType,\n"
                    "    required String tempAuthId,\n"
                    "  }) = _VerifyMobilePageExtra;\n"
                    "  factory VerifyMobilePageExtra.fromJson(\n"
                    "    Map<String, dynamic> json,\n"
                    "  ) => _$VerifyMobilePageExtraFromJson(json);\n"
                    "}\n"
                )
            )
        temp_expansion = (
            "tempAuthId: $extra?.tempAuthId ?? ''," if expand_temp_auth_id else ""
        )
        (verify / "verify_mobile.page.dart").write_text(
            "part 'verify_mobile.page.freezed.dart';\n"
            "part 'verify_mobile.page.g.dart';\n"
            + verify_extra
            + "@TypedGoRoute<VerifyMobilePage>(path: '/verify-mobile')\n"
            + "class VerifyMobilePage extends GoRouteData with $VerifyMobilePage {\n"
            "  final VerifyMobilePageExtra? $extra;\n"
            "  Object build() => VerifyMobileView(\n"
            "    loginId: $extra?.loginId ?? '',\n"
            "    authType: $extra?.authType ?? 'MOBILE',\n"
            f"    {temp_expansion}\n"
            "  );\n"
            "}\n",
            encoding="utf-8",
        )
        (verify / "verify_mobile.dart").write_text(
            "Object view() => VerifyMobilePageExtra;\n"
            if component_uses_own_extra
            else "Object view() => VerifyMobileView;\n",
            encoding="utf-8",
        )

        (password / "set_password.page.dart").write_text(
            "part 'set_password.page.freezed.dart';\n"
            "part 'set_password.page.g.dart';\n"
            "@FrAcddFreezedJSON\n"
            "sealed class SetPasswordPageExtra with _$SetPasswordPageExtra {\n"
            "  const factory SetPasswordPageExtra({required String authId}) = "
            "_SetPasswordPageExtra;\n"
            "  factory SetPasswordPageExtra.fromJson(\n"
            "    Map<String, dynamic> json,\n"
            "  ) => _$SetPasswordPageExtraFromJson(json);\n"
            "}\n"
            "@TypedGoRoute<SetPasswordPage>(path: '/set-password')\n"
            "class SetPasswordPage extends GoRouteData with $SetPasswordPage {\n"
            "  final SetPasswordPageExtra? $extra;\n"
            "  Object build() => SetPasswordView(\n"
            "    authId: $extra?.authId ?? '',\n"
            "  );\n"
            "}\n",
            encoding="utf-8",
        )
        (password / "set_password.dart").write_text(
            "Object view() => SetPasswordView;\n", encoding="utf-8"
        )
        codec_source = (
            "final appRouter = GoRouter(\n"
            "  extraCodec: const AppRouteExtraCodec(), routes: const [],\n"
            ");\n"
            "Object? encodeExtra(Object? input) => switch (input) {\n"
            + (
                "  VerifyMobilePageExtra value => "
                "['VerifyMobilePageExtra', value.toJson()],\n"
                if codec_covers_verify
                else ""
            )
            + "  SetPasswordPageExtra value => "
            "['SetPasswordPageExtra', value.toJson()],\n"
            "  _ => null,\n"
            "};\n"
            "Object? decodeExtra(String type, Map<String, dynamic> data) => "
            "switch (type) {\n"
            + (
                "  'VerifyMobilePageExtra' => "
                "VerifyMobilePageExtra.fromJson(data),\n"
                if codec_covers_verify
                else ""
            )
            + "  'SetPasswordPageExtra' => SetPasswordPageExtra.fromJson(data),\n"
            "  _ => null,\n"
            "};\n"
            if include_extra_codec
            else ""
        )
        (root / "lib/app_router.dart").write_text(
            "abstract final class AppRoutes {\n"
            "  static const login = '/login';\n"
            "  static const verifyMobile = '/verify-mobile';\n"
            "  static const setPassword = '/set-password';\n"
            "}\n"
            + codec_source,
            encoding="utf-8",
        )
        if not extra_in_page:
            (module / "auth_extra.dart").write_text(
                "final class VerifyMobilePageExtra {\n"
                "  final String loginId;\n"
                "  final String authType;\n"
                "  final String tempAuthId;\n"
                "}\n",
                encoding="utf-8",
            )
        return module_file

    def validate(self, module_file: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*UV_RUN_SCRIPT, str(VALIDATOR), "--module-file", str(module_file)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_cross_page_module(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(self.write_fixture(Path(temporary)))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("route refactor validation: OK", result.stdout)

    def test_page_inventory_must_be_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = self.write_fixture(
                Path(temporary), pages="[LoginPage], [VerifyMobilePage]"
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 2)
        self.assertIn("inventory mismatch", result.stderr)

    def test_module_must_declare_pages_comment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = self.write_fixture(Path(temporary))
            module.write_text(
                module.read_text(encoding="utf-8").replace("/// Pages:", "// Pages:"),
                encoding="utf-8",
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 2)
        self.assertIn("must declare `/// Pages:`", result.stderr)

    def test_module_must_declare_page_data_flow_comment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = self.write_fixture(Path(temporary))
            module.write_text(
                module.read_text(encoding="utf-8").replace(
                    "/// Page Data Flow:", "// Page Data Flow:"
                ),
                encoding="utf-8",
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 2)
        self.assertIn("must declare `/// Page Data Flow:`", result.stderr)

    def test_page_extra_must_live_in_target_page_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), extra_in_page=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("route transport model", result.stderr)
        self.assertIn("target .page.dart", result.stderr)

    def test_page_extra_must_use_fr_acdd_freezed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), plain_page_extra=True)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must use `@FrAcddFreezedJSON`", result.stderr)

    def test_page_extra_requires_application_codec(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), include_extra_codec=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("GoRouter must configure", result.stderr)
        self.assertIn("`extraCodec`", result.stderr)

    def test_route_extra_codec_must_cover_every_extra(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), codec_covers_verify=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "codec encoder must cover VerifyMobilePageExtra",
            result.stderr,
        )

    def test_validator_preserves_approved_password_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = self.write_fixture(Path(temporary))
            page = module.parent / "verify_mobile/verify_mobile.page.dart"
            page.write_text(
                page.read_text(encoding="utf-8")
                .replace(
                    "required String tempAuthId,",
                    "required String expectedPassword,",
                )
                .replace(
                    "tempAuthId: $extra?.tempAuthId ?? '',",
                    "expectedPassword: $extra?.expectedPassword ?? '',",
                ),
                encoding="utf-8",
            )
            module.write_text(
                module.read_text(encoding="utf-8").replace(
                    "loginId, authType, tempAuthId",
                    "loginId, authType, expectedPassword",
                ),
                encoding="utf-8",
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_flow_fields_must_match_page_extra(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), flow_fields="loginId, authType")
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("flow fields", result.stderr)

    def test_page_must_expand_every_extra_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), expand_temp_auth_id=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("expand $extra.tempAuthId", result.stderr)

    def test_page_must_type_extra_with_target_page_extra(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = self.write_fixture(Path(temporary))
            page = module.parent / "verify_mobile/verify_mobile.page.dart"
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "final VerifyMobilePageExtra? $extra;",
                    "final Object? $extra;",
                ),
                encoding="utf-8",
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 2)
        self.assertIn("must declare `$extra` as VerifyMobilePageExtra", result.stderr)

    def test_target_component_must_not_use_own_page_extra(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), component_uses_own_extra=True)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must not use its sibling VerifyMobilePageExtra", result.stderr)

    def test_fixed_go_to_known_typed_page_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(
                    Path(temporary),
                    navigation=(
                        "void next(BuildContext context) => "
                        "context.go('/verify-mobile');\n"
                    ),
                )
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("targets typed VerifyMobilePage", result.stderr)
        self.assertIn("VerifyMobilePage(...).go(context)", result.stderr)

    def test_fixed_generic_push_to_known_typed_page_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(
                    Path(temporary),
                    navigation=(
                        "void next(BuildContext context) => "
                        "context.push<void>('/set-password');\n"
                    ),
                )
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("targets typed SetPasswordPage", result.stderr)
        self.assertIn("SetPasswordPage(...).push(context)", result.stderr)

    def test_fixed_uri_matching_parameterized_typed_route_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = self.write_fixture(
                root,
                navigation=(
                    "void next(BuildContext context) => "
                    "context.replace('/orders/42');\n"
                ),
            )
            orders = root / "lib/app/orders"
            orders.mkdir(parents=True)
            (orders / "orders.page.dart").write_text(
                "@TypedGoRoute<OrderPage>(path: '/orders/:orderId')\n"
                "class OrderPage extends GoRouteData with $OrderPage {}\n",
                encoding="utf-8",
            )
            result = self.validate(module)

        self.assertEqual(result.returncode, 2)
        self.assertIn("targets typed OrderPage", result.stderr)
        self.assertIn("OrderPage(...).replace(context)", result.stderr)

    def test_app_routes_constant_is_not_a_typed_navigation_substitute(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(
                    Path(temporary),
                    navigation=(
                        "void next(BuildContext context) => "
                        "context.go(AppRoutes.verifyMobile);\n"
                    ),
                )
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("context.go(AppRoutes.verifyMobile)", result.stderr)
        self.assertIn("VerifyMobilePage(...).go(context)", result.stderr)

    def test_dynamic_and_bff_returned_uris_are_allowed(self) -> None:
        for navigation in (
            "void next(BuildContext context, String uri) => context.go(uri);\n",
            "void next(BuildContext context, rsp) => context.go(rsp.nextRoute);\n",
            "void next(BuildContext context, String id) => context.go('/orders/$id');\n",
        ):
            with self.subTest(navigation=navigation):
                with tempfile.TemporaryDirectory() as temporary:
                    result = self.validate(
                        self.write_fixture(Path(temporary), navigation=navigation)
                    )

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_external_uri_literals_are_allowed(self) -> None:
        for uri in (
            "https://example.com/callback",
            "mailto:support@example.com",
            "//external.example.com/callback",
        ):
            with self.subTest(uri=uri):
                with tempfile.TemporaryDirectory() as temporary:
                    result = self.validate(
                        self.write_fixture(
                            Path(temporary),
                            navigation=(
                                "void next(BuildContext context) => "
                                f"context.push('{uri}');\n"
                            ),
                        )
                    )

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_fixed_uri_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(
                    Path(temporary),
                    navigation=(
                        "void next(BuildContext context) => "
                        "context.go('/sdk-callback');\n"
                    ),
                )
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reasoned_compatibility_boundary_allows_fixed_internal_uri(self) -> None:
        for expression in ("'/verify-mobile'", "AppRoutes.verifyMobile"):
            with self.subTest(expression=expression):
                with tempfile.TemporaryDirectory() as temporary:
                    result = self.validate(
                        self.write_fixture(
                            Path(temporary),
                            navigation=(
                                "void next(BuildContext context) {\n"
                                "  // fr-route: compatibility-boundary legacy SDK callback\n"
                                f"  context.go({expression});\n"
                                "}\n"
                            ),
                        )
                    )

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_compatibility_marker_does_not_bypass_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(
                    Path(temporary),
                    navigation=(
                        "void next(BuildContext context) {\n"
                        "  // fr-route: compatibility-boundary\n"
                        "  context.go('/verify-mobile');\n"
                        "}\n"
                    ),
                )
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("targets typed VerifyMobilePage", result.stderr)


if __name__ == "__main__":
    unittest.main()
