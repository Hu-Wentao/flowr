#!/usr/bin/env python3
"""Resolve fr-mvvm-contract task instructions with project profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


RESOLVER_VERSION = "3"
SKILL_NAME = "fr-mvvm-contract"
DEFAULT_DESCRIPTION_LANGUAGE = "English"
SUPPORTED_TASKS = (
    "adapt_project",
    "gen_page",
    "gen_component",
    "validate",
    "refresh",
    "package_bff",
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
    service_base_url: str | None
    instructions_id: str
    instructions_text: str
    cache_path: Path
    sources: dict[str, str]
    commands: dict[str, str]
    deltas: tuple[str, ...]


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

    return f"uv run python {display_path(script_path, repo_root)} {placeholder}".strip()


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
        service_config = require_mapping(config.get("service", {}), "service")
        raw_service_base_url = service_config.get("base_url")
        service_base_url = (
            require_string(raw_service_base_url, "service.base_url")
            if raw_service_base_url is not None
            else None
        )
        if service_base_url is not None:
            parsed_base_url = urlparse(service_base_url)
            if (
                parsed_base_url.scheme not in {"http", "https"}
                or not parsed_base_url.netloc
            ):
                raise ResolveError("service.base_url must be an absolute HTTP(S) URL")
        tasks = require_mapping(config.get("tasks", {}), "tasks")
        task_config = require_mapping(
            tasks.get(args.task, {}), f"tasks.{args.task}"
        )
        if args.task in {"adapt_project", "package_bff"} and not task_config:
            task_config = default_task_config(args.task)
    else:
        profile = "generic"
        description_language = DEFAULT_DESCRIPTION_LANGUAGE
        service_base_url = None
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
            f"uv run python {display_path(package_script, repo_root)} "
            "--project-root . --output build/bff-contracts.zip"
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
        "service_base_url": service_base_url,
        "config": config_text or "",
        "sources": sources,
        "base": base_text,
        "profile_text": profile_text,
        "commands": commands,
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
        f"- Service Base URL: `{service_base_url or 'constructor-required'}`",
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
        service_base_url=service_base_url,
        instructions_id=instructions_id,
        instructions_text=instructions_text,
        cache_path=cache_path,
        sources=sources,
        commands=commands,
        deltas=deltas,
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
        f"service_base_url: {resolved.service_base_url or 'constructor-required'}",
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
