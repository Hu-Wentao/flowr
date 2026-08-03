#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
# ///
"""Resolve fr-mvvm-contract task instructions with project profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RESOLVER_VERSION = "11"
SKILL_NAME = "fr-mvvm-contract"
DEFAULT_DESCRIPTION_LANGUAGE = "English"
SUPPORTED_TASKS = (
    "adapt_project",
    "gen_page",
    "gen_component",
    "extract_shared_ui",
    "validate",
    "validate_routes",
    "validate_navigation_shell",
    "audit_figma_fidelity",
    "refresh",
    "package_bff",
    "generate_openapi",
)
READ_POLICY = "read_if_not_already_loaded_in_this_thread"


class ResolveError(ValueError):
    """Raised when resolver input or config is invalid."""


@dataclass(frozen=True)
class ResolvedTask:
    """Resolved task data before output rendering."""

    task: str
    profile: str
    description_language: str
    instructions_id: str
    instructions_text: str
    cache_path: Path
    sources: dict[str, str]
    commands: dict[str, str]
    deltas: tuple[str, ...]
    request_data_envelope: "RequestDataEnvelopeProfile | None"
    bff_response_envelope: "BffResponseEnvelopeProfile | None"
    backend_openapi: "BackendOpenApiProfile | None"
    dart_generic_wrappers: tuple["DartGenericWrapperRule", ...]
    dart_interceptor_owned_headers: tuple[str, ...]


@dataclass(frozen=True)
class RequestDataEnvelopeProfile:
    """Project-owned Retrofit metadata for data-envelope payloads."""

    extra_key: str
    extra_import: str


@dataclass(frozen=True)
class BffResponseEnvelopeProfile:
    """Project-owned outer response fields represented in every BFF response DTO."""

    state_field: str
    code_field: str
    message_field: str
    data_field: str


@dataclass(frozen=True)
class BackendOpenApiProfile:
    """Project-owned local checkout root for relative OpenAPI references."""

    local_root: Path
    configured_root: str


@dataclass(frozen=True)
class DartGenericWrapperRule:
    """Project-owned OpenAPI schema-to-Dart generic wrapper mapping."""

    rule_name: str
    dart_name: str
    schema_glob: str
    type_parameter_field: str
    missing_type_parameter_field: str = "reject"


def find_repo_root(start: Path) -> Path:
    """Return the nearest parent containing .git, or the start directory."""

    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def is_relative_to(path: Path, root: Path) -> bool:
    """Backport Path.is_relative_to for stable explicit checks."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def display_path(path: Path, repo_root: Path) -> str:
    """Return a deterministic repository-relative path when possible."""

    resolved = path.resolve()
    if is_relative_to(resolved, repo_root):
        return str(resolved.relative_to(repo_root))
    return str(resolved)


