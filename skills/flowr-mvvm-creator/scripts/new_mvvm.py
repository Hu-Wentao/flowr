#!/usr/bin/env python3
"""Generate a minimal FlowR MVVM starter file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def pascal_case(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    if not parts:
        raise ValueError("name must contain at least one letter or number")
    return "".join(part[:1].upper() + part[1:] for part in parts)


def method_template(name: str) -> str:
    model = f"{name}Model"
    vm = f"{name}ViewModel"
    return f"""import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';

class {model} {{
  final int value;
  final bool loading;

  const {model}({{
    this.value = 0,
    this.loading = false,
  }});

  {model} copyWith({{
    int? value,
    bool? loading,
  }}) =>
      {model}(
        value: value ?? this.value,
        loading: loading ?? this.loading,
      );
}}

class {vm} extends FrViewModel<{model}> {{
  {vm}() : super(const {model}());

  FutureOr<{model}?> increment() => update(
        (old) => old.copyWith(value: old.value + 1),
      );
}}
"""


def bloc_template(name: str) -> str:
    model = f"{name}Model"
    vm = f"{name}ViewModel"
    event = f"{name}Event"
    incremented = f"{name}Incremented"
    return f"""import 'package:flowr/flowr_mvvm.dart';

sealed class {event} {{
  const {event}();
}}

class {incremented} extends {event} {{
  const {incremented}();
}}

class {model} {{
  final int value;

  const {model}({{this.value = 0}});

  {model} copyWith({{int? value}}) => {model}(
        value: value ?? this.value,
      );
}}

class {vm} extends FrBlocViewModel<{event}, {model}> {{
  {vm}() : super(const {model}()) {{
    on<{incremented}>(
      (event, emit) => emit(state.copyWith(value: state.value + 1)),
    );
  }}
}}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Feature/class prefix, for example Counter or user-profile.")
    parser.add_argument("--mode", choices=("method", "bloc"), default="method")
    parser.add_argument("--output", type=Path, help="Write to this file instead of stdout.")
    parser.add_argument("--force", action="store_true", help="Overwrite --output when it already exists.")
    args = parser.parse_args()

    name = pascal_case(args.name)
    content = method_template(name) if args.mode == "method" else bloc_template(name)

    if args.output is None:
        print(content, end="")
        return 0

    output = args.output
    if output.exists() and not args.force:
        parser.error(f"{output} already exists; pass --force to overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"wrote {output}")
    print(f"next: fvm dart format {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
