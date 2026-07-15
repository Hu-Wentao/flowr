#!/usr/bin/env python3
"""Resolve FlowR core or Flutter instructions for the target Dart package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RESOLVER_VERSION = "1"
SKILL_NAME = "flowr-usage"
TASKS = ("auto", "core", "flutter")
READ_POLICY = "read_if_not_already_loaded_in_this_thread"


class ResolveError(ValueError):
    """Raised for an unsupported target package or resolver configuration."""


@dataclass(frozen=True)
class PackageKind:
    """Direct package capabilities used for route selection."""

    pubspec_path: Path
    has_flowr: bool
    has_flowr_dart: bool
    has_flutter_sdk: bool


@dataclass(frozen=True)
class ResolvedTask:
    """Resolved task data before output rendering."""

    task: str
    profile: str
    instructions_id: str
    instructions_text: str
    cache_path: Path
    sources: dict[str, str]
    package: PackageKind


def find_repo_root(start: Path) -> Path:
    """Return the nearest parent containing .git, or the start directory."""

    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def find_pubspec(start: Path, repo_root: Path) -> Path:
    """Find the nearest target package manifest without leaving the repository."""

    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pubspec.yaml").is_file():
            return candidate / "pubspec.yaml"
        if candidate == repo_root:
            break
    raise ResolveError("no target pubspec.yaml found from the selected working directory")


def is_relative_to(path: Path, root: Path) -> bool:
    """Backport Path.is_relative_to for explicit containment checks."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def display_path(path: Path, repo_root: Path) -> str:
    """Return a deterministic repository-relative path when possible."""

    resolved = path.resolve()
    if is_relative_to(resolved, repo_root.resolve()):
        return str(resolved.relative_to(repo_root.resolve()))
    return str(resolved)


def parse_pubspec(text: str) -> dict[str, Any]:
    """Parse pubspec YAML, with a narrow fallback for unavailable PyYAML."""

    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        return {}
    try:
        parsed = yaml.safe_load(text)
    except Exception as exc:  # pragma: no cover - optional dependency behavior
        raise ResolveError(f"failed to parse pubspec.yaml: {exc}") from exc
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ResolveError("pubspec.yaml must contain a mapping")
    return parsed


def has_dependency(raw: dict[str, Any], package: str, text: str) -> bool:
    """Check direct runtime or development dependency declarations."""

    for section in ("dependencies", "dev_dependencies"):
        values = raw.get(section)
        if isinstance(values, dict) and package in values:
            return True
    pattern = rf"(?m)^  {re.escape(package)}:\s*(?:[^#]+)?$"
    return re.search(pattern, text) is not None


def has_flutter_sdk(raw: dict[str, Any], text: str) -> bool:
    """Check for Flutter SDK declaration, including the no-PyYAML fallback."""

    for section in ("dependencies", "dev_dependencies"):
        values = raw.get(section)
        if not isinstance(values, dict):
            continue
        flutter = values.get("flutter")
        if isinstance(flutter, dict) and flutter.get("sdk") == "flutter":
            return True
    return re.search(
        r"(?m)^  flutter:\s*\n^    sdk:\s*flutter\s*(?:#.*)?$", text
    ) is not None


def inspect_package(pubspec_path: Path) -> PackageKind:
    """Read the direct FlowR and Flutter capabilities of a package manifest."""

    text = pubspec_path.read_text(encoding="utf-8")
    parsed = parse_pubspec(text)
    return PackageKind(
        pubspec_path=pubspec_path,
        has_flowr=has_dependency(parsed, "flowr", text),
        has_flowr_dart=has_dependency(parsed, "flowr_dart", text),
        has_flutter_sdk=has_flutter_sdk(parsed, text),
    )


