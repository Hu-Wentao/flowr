#!/usr/bin/env python3
"""Create and verify a native Flutter project for ACDD contract development."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


DEFAULT_PLATFORMS = ("android", "ios")
SUPPORTED_PLATFORMS = frozenset(DEFAULT_PLATFORMS)
RUNTIME_DEPENDENCIES = (
    "flowr",
    "fr_acdd",
    "fr_mvvm_theme",
    "fr_mvvm_locale",
    "fr_mvvm_env",
    "fr_storage",
    "go_router",
    "freezed_annotation",
    "flutter_localizations:{sdk: flutter}",
)
DEV_DEPENDENCIES = ("dev:freezed", "dev:build_runner")
TEMPLATE_FILES = {
    "lib/main.dart.tmpl": "lib/main.dart",
    "lib/application.dart.tmpl": "lib/application.dart",
    "lib/app_router.dart.tmpl": "lib/app_router.dart",
    "lib/core/app_providers.dart.tmpl": "lib/core/app_providers.dart",
    "lib/core/app_env.dart.tmpl": "lib/core/app_env.dart",
    "lib/core/app_locale.dart.tmpl": "lib/core/app_locale.dart",
    "lib/core/app_theme.dart.tmpl": "lib/core/app_theme.dart",
    "test/application_test.dart.tmpl": "test/application_test.dart",
}
EMPTY_DIRECTORY_MARKERS = ("lib/app/.gitkeep", "lib/components/.gitkeep")
VERIFY_COMMANDS = (
    ("format", ("fvm", "dart", "format", ".")),
    ("analyze", ("fvm", "flutter", "analyze")),
    ("test", ("fvm", "flutter", "test")),
)


class ScaffoldError(ValueError):
    """Raised when scaffold inputs or execution are invalid."""


@dataclass(frozen=True)
class ScaffoldConfig:
    """Resolved scaffold inputs."""

    name: str
    output: Path
    org: str
    platforms: tuple[str, ...]
    description: str
    apply: bool


@dataclass(frozen=True)
class CommandStep:
    """One external command in the scaffold workflow."""

    stage: str
    command: tuple[str, ...]
    cwd: Path


CommandRunner = Callable[[CommandStep], None]
InputReader = Callable[[str], str]


def prompt_value(
    label: str,
    *,
    input_reader: InputReader,
    default: str | None = None,
) -> str:
    """Prompt until a non-empty value is returned, applying an optional default."""

    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input_reader(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        print(f"{label} is required.", file=sys.stderr)


def resolve_value(
    value: str | None,
    *,
    option: str,
    label: str,
    interactive: bool,
    input_reader: InputReader,
    default: str | None = None,
) -> str:
    """Resolve one CLI value from input, prompt, or a default."""

    if value is not None and value.strip():
        return value.strip()
    if interactive:
        return prompt_value(label, input_reader=input_reader, default=default)
    if default is not None:
        return default
    raise ScaffoldError(
        f"missing {option}; pass it explicitly or run in an interactive terminal"
    )


def validate_project_name(value: str) -> str:
    """Validate a Dart package name."""

    if not re.fullmatch(r"[a-z][a-z0-9_]*[a-z0-9]|[a-z]", value):
        raise ScaffoldError(
            "project name must be lower_snake_case, start with a letter, "
            "and end with a letter or digit"
        )
    return value


def validate_org(value: str) -> str:
    """Validate a reverse-domain organization identifier."""

    if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+", value):
        raise ScaffoldError(
            "org must be a lowercase reverse-domain identifier such as com.example"
        )
    return value


def parse_platforms(value: str) -> tuple[str, ...]:
    """Parse, normalize, and validate a comma-separated platform list."""

    platforms = tuple(
        dict.fromkeys(part.strip() for part in value.split(",") if part.strip())
    )
    if not platforms:
        return DEFAULT_PLATFORMS
    unsupported = sorted(set(platforms) - SUPPORTED_PLATFORMS)
    if unsupported:
        joined = ", ".join(unsupported)
        raise ScaffoldError(
            f"unsupported platform(s): {joined}; acdd_scaffold currently supports "
            "android and ios only because fr_storage is enabled by default"
        )
    return platforms


def ensure_empty_target(output: Path) -> None:
    """Reject targets that are files or non-empty directories."""

    if not output.exists():
        return
    if not output.is_dir():
        raise ScaffoldError(f"output exists and is not a directory: {output}")
    if next(output.iterdir(), None) is not None:
        raise ScaffoldError(f"output directory is not empty: {output}")


def build_config(
    args: argparse.Namespace,
    *,
    input_reader: InputReader = input,
    interactive: bool | None = None,
) -> ScaffoldConfig:
    """Resolve prompts, defaults, and validated scaffold configuration."""

    is_interactive = sys.stdin.isatty() if interactive is None else interactive
    name = validate_project_name(
        resolve_value(
            args.name,
            option="--name",
            label="Project name",
            interactive=is_interactive,
            input_reader=input_reader,
        )
    )
    output_raw = resolve_value(
        args.output,
        option="--output",
        label="Output directory",
        interactive=is_interactive,
        input_reader=input_reader,
        default=name,
    )
    org = validate_org(
        resolve_value(
            args.org,
            option="--org",
            label="Organization",
            interactive=is_interactive,
            input_reader=input_reader,
        )
    )
    platforms_raw = resolve_value(
        args.platforms,
        option="--platforms",
        label="Platforms",
        interactive=is_interactive,
        input_reader=input_reader,
        default=",".join(DEFAULT_PLATFORMS),
    )
    description = (
        args.description.strip()
        if args.description and args.description.strip()
        else "An ACDD contract-first Flutter application."
    )
    output = Path(output_raw).expanduser().resolve()
    ensure_empty_target(output)
    return ScaffoldConfig(
        name=name,
        output=output,
        org=org,
        platforms=parse_platforms(platforms_raw),
        description=description,
        apply=args.apply,
    )


def build_command_steps(config: ScaffoldConfig) -> tuple[CommandStep, ...]:
    """Build every external command in deterministic execution order."""

    create = CommandStep(
        stage="create",
        command=(
            "fvm",
            "flutter",
            "create",
            "--empty",
            "--org",
            config.org,
            "--project-name",
            config.name,
            "--platforms",
            ",".join(config.platforms),
            "--description",
            config.description,
            str(config.output),
        ),
        cwd=Path.cwd().resolve(),
    )
    runtime = CommandStep(
        stage="dependencies",
        command=("fvm", "flutter", "pub", "add", *RUNTIME_DEPENDENCIES),
        cwd=config.output,
    )
    dev = CommandStep(
        stage="dev_dependencies",
        command=("fvm", "flutter", "pub", "add", *DEV_DEPENDENCIES),
        cwd=config.output,
    )
    verify = tuple(
        CommandStep(stage=stage, command=command, cwd=config.output)
        for stage, command in VERIFY_COMMANDS
    )
    return (create, runtime, dev, *verify)


def render_command(command: Sequence[str]) -> str:
    """Render a command for human review without executing it."""

    return shlex.join(command)


def render_plan(config: ScaffoldConfig) -> str:
    """Render the complete dry-run plan."""

    steps = build_command_steps(config)
    lines = [
        "ACDD scaffold plan",
        f"  name: {config.name}",
        f"  output: {config.output}",
        f"  org: {config.org}",
        f"  platforms: {','.join(config.platforms)}",
        f"  description: {config.description}",
        "",
        "commands:",
    ]
    for step in steps:
        lines.append(f"  [{step.stage}] {render_command(step.command)}")
    lines.extend(["", "generated files:"])
    for destination in (*TEMPLATE_FILES.values(), *EMPTY_DIRECTORY_MARKERS):
        lines.append(f"  - {destination}")
    lines.extend(
        [
            "",
            "No files were written. Re-run with --apply after approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def default_command_runner(step: CommandStep) -> None:
    """Run one command with live output and stable stage reporting."""

    print(f"[{step.stage}] {render_command(step.command)}", flush=True)
    try:
        subprocess.run(step.command, cwd=step.cwd, check=True)
    except FileNotFoundError as error:
        raise ScaffoldError(
            f"stage {step.stage} failed: command not found: {step.command[0]}"
        ) from error
    except subprocess.CalledProcessError as error:
        raise ScaffoldError(
            f"stage {step.stage} failed with exit code {error.returncode}: "
            f"{render_command(step.command)}"
        ) from error


def render_templates(config: ScaffoldConfig) -> None:
    """Render bundled templates and empty directory markers into the project."""

    template_root = Path(__file__).resolve().parents[1] / "assets" / "acdd_scaffold"
    replacements = {"{{PROJECT_NAME}}": config.name}
    for source_name, destination_name in TEMPLATE_FILES.items():
        source = template_root / source_name
        if not source.is_file():
            raise ScaffoldError(f"template not found: {source}")
        text = source.read_text(encoding="utf-8")
        for marker, value in replacements.items():
            text = text.replace(marker, value)
        if re.search(r"\{\{[A-Z0-9_]+\}\}", text):
            raise ScaffoldError(f"unresolved template marker in {source}")
        destination = config.output / destination_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    default_test = config.output / "test" / "widget_test.dart"
    if default_test.exists():
        default_test.unlink()
    for marker_name in EMPTY_DIRECTORY_MARKERS:
        marker = config.output / marker_name
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")


def apply_scaffold(
    config: ScaffoldConfig,
    *,
    command_runner: CommandRunner = default_command_runner,
) -> None:
    """Create, render, and verify the scaffold."""

    ensure_empty_target(config.output)
    steps = build_command_steps(config)
    for step in steps[:3]:
        command_runner(step)
    print("[templates] render ACDD application files", flush=True)
    render_templates(config)
    for step in steps[3:]:
        command_runner(step)
    print(f"ACDD scaffold ready: {config.output}")
    print("Next contract directory: lib/app/<route-segment>/")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", help="Dart project name; prompted when omitted")
    parser.add_argument("--output", help="Target directory; defaults to project name")
    parser.add_argument(
        "--org",
        help="Reverse-domain organization; prompted when omitted",
    )
    parser.add_argument(
        "--platforms",
        help="Comma-separated platforms; defaults to android,ios",
    )
    parser.add_argument("--description", help="Flutter project description")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved plan without writing (default)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Create and verify the project",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    try:
        config = build_config(parse_args(argv))
        if not config.apply:
            print(render_plan(config), end="")
            return 0
        apply_scaffold(config)
        return 0
    except (EOFError, KeyboardInterrupt):
        print("acdd_scaffold cancelled", file=sys.stderr)
        return 130
    except ScaffoldError as error:
        print(f"acdd_scaffold blocked: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
