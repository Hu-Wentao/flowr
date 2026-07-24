#!/usr/bin/env python3
"""Plan and safely extract a pure shared Dart Widget from an existing View."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


OWNERSHIP_SIGNALS = (
    "FrProvider",
    "ViewModel",
    "FrBloc",
    "@FrState",
    " Service",
    ".add(",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_class(source: str, symbol: str) -> tuple[int, int, str]:
    match = re.search(rf"(?m)^class\s+{re.escape(symbol)}\b", source)
    if not match:
        raise ValueError(f"class `{symbol}` was not found")
    open_brace = source.find("{", match.end())
    if open_brace < 0:
        raise ValueError(f"class `{symbol}` has no body")
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                while end < len(source) and source[end] in " \t\r\n":
                    end += 1
                return match.start(), end, source[match.start() : end]
    raise ValueError(f"class `{symbol}` has an unclosed body")


def package_name(root: Path) -> str:
    pubspec = root / "pubspec.yaml"
    match = re.search(r"(?m)^name:\s*([^\s#]+)", read(pubspec)) if pubspec.exists() else None
    if not match:
        raise ValueError("project root must contain pubspec.yaml with package name")
    return match.group(1)


def existing_matches(root: Path, capability: str) -> list[str]:
    result: list[str] = []
    for base in (root / "lib/widgets", root / "lib/components"):
        if not base.is_dir():
            continue
        for path in base.rglob("*.dart"):
            text = read(path)
            if "Capabilities:" in text and capability.casefold() in text.casefold():
                result.append(str(path.relative_to(root)))
    return sorted(result)


def import_line(package: str, name: str) -> str:
    return f"import 'package:{package}/widgets/{name}.dart';"


def add_import(source: str, statement: str) -> str:
    if statement in source:
        return source
    imports = list(re.finditer(r"(?m)^import\s+[^;]+;\s*$", source))
    if imports:
        end = imports[-1].end()
        return source[:end] + "\n" + statement + source[end:]
    return statement + "\n\n" + source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--consumer", type=Path, action="append", default=[])
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--public-name")
    parser.add_argument("--name", required=True, help="snake_case shared Widget module name")
    parser.add_argument("--capability", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    source_path = (root / args.source).resolve() if not args.source.is_absolute() else args.source.resolve()
    consumers = [(root / path).resolve() if not path.is_absolute() else path.resolve() for path in args.consumer]
    target = root / "lib/widgets" / f"{args.name}.dart"
    if not source_path.is_file() or not source_path.is_relative_to(root):
        parser.error("--source must be an existing file inside --project-root")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.name):
        parser.error("--name must be snake_case")
    try:
        source = read(source_path)
        start, end, body = extract_class(source, args.symbol)
        public_name = args.public_name or args.symbol
        signals = [signal for signal in OWNERSHIP_SIGNALS if signal in body]
        private_helpers = re.findall(r"(?m)^class\s+(_[A-Za-z0-9_]+)\b", body)
        manifest = {
            "status": "ready" if not signals and not private_helpers else "blocked",
            "classification": "widget" if not signals else "component",
            "source": str(source_path.relative_to(root)),
            "consumers": [str(path.relative_to(root)) for path in consumers],
            "symbol": args.symbol,
            "publicName": public_name,
            "target": str(target.relative_to(root)),
            "capability": args.capability,
            "existingMatches": existing_matches(root, args.capability),
            "ownershipSignals": signals,
            "privateHelpers": private_helpers,
            "apply": args.apply,
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        if signals:
            raise ValueError("component-owned UI requires the gen_component contract workflow")
        if private_helpers:
            raise ValueError("private helper classes require an explicit manual extraction")
        if args.apply:
            if target.exists():
                raise ValueError(f"target already exists: {target.relative_to(root)}")
            invalid_consumers = [
                consumer
                for consumer in consumers
                if not consumer.is_file() or not consumer.is_relative_to(root)
            ]
            if invalid_consumers:
                raise ValueError(
                    "consumer must be an existing file inside project: "
                    + str(invalid_consumers[0])
                )
            package = package_name(root)
            imports = "\n".join(re.findall(r"(?m)^import\s+[^;]+;\s*$", source))
            moved = re.sub(rf"\b{re.escape(args.symbol)}\b", public_name, body)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "/// Capabilities:\n"
                f"/// - {args.capability}.\n"
                "/// Public Widgets:\n"
                f"/// - [{public_name}] — 共享的{args.capability}展示与交互入口。\n\n"
                + (imports + "\n\n" if imports else "")
                + moved,
                encoding="utf-8",
            )
            replacement = source[:start] + source[end:]
            replacement = re.sub(rf"\b{re.escape(args.symbol)}\b", public_name, replacement)
            statement = import_line(package, args.name)
            source_path.write_text(add_import(replacement, statement), encoding="utf-8")
            for consumer in consumers:
                text = re.sub(rf"\b{re.escape(args.symbol)}\b", public_name, read(consumer))
                consumer.write_text(add_import(text, statement), encoding="utf-8")
    except ValueError as error:
        print(f"blocked: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