def select_task(requested: str, package: PackageKind) -> str:
    """Select a valid route without ever injecting Flutter into pure Dart."""

    if package.has_flowr and not package.has_flutter_sdk:
        raise ResolveError(
            "flowr is declared without a Flutter SDK dependency; "
            "declare flutter: {sdk: flutter} or target a flowr_dart-only package"
        )
    if package.has_flowr and package.has_flutter_sdk:
        detected = "flutter"
    elif package.has_flowr_dart and not package.has_flutter_sdk:
        detected = "core"
    elif package.has_flowr_dart and package.has_flutter_sdk:
        detected = "core"
    else:
        raise ResolveError("target package directly depends on neither flowr nor flowr_dart")

    if requested == "auto":
        return detected
    if requested == "flutter" and detected != "flutter":
        raise ResolveError(
            "Flutter instructions are unavailable: the target package is flowr_dart-only"
        )
    if requested == "core":
        return "core"
    return requested


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the mapping-only config subset used by this resolver."""

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("\t"):
            raise ResolveError(f"config.yaml:{line_number}: tabs are not supported")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0 or ":" not in raw_line:
            raise ResolveError(f"config.yaml:{line_number}: expected two-space key: value")
        key, value = raw_line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip():
            parent[key] = value.strip().strip("\"'")
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def load_config(config_path: Path) -> tuple[dict[str, Any], str | None]:
    """Load the optional repository-owned profile configuration."""

    if not config_path.exists():
        return {}, None
    text = config_path.read_text(encoding="utf-8")
    parsed = parse_pubspec(text)
    if not parsed:
        parsed = parse_simple_yaml(text)
    return parsed, text


def resolve_profile(
    task: str, config_root: Path
) -> tuple[str, Path | None, str, str | None]:
    """Return an optional Flutter-only project profile reference."""

    if task == "core":
        return "generic", None, "", None
    config_path = config_root / "config.yaml"
    config, config_text = load_config(config_path)
    if not config:
        return "generic", None, "", config_text
    if config.get("schema") != "flowr-usage.config.v1":
        raise ResolveError("config.yaml schema must be flowr-usage.config.v1")
    profile = str(config.get("profile", "generic"))
    tasks = config.get("tasks")
    if not isinstance(tasks, dict):
        raise ResolveError("config.yaml tasks must be a mapping")
    flutter = tasks.get("flutter")
    if not isinstance(flutter, dict):
        raise ResolveError("config.yaml tasks.flutter must be a mapping")
    raw_path = flutter.get("profile")
    if not isinstance(raw_path, str) or not raw_path:
        raise ResolveError("config.yaml tasks.flutter.profile is required")
    profile_path = (config_root / raw_path).resolve()
    if not is_relative_to(profile_path, config_root.resolve()):
        raise ResolveError("config.yaml tasks.flutter.profile escapes skills-config")
    if not profile_path.is_file():
        raise ResolveError(f"Flutter profile not found: {profile_path}")
    return profile, profile_path, profile_path.read_text(encoding="utf-8").strip(), config_text


def resolve_task(args: argparse.Namespace) -> ResolvedTask:
    """Resolve the base instruction set and any allowed project profile."""

    start = (args.cwd or Path.cwd()).resolve()
    repo_root = find_repo_root(start)
    skill_root = repo_root / ".agents" / "skills" / SKILL_NAME
    config_root = repo_root / ".agents" / "skills-config" / SKILL_NAME
    package = inspect_package(find_pubspec(start, repo_root))
    task = select_task(args.task, package)

    core_path = skill_root / "references/core.md"
    if not core_path.is_file():
        raise ResolveError(f"core instructions not found: {core_path}")
    core_text = core_path.read_text(encoding="utf-8").strip()
    sources = {"core": display_path(core_path, repo_root)}
    parts = ["# Resolved FlowR Instructions", "", f"- Task: `{task}`"]

    flutter_text = ""
    if task == "flutter":
        flutter_path = skill_root / "references/flutter.md"
        if not flutter_path.is_file():
            raise ResolveError(f"Flutter instructions not found: {flutter_path}")
        flutter_text = flutter_path.read_text(encoding="utf-8").strip()
        sources["flutter"] = display_path(flutter_path, repo_root)

    profile, profile_path, profile_text, config_text = resolve_profile(task, config_root)
    if profile_path is not None:
        sources["profile"] = display_path(profile_path, repo_root)
        sources["project_config"] = display_path(config_root / "config.yaml", repo_root)

    hash_input = {
        "version": RESOLVER_VERSION,
        "task": task,
        "profile": profile,
        "package": display_path(package.pubspec_path, repo_root),
        "core": core_text,
        "flutter": flutter_text,
        "profile_text": profile_text,
        "config": config_text or "",
    }
    digest = hashlib.sha256(
        json.dumps(hash_input, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:7]
    instructions_id = f"{SKILL_NAME}/{task}@{digest}"
    cache_path = repo_root / ".agents/.cache" / SKILL_NAME / f"{task}.{digest}.md"

    parts.extend(
        [
            f"- Profile: `{profile}`",
            f"- Instructions ID: `{instructions_id}`",
            f"- Target package: `{display_path(package.pubspec_path, repo_root)}`",
            "",
            "## Core Instructions",
            "",
            core_text,
        ]
    )
    if flutter_text:
        parts.extend(["", "## Flutter Instructions", "", flutter_text])
    if profile_text:
        parts.extend(["", "## Project Profile Instructions", "", profile_text])
    return ResolvedTask(
        task=task,
        profile=profile,
        instructions_id=instructions_id,
        instructions_text="\n".join(parts).rstrip() + "\n",
        cache_path=cache_path,
        sources=sources,
        package=package,
    )


def ensure_cache(resolved: ResolvedTask) -> None:
    """Write the deterministic cache for the manifest reader."""

    resolved.cache_path.parent.mkdir(parents=True, exist_ok=True)
    resolved.cache_path.write_text(resolved.instructions_text, encoding="utf-8")


def render_manifest(resolved: ResolvedTask, repo_root: Path) -> str:
    """Render a compact deterministic manifest."""

    lines = [
        f"skill: {SKILL_NAME}",
        f"task: {resolved.task}",
        f"profile: {resolved.profile}",
        "status: ready",
        f"instructions_id: {resolved.instructions_id}",
        f"target_package: {display_path(resolved.package.pubspec_path, repo_root)}",
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
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=TASKS, default="auto")
    parser.add_argument("--cwd", type=Path, help="Target package directory")
    parser.add_argument("--emit", choices=("manifest", "instructions"), default="manifest")
    return parser.parse_args()


def main() -> int:
    """Resolve and print instructions or a small manifest."""

    args = parse_args()
    try:
        resolved = resolve_task(args)
        if args.emit == "instructions":
            print(resolved.instructions_text, end="")
        else:
            ensure_cache(resolved)
            print(render_manifest(resolved, find_repo_root(args.cwd or Path.cwd())), end="")
        return 0
    except Exception as error:
        print(f"skill: {SKILL_NAME}\nstatus: blocked\nreason: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