def parse_scalar(value: str) -> str:
    """Parse a scalar from the supported YAML subset."""

    stripped = value.strip()
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in {"'", '"'}
    ):
        return stripped[1:-1]
    return stripped


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small mapping-only YAML subset used by config.yaml.

    Supported syntax:
    - string keys
    - nested maps by two-space indentation
    - string scalar values

    Lists, anchors, multiline strings, and other YAML features are deliberately
    unsupported so the resolver does not need a runtime dependency.
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("\t"):
            raise ResolveError(f"config.yaml:{line_number}: tabs are not supported")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise ResolveError(
                f"config.yaml:{line_number}: indentation must use two spaces"
            )
        line = raw_line.strip()
        if line.startswith("- "):
            raise ResolveError(f"config.yaml:{line_number}: lists are not supported")
        if ":" not in line:
            raise ResolveError(f"config.yaml:{line_number}: expected key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ResolveError(f"config.yaml:{line_number}: empty keys are invalid")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value.strip():
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_config(config_path: Path) -> tuple[dict[str, Any], str | None]:
    """Load project config if present."""

    if not config_path.exists():
        return {}, None
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        return parse_simple_yaml(text), text
    try:
        parsed = yaml.safe_load(text)
    except Exception as exc:  # pragma: no cover - depends on optional PyYAML
        raise ResolveError(f"failed to parse {config_path}: {exc}") from exc
    if parsed is None:
        return {}, text
    if not isinstance(parsed, dict):
        raise ResolveError("config.yaml must contain a mapping")
    return parsed, text


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    """Require a mapping value."""

    if not isinstance(value, dict):
        raise ResolveError(f"{name} must be a mapping")
    return value


def resolve_config_path(
    raw_value: str,
    *,
    relative_root: Path,
    repo_root: Path,
    field_name: str,
) -> Path:
    """Resolve a configured path and reject traversal outside allowed roots."""

    raw_path = Path(raw_value)
    if raw_path.is_absolute():
        candidate = raw_path.resolve()
        allowed_root = repo_root.resolve()
    elif raw_value.startswith(".agents/"):
        candidate = (repo_root / raw_path).resolve()
        allowed_root = repo_root.resolve()
    else:
        candidate = (relative_root / raw_path).resolve()
        allowed_root = relative_root.resolve()
    if not is_relative_to(candidate, allowed_root):
        raise ResolveError(f"{field_name} escapes {display_path(allowed_root, repo_root)}")
    relative_is_in_repo = is_relative_to(relative_root.resolve(), repo_root.resolve())
    if relative_is_in_repo and not is_relative_to(candidate, repo_root.resolve()):
        raise ResolveError(f"{field_name} escapes repository root")
    return candidate


def default_task_config(task: str) -> dict[str, Any]:
    """Return a generic fallback task config."""

    return {"base": f"references/{task}.md"}


def require_string(value: Any, name: str) -> str:
    """Require a non-empty string configuration value."""

    if not isinstance(value, str) or not value.strip():
        raise ResolveError(f"{name} must be a non-empty string")
    return value


def request_data_envelope_profile(
    config: dict[str, Any],
) -> RequestDataEnvelopeProfile | None:
    """Read the optional interceptor-owned request data envelope profile."""

    transport = config.get("transport")
    if transport is None:
        return None
    transport_mapping = require_mapping(transport, "transport")
    raw_profile = transport_mapping.get("request_data_envelope")
    if raw_profile is None:
        return None
    profile = require_mapping(raw_profile, "transport.request_data_envelope")
    mode = require_string(
        profile.get("mode"), "transport.request_data_envelope.mode"
    )
    if mode != "interceptor":
        raise ResolveError(
            "transport.request_data_envelope.mode must be interceptor"
        )
    extra = require_mapping(
        profile.get("retrofit_extra"),
        "transport.request_data_envelope.retrofit_extra",
    )
    return RequestDataEnvelopeProfile(
        extra_key=require_string(
            extra.get("key"),
            "transport.request_data_envelope.retrofit_extra.key",
        ),
        extra_import=require_string(
            extra.get("import"),
            "transport.request_data_envelope.retrofit_extra.import",
        ),
    )


def bff_response_envelope_profile(
    config: dict[str, Any],
) -> BffResponseEnvelopeProfile | None:
    """Read the optional project-wide BFF response envelope definition."""

    transport = config.get("transport")
    if transport is None:
        return None
    transport_mapping = require_mapping(transport, "transport")
    raw_profile = transport_mapping.get("bff_response_envelope")
    if raw_profile is None:
        return None
    profile = require_mapping(raw_profile, "transport.bff_response_envelope")
    return BffResponseEnvelopeProfile(
        state_field=require_string(
            profile.get("state_field"),
            "transport.bff_response_envelope.state_field",
        ),
        code_field=require_string(
            profile.get("code_field"),
            "transport.bff_response_envelope.code_field",
        ),
        message_field=require_string(
            profile.get("message_field"),
            "transport.bff_response_envelope.message_field",
        ),
        data_field=require_string(
            profile.get("data_field"),
            "transport.bff_response_envelope.data_field",
        ),
    )


def backend_openapi_profile(
    config: dict[str, Any], repo_root: Path
) -> BackendOpenApiProfile | None:
    """Read the optional local root for relative backend OpenAPI references."""

    transport = config.get("transport")
    if transport is None:
        return None
    transport_mapping = require_mapping(transport, "transport")
    raw_profile = transport_mapping.get("backend_openapi")
    if raw_profile is None:
        return None
    profile = require_mapping(raw_profile, "transport.backend_openapi")
    configured_root = require_string(
        profile.get("local_root"), "transport.backend_openapi.local_root"
    )
    raw_root = Path(configured_root)
    if raw_root.is_absolute():
        raise ResolveError(
            "transport.backend_openapi.local_root must be repository-relative"
        )
    local_root = (repo_root / raw_root).resolve()
    if not is_relative_to(local_root, repo_root.resolve()):
        raise ResolveError(
            "transport.backend_openapi.local_root escapes repository root"
        )
    return BackendOpenApiProfile(
        local_root=local_root,
        configured_root=raw_root.as_posix(),
    )


def dart_generic_wrapper_rules(
    config: dict[str, Any],
) -> tuple[DartGenericWrapperRule, ...]:
    """Read configured generic wrappers for OpenAPI Dart generation."""

    transport = config.get("transport")
    if transport is None:
        return ()
    transport_mapping = require_mapping(transport, "transport")
    raw_backend = transport_mapping.get("backend_openapi")
    if raw_backend is None:
        return ()
    backend = require_mapping(raw_backend, "transport.backend_openapi")
    raw_codegen = backend.get("dart_codegen")
    if raw_codegen is None:
        return ()
    codegen = require_mapping(raw_codegen, "transport.backend_openapi.dart_codegen")
    raw_wrappers = codegen.get("generic_wrappers")
    if raw_wrappers is None:
        return ()
    wrappers = require_mapping(
        raw_wrappers,
        "transport.backend_openapi.dart_codegen.generic_wrappers",
    )
    rules: list[DartGenericWrapperRule] = []
    dart_names: set[str] = set()
    for raw_name, raw_rule in wrappers.items():
        rule_name = require_string(
            raw_name,
            "transport.backend_openapi.dart_codegen.generic_wrappers key",
        )
        prefix = (
            "transport.backend_openapi.dart_codegen.generic_wrappers."
            + rule_name
        )
        rule = require_mapping(raw_rule, prefix)
        unknown = set(rule) - {
            "dart_name",
            "schema_glob",
            "type_parameter_field",
            "missing_type_parameter_field",
        }
        if unknown:
            raise ResolveError(
                f"{prefix} contains unsupported fields: {', '.join(sorted(unknown))}"
            )
        dart_name = require_string(rule.get("dart_name"), f"{prefix}.dart_name")
        type_parameter_field = require_string(
            rule.get("type_parameter_field"),
            f"{prefix}.type_parameter_field",
        )
        if not dart_name.isidentifier():
            raise ResolveError(f"{prefix}.dart_name must be an identifier")
        if not type_parameter_field.isidentifier():
            raise ResolveError(
                f"{prefix}.type_parameter_field must be an identifier"
            )
        missing_type_parameter_field = require_string(
            rule.get("missing_type_parameter_field", "reject"),
            f"{prefix}.missing_type_parameter_field",
        )
        if missing_type_parameter_field not in {"reject", "optional"}:
            raise ResolveError(
                f"{prefix}.missing_type_parameter_field must be "
                "'reject' or 'optional'"
            )
        if dart_name in dart_names:
            raise ResolveError(
                "transport.backend_openapi.dart_codegen.generic_wrappers "
                f"reuses dart_name {dart_name!r}"
            )
        dart_names.add(dart_name)
        rules.append(
            DartGenericWrapperRule(
                rule_name=rule_name,
                dart_name=dart_name,
                schema_glob=require_string(
                    rule.get("schema_glob"), f"{prefix}.schema_glob"
                ),
                type_parameter_field=type_parameter_field,
                missing_type_parameter_field=missing_type_parameter_field,
            )
        )
    return tuple(rules)


def dart_interceptor_owned_headers(config: dict[str, Any]) -> tuple[str, ...]:
    """Read headers supplied by the consuming project's Dio interceptors."""

    transport = config.get("transport")
    if transport is None:
        return ()
    transport_mapping = require_mapping(transport, "transport")
    raw_backend = transport_mapping.get("backend_openapi")
    if raw_backend is None:
        return ()
    backend = require_mapping(raw_backend, "transport.backend_openapi")
    raw_codegen = backend.get("dart_codegen")
    if raw_codegen is None:
        return ()
    codegen = require_mapping(raw_codegen, "transport.backend_openapi.dart_codegen")
    raw_headers = codegen.get("interceptor_owned_headers")
    if raw_headers is None:
        return ()
    prefix = "transport.backend_openapi.dart_codegen.interceptor_owned_headers"
    headers = require_mapping(raw_headers, prefix)
    resolved: list[str] = []
    seen: set[str] = set()
    for raw_name, raw_header in headers.items():
        name = require_string(raw_name, f"{prefix} key")
        header = require_string(raw_header, f"{prefix}.{name}")
        if header in seen:
            raise ResolveError(f"{prefix} repeats header {header!r}")
        seen.add(header)
        resolved.append(header)
    return tuple(resolved)


def load_request_data_envelope_profile(
    start: Path,
) -> RequestDataEnvelopeProfile | None:
    """Load the nearest repository's data-envelope profile without caching."""

    repo_root = find_repo_root(start)
    config, _ = load_config(
        repo_root / ".agents" / "skills-config" / SKILL_NAME / "config.yaml"
    )
    if not config:
        return None
    schema = str(config.get("schema", ""))
    if schema != "fr-mvvm-contract.config.v1":
        raise ResolveError("config.yaml schema must be fr-mvvm-contract.config.v1")
    return request_data_envelope_profile(config)


def load_bff_response_envelope_profile(
    start: Path,
) -> BffResponseEnvelopeProfile | None:
    """Load the nearest repository's BFF response envelope profile."""

    repo_root = find_repo_root(start)
    config, _ = load_config(
        repo_root / ".agents" / "skills-config" / SKILL_NAME / "config.yaml"
    )
    if not config:
        return None
    schema = str(config.get("schema", ""))
    if schema != "fr-mvvm-contract.config.v1":
        raise ResolveError("config.yaml schema must be fr-mvvm-contract.config.v1")
    return bff_response_envelope_profile(config)


def load_backend_openapi_profile(start: Path) -> BackendOpenApiProfile | None:
    """Load the nearest repository's backend OpenAPI reference root."""

    repo_root = find_repo_root(start)
    config, _ = load_config(
        repo_root / ".agents" / "skills-config" / SKILL_NAME / "config.yaml"
    )
    if not config:
        return None
    schema = str(config.get("schema", ""))
    if schema != "fr-mvvm-contract.config.v1":
        raise ResolveError("config.yaml schema must be fr-mvvm-contract.config.v1")
    return backend_openapi_profile(config, repo_root)


def load_dart_generic_wrapper_rules(
    start: Path,
) -> tuple[DartGenericWrapperRule, ...]:
    """Load the nearest repository's configured OpenAPI generic wrappers."""

    repo_root = find_repo_root(start)
    config, _ = load_config(
        repo_root / ".agents" / "skills-config" / SKILL_NAME / "config.yaml"
    )
    if not config:
        return ()
    schema = str(config.get("schema", ""))
    if schema != "fr-mvvm-contract.config.v1":
        raise ResolveError("config.yaml schema must be fr-mvvm-contract.config.v1")
    return dart_generic_wrapper_rules(config)


def load_dart_interceptor_owned_headers(start: Path) -> tuple[str, ...]:
    """Load headers supplied by the nearest repository's Dio interceptors."""

    repo_root = find_repo_root(start)
    config, _ = load_config(
        repo_root / ".agents" / "skills-config" / SKILL_NAME / "config.yaml"
    )
    if not config:
        return ()
    schema = str(config.get("schema", ""))
    if schema != "fr-mvvm-contract.config.v1":
        raise ResolveError("config.yaml schema must be fr-mvvm-contract.config.v1")
    return dart_interceptor_owned_headers(config)


def read_required(path: Path, label: str, repo_root: Path) -> str:
    """Read a required instruction file."""

    if not path.exists():
        raise ResolveError(f"{label} not found: {display_path(path, repo_root)}")
    return path.read_text(encoding="utf-8").strip()


def build_deltas(task: str, profile: str, has_profile: bool) -> tuple[str, ...]:
    """Return short manifest deltas."""

    if not has_profile:
        if task == "adapt_project":
            return (
                "Use the bundled ACDD scaffold as the structural baseline.",
                "Preserve existing behavior and platform configuration during adaptation.",
            )
        if task == "package_bff":
            return ("Package all project BFF contracts with the generic collector.",)
        return ("Using generic fr-mvvm-contract fallback instructions.",)
    return (f"Using project profile: {profile}.",)


def task_command(
    script_path: Path,
    repo_root: Path,
    placeholder: str,
) -> str:
    """Render a Python command for a profile script."""

    return f"uv run --script {display_path(script_path, repo_root)} {placeholder}".strip()


def resolve_task(args: argparse.Namespace) -> ResolvedTask:
    """Resolve instructions and cache location for a task."""

    repo_root = find_repo_root(args.cwd or Path.cwd())
    installed_skill_root = repo_root / ".agents" / "skills" / SKILL_NAME
    bundled_skill_root = Path(__file__).resolve().parents[1]
    skill_root = (
        installed_skill_root if installed_skill_root.is_dir() else bundled_skill_root
    )
    config_root = repo_root / ".agents" / "skills-config" / SKILL_NAME
    cache_root = repo_root / ".agents" / ".cache" / SKILL_NAME
    config_path = config_root / "config.yaml"

    if args.task not in SUPPORTED_TASKS:
        raise ResolveError(
            f"unsupported task {args.task!r}; expected one of {', '.join(SUPPORTED_TASKS)}"
        )

    config, config_text = load_config(config_path)
    data_envelope = request_data_envelope_profile(config) if config else None
    response_envelope = bff_response_envelope_profile(config) if config else None
    backend_openapi = backend_openapi_profile(config, repo_root) if config else None
    generic_wrappers = dart_generic_wrapper_rules(config) if config else ()
    interceptor_owned_headers = (
        dart_interceptor_owned_headers(config) if config else ()
    )
    if config:
        schema = str(config.get("schema", ""))
        if schema != "fr-mvvm-contract.config.v1":
            raise ResolveError(
                "config.yaml schema must be fr-mvvm-contract.config.v1"
            )
        profile = str(config.get("profile", "generic"))
        contract_config = require_mapping(config.get("contract", {}), "contract")
        description_language = require_string(
            contract_config.get(
                "description_language", DEFAULT_DESCRIPTION_LANGUAGE
            ),
            "contract.description_language",
        )
        if "service" in config:
            raise ResolveError(
                "service.base_url is obsolete; configure AppEnv.apiBaseUrl and "
                "createAppDio(AppEnv) instead"
            )
        tasks = require_mapping(config.get("tasks", {}), "tasks")
        task_config = require_mapping(
            tasks.get(args.task, {}), f"tasks.{args.task}"
        )
        if (
            args.task
            in {
                "adapt_project",
                "extract_shared_ui",
                "validate_routes",
                "validate_navigation_shell",
                "audit_figma_fidelity",
                "package_bff",
                "generate_openapi",
            }
            and not task_config
        ):
            task_config = default_task_config(args.task)
    else:
        profile = "generic"
        description_language = DEFAULT_DESCRIPTION_LANGUAGE
        task_config = default_task_config(args.task)

    if not task_config:
        raise ResolveError(f"task {args.task!r} is not configured")

    sources: dict[str, str] = {}
    commands: dict[str, str] = {}

    base_value = require_string(
        task_config.get("base") or f"references/{args.task}.md",
        f"tasks.{args.task}.base",
    )
    base_path = resolve_config_path(
        base_value,
        relative_root=skill_root,
        repo_root=repo_root,
        field_name=f"tasks.{args.task}.base",
    )
    base_text = read_required(base_path, "base instructions", repo_root)
    sources["base"] = display_path(base_path, repo_root)

    profile_text = ""
    has_profile = False
    profile_value = task_config.get("profile")
    if profile_value:
        profile_value = require_string(profile_value, f"tasks.{args.task}.profile")
        profile_path = resolve_config_path(
            profile_value,
            relative_root=config_root,
            repo_root=repo_root,
            field_name=f"tasks.{args.task}.profile",
        )
        profile_text = read_required(profile_path, "profile instructions", repo_root)
        sources["profile"] = display_path(profile_path, repo_root)
        has_profile = True

    if config_text is not None:
        sources["project_config"] = display_path(config_path, repo_root)

    if args.task == "package_bff":
        package_script = skill_root / "scripts/package_bff.py"
        commands["package"] = (
            f"uv run --script {display_path(package_script, repo_root)} "
            "--project-root . --output build/bff-contracts.zip"
        )
    if args.task == "validate_routes":
        route_validator = skill_root / "scripts/validate_routes.py"
        commands["validate_routes"] = (
            f"uv run --script {display_path(route_validator, repo_root)} "
            "--module-file <lib/app/module/module.dart>"
        )
    if args.task == "validate_navigation_shell":
        shell_validator = skill_root / "scripts/validate_navigation_shell.py"
        commands["validate_navigation_shell"] = (
            f"uv run --script {display_path(shell_validator, repo_root)} "
            "--project-root . --profile "
            "<.agents/skills-config/fr-mvvm-contract/navigation-shell.json>"
        )
    if args.task == "generate_openapi":
        openapi_generator = skill_root / "scripts/openapi_to_retrofit.py"
        commands["generate_openapi"] = (
            f"uv run --script {display_path(openapi_generator, repo_root)} "
            "--source <openapi-root> --output <dart-output>"
        )

    for key in ("adapter", "generate", "validator"):
        value = task_config.get(key)
        if not value:
            continue
        value = require_string(value, f"tasks.{args.task}.{key}")
        resolved = resolve_config_path(
            value,
            relative_root=config_root,
            repo_root=repo_root,
            field_name=f"tasks.{args.task}.{key}",
        )
        sources[key] = display_path(resolved, repo_root)
        if key == "generate":
            commands[key] = task_command(resolved, repo_root, "--page-file <xxx.page.dart>")
        elif key == "validator":
            commands["validate"] = task_command(resolved, repo_root, "--component-file <xxx.dart>")

    global_commands = config.get("commands", {}) if config else {}
    if global_commands:
        for key, value in require_mapping(global_commands, "commands").items():
            commands[str(key)] = require_string(value, f"commands.{key}")

    task_commands = task_config.get("commands", {})
    if task_commands:
        for key, value in require_mapping(
            task_commands, f"tasks.{args.task}.commands"
        ).items():
            commands[str(key)] = require_string(
                value, f"tasks.{args.task}.commands.{key}"
            )

    hash_input = {
        "resolver_version": RESOLVER_VERSION,
        "task": args.task,
        "profile": profile,
        "description_language": description_language,
        "config": config_text or "",
        "sources": sources,
        "base": base_text,
        "profile_text": profile_text,
        "commands": commands,
        "request_data_envelope": (
            {
                "extra_key": data_envelope.extra_key,
                "extra_import": data_envelope.extra_import,
            }
            if data_envelope
            else None
        ),
        "bff_response_envelope": (
            {
                "state_field": response_envelope.state_field,
                "code_field": response_envelope.code_field,
                "message_field": response_envelope.message_field,
                "data_field": response_envelope.data_field,
            }
            if response_envelope
            else None
        ),
        "backend_openapi": (
            {"local_root": backend_openapi.configured_root} if backend_openapi else None
        ),
        "dart_generic_wrappers": [
            {
                "rule_name": rule.rule_name,
                "dart_name": rule.dart_name,
                "schema_glob": rule.schema_glob,
                "type_parameter_field": rule.type_parameter_field,
                "missing_type_parameter_field": (
                    rule.missing_type_parameter_field
                ),
            }
            for rule in generic_wrappers
        ],
        "dart_interceptor_owned_headers": interceptor_owned_headers,
    }
    digest = hashlib.sha256(
        json.dumps(hash_input, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:7]
    instructions_id = f"{SKILL_NAME}/{args.task}@{digest}"
    cache_path = cache_root / f"{args.task}.{digest}.md"
    deltas = build_deltas(args.task, profile, has_profile)

    instructions_parts = [
        f"# Resolved {SKILL_NAME} Instructions",
        "",
        f"- Task: `{args.task}`",
        f"- Profile: `{profile}`",
        f"- Contract Description Language: `{description_language}`",
        f"- Instructions ID: `{instructions_id}`",
        "",
        "## Contract Description Language",
        "",
        f"Write descriptive contract values in {description_language}. This includes "
        "Data and Business entries, the purpose prose in Request Field Sources, "
        "and Notes. Keep stable contract labels, Dart identifiers and types, HTTP "
        "methods and paths, enum literals, and code references unchanged. Preserve "
        "authoritative source expressions in Request Field Sources; translate only "
        "their surrounding descriptive prose.",
        "",
        "## Base Instructions",
        "",
        base_text,
    ]
    if data_envelope:
        instructions_parts.extend(
            [
                "",
                "## Request Data Envelope Transport",
                "",
                "This project documents interceptor-owned `data` envelopes for the "
                "frontend UI data API. Model only the business payload as a root "
                "`XxxRequestDto`; do not add a duplicate `XxxBffReq(data: ...)` "
                "wrapper. This profile does not generate Retrofit Service code. "
                "The SDK adapter must use the wrappers and DTOs generated from "
                "OpenAPI in `lib/api/gen`.",
            ]
        )
    if response_envelope:
        instructions_parts.extend(
            [
                "",
                "## BFF Response Envelope",
                "",
                "This project represents the full gateway response in every root "
                "`XxxBffRsp`. Its required outer fields are `"
                + response_envelope.state_field
                + "`, `"
                + response_envelope.code_field
                + "`, `"
                + response_envelope.message_field
                + "`, and `"
                + response_envelope.data_field
                + "`. Move the original business response definition under `"
                + response_envelope.data_field
                + "`; use a nested `XxxDto` when that business value is structured. "
                "BFF Markdown therefore documents the complete envelope, not only "
                "its business `data` value.",
            ]
        )
    if backend_openapi:
        instructions_parts.extend(
            [
                "",
                "## Backend OpenAPI Authority",
                "",
                "Resolve local backend OpenAPI references relative to the configured "
                "documentation checkout root `"
                + backend_openapi.configured_root
                + "`. Author BFF references relative to that root (for example "
                "`openapi/example.openapi.json`), never with the checkout's "
                "application-project path. The OpenAPI files are independently owned "
                "and are not BFF package or synchronization payloads.",
            ]
        )
    if generic_wrappers:
        rendered_rules = ", ".join(
            f"`{rule.schema_glob}` -> `{rule.dart_name}<T>` via "
            f"`{rule.type_parameter_field}` "
            f"(missing: `{rule.missing_type_parameter_field}`)"
            for rule in generic_wrappers
        )
        instructions_parts.extend(
            [
                "",
                "## OpenAPI Dart Generic Wrappers",
                "",
                "Apply the configured generic wrapper rules during OpenAPI-to-Dart "
                "generation: "
                + rendered_rules
                + ". Derive every non-generic field from the matched OpenAPI schemas. "
                "A rule configured with `missing: optional` may map a matched "
                "schema that omits its non-required type-parameter field to "
                "`dynamic`; the generated wrapper field remains nullable. "
                "Fail generation when schemas matched by one rule differ anywhere "
                "outside its configured type-parameter field.",
            ]
        )
    if interceptor_owned_headers:
        instructions_parts.extend(
            [
                "",
                "## OpenAPI Interceptor-Owned Headers",
                "",
                "Resolve OpenAPI parameter references before rendering operation "
                "arguments. Do not expose these project-configured headers as SDK "
                "method parameters because the application Dio interceptor owns "
                "their injection: `"
                + "`, `".join(interceptor_owned_headers)
                + "`. Preserve every other referenced header, including "
                "operation-specific authorization headers.",
            ]
        )
    if profile_text:
        instructions_parts.extend(["", "## Project Profile Instructions", "", profile_text])
    instructions_parts.extend(
        [
            "",
            "## Precedence",
            "",
            "Apply base instructions first, then project profile instructions; "
            "project task commands override generic commands with the same name.",
        ]
    )
    if commands:
        instructions_parts.extend(["", "## Commands", ""])
        for key in sorted(commands):
            instructions_parts.append(f"- `{key}`: `{commands[key]}`")
    instructions_text = "\n".join(instructions_parts).rstrip() + "\n"

    return ResolvedTask(
        task=args.task,
        profile=profile,
        description_language=description_language,
        instructions_id=instructions_id,
        instructions_text=instructions_text,
        cache_path=cache_path,
        sources=sources,
        commands=commands,
        deltas=deltas,
        request_data_envelope=data_envelope,
        bff_response_envelope=response_envelope,
        backend_openapi=backend_openapi,
        dart_generic_wrappers=generic_wrappers,
        dart_interceptor_owned_headers=interceptor_owned_headers,
    )


def ensure_cache(resolved: ResolvedTask, repo_root: Path, *, force: bool) -> None:
    """Write the resolved instructions cache when needed."""

    cache_root = repo_root / ".agents" / ".cache" / SKILL_NAME
    resolved_cache = resolved.cache_path.resolve()
    if not is_relative_to(resolved_cache, cache_root.resolve()):
        raise ResolveError("cache path escapes cache root")
    if force or not resolved.cache_path.exists():
        resolved.cache_path.parent.mkdir(parents=True, exist_ok=True)
        resolved.cache_path.write_text(resolved.instructions_text, encoding="utf-8")


def render_manifest(resolved: ResolvedTask, repo_root: Path) -> str:
    """Render a compact deterministic manifest."""

    lines = [
        f"skill: {SKILL_NAME}",
        f"task: {resolved.task}",
        f"profile: {resolved.profile}",
        f"description_language: {resolved.description_language}",
        "request_data_envelope: "
        + ("interceptor" if resolved.request_data_envelope else "none"),
        "bff_response_envelope: "
        + ("configured" if resolved.bff_response_envelope else "none"),
        "backend_openapi_root: "
        + (
            resolved.backend_openapi.configured_root
            if resolved.backend_openapi
            else "project-root"
        ),
        "dart_generic_wrappers: "
        + (
            ",".join(rule.dart_name for rule in resolved.dart_generic_wrappers)
            if resolved.dart_generic_wrappers
            else "none"
        ),
        "dart_interceptor_owned_headers: "
        + (
            ",".join(resolved.dart_interceptor_owned_headers)
            if resolved.dart_interceptor_owned_headers
            else "none"
        ),
        "status: ready",
        f"instructions_id: {resolved.instructions_id}",
        "",
        "sources:",
    ]
    for key in sorted(resolved.sources):
        lines.append(f"  {key}: {resolved.sources[key]}")
    lines.extend(
        [
            "",
            "instructions:",
            f"  path: {display_path(resolved.cache_path, repo_root)}",
            f"  read_policy: {READ_POLICY}",
        ]
    )
    if resolved.deltas:
        lines.extend(["", "delta:"])
        for delta in resolved.deltas:
            lines.append(f"  - {delta}")
    if resolved.commands:
        lines.extend(["", "commands:"])
        for key in sorted(resolved.commands):
            lines.append(f"  {key}: {resolved.commands[key]}")
    return "\n".join(lines) + "\n"


def render_blocked(error: Exception) -> str:
    """Render a blocked manifest."""

    return "\n".join(
        [
            f"skill: {SKILL_NAME}",
            "status: blocked",
            f"reason: {error}",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Task to resolve")
    parser.add_argument(
        "--emit",
        choices=("manifest", "instructions"),
        default="manifest",
        help="Output format. Defaults to the short manifest.",
    )
    parser.add_argument(
        "--write-cache",
        action="store_true",
        help="Force-refresh the resolved instruction cache.",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        help="Optional working directory for tests or wrappers.",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""

    args = parse_args()
    repo_root = find_repo_root(args.cwd or Path.cwd())
    try:
        resolved = resolve_task(args)
        if args.emit == "instructions":
            print(resolved.instructions_text, end="")
            return 0
        ensure_cache(resolved, repo_root, force=args.write_cache)
        print(render_manifest(resolved, repo_root), end="")
        return 0
    except Exception as error:
        print(render_blocked(error), end="")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
