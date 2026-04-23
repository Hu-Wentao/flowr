#!/usr/bin/env python3
"""Generate FlowR MVVM Dart modules.

Examples:
  python generate_mvvm.py profile --field username:String=guest --field avatarUrl:String --with-view
  python generate_mvvm.py counter --state scalar --scalar-type int --scalar-initial 0
  python generate_mvvm.py weather --field city:String --field temperature:int=0 --with-service
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Field:
    name: str
    dart_type: str
    default: str | None

    @property
    def pascal_name(self) -> str:
        return to_pascal_case(self.name)


def to_words(value: str) -> list[str]:
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return [w for w in re.split(r"[^A-Za-z0-9]+", words) if w]


def to_snake_case(value: str) -> str:
    return "_".join(w.lower() for w in to_words(value))


def to_pascal_case(value: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in to_words(value))


def to_camel_case(value: str) -> str:
    pascal = to_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def parse_field(raw: str) -> Field:
    match = re.fullmatch(
        r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?\s*",
        raw,
    )
    if not match:
        raise argparse.ArgumentTypeError(
            "field must use name:Type or name:Type=default",
        )
    name, dart_type, default = match.groups()
    return Field(name=name, dart_type=dart_type.strip(), default=default)


def quote_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def default_literal(dart_type: str) -> str:
    clean = dart_type.strip()
    nullable = clean.endswith("?")
    base = clean[:-1] if nullable else clean
    if nullable:
        return "null"
    if base == "String":
        return "''"
    if base == "int":
        return "0"
    if base == "double":
        return "0"
    if base == "num":
        return "0"
    if base == "bool":
        return "false"
    if base.startswith("List<"):
        return f"const <{base[5:-1]}>[]"
    if base.startswith("Set<"):
        return f"const <{base[4:-1]}>{{}}"
    if base.startswith("Map<"):
        return f"const <{base[4:-1]}>{{}}"
    return f"{base}()"


def normalize_default(field: Field) -> str:
    if field.default is None:
        return default_literal(field.dart_type)
    value = field.default.strip()
    if field.dart_type.rstrip("?") == "String":
        if value.startswith(("'", '"')) or value == "null":
            return value
        return quote_string(value)
    return value


def is_const_literal(value: str) -> bool:
    return (
        value == "null"
        or value in {"true", "false"}
        or value.startswith(("'", '"', "const "))
        or re.fullmatch(r"-?\d+(\.\d+)?", value) is not None
    )


def indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def constructor_args(fields: list[Field], force_defaults: bool) -> str:
    lines = []
    for field in fields:
        default = normalize_default(field)
        if force_defaults or field.default is not None:
            lines.append(f"this.{field.name} = {default},")
        else:
            lines.append(f"required this.{field.name},")
    return "\n".join(lines)


def init_model_literal(model_name: str, fields: list[Field], const_ok: bool) -> str:
    prefix = "const " if const_ok else ""
    args = ", ".join(f"{f.name}: {normalize_default(f)}" for f in fields)
    return f"{prefix}{model_name}({args})"


def build_model(prefix: str, fields: list[Field], state: str, di: bool) -> str:
    if state == "scalar":
        return ""

    model_name = f"{prefix}Model"
    immutable = state == "immutable"
    final_kw = "final " if immutable else ""
    const_kw = "const " if immutable else ""
    force_defaults = di

    declarations = "\n".join(
        f"  {final_kw}{field.dart_type} {field.name};" for field in fields
    )
    ctor = constructor_args(fields, force_defaults=force_defaults)
    copy_params = "\n".join(f"    {field.dart_type}? {field.name}," for field in fields)
    copy_values = "\n".join(
        f"        {field.name}: {field.name} ?? this.{field.name},"
        for field in fields
    )
    to_string_fields = ", ".join(f"{f.name}: ${f.name}" for f in fields)

    copy_with = ""
    if immutable:
        copy_with = f"""

  {model_name} copyWith({{
{copy_params}
  }}) =>
      {model_name}(
{copy_values}
      );"""

    return f"""class {model_name} {{
{declarations}

  {const_kw}{model_name}({{
{indent(ctor, 4)}
  }});{copy_with}

  @override
  String toString() => '{model_name}({to_string_fields})';
}}
"""


def build_update_methods(prefix: str, fields: list[Field], state: str) -> str:
    if state == "scalar":
        return """  void setValue(TODO value) => update((old) => value);
"""

    methods = []
    immutable = state == "immutable"
    for field in fields:
        method = f"update{field.pascal_name}"
        if immutable:
            body = f"""  void {method}({field.dart_type} {field.name}) => update((old) {{
        skpIf({field.name} == old.{field.name}, '{field.name} unchanged');
        return old.copyWith({field.name}: {field.name});
      }});"""
        else:
            body = f"""  void {method}({field.dart_type} {field.name}) => update((old) {{
        skpIf({field.name} == old.{field.name}, '{field.name} unchanged');
        return old..{field.name} = {field.name};
      }});"""
        methods.append(body)

    methods.append(
        f"""  Future<void> refresh() async => update(
        (old) async {{
          logger('refresh {to_snake_case(prefix)}');
          return old;
        }},
        mutexTag: '{to_snake_case(prefix)}_refresh',
      );""",
    )
    return "\n\n".join(methods)


def build_view_model(
    prefix: str,
    fields: list[Field],
    state: str,
    scalar_type: str,
    scalar_initial: str,
    di: bool,
    with_service: bool,
) -> str:
    vm_name = f"{prefix}ViewModel"
    service_name = f"{prefix}ApiService"
    if state == "scalar":
        model_type = scalar_type
        init_value = scalar_initial
    else:
        model_type = f"{prefix}Model"
        const_ok = state == "immutable" and all(
            is_const_literal(normalize_default(field)) for field in fields
        )
        init_value = init_model_literal(model_type, fields, const_ok=const_ok)

    annotation = "@lazySingleton\n" if di else ""
    service_field = f"  final {service_name}? api;\n\n" if with_service else ""

    if di:
        ctor_params = "{this.api}" if with_service else ""
        ctor = f"  {vm_name}({ctor_params});"
        init = f"  @override\n  {model_type} get initValue => {init_value};"
    else:
        ctor_params = "{required this.initValue"
        if with_service:
            ctor_params += ", this.api"
        ctor_params += "}"
        ctor = f"  {vm_name}({ctor_params});"
        init = f"  @override\n  final {model_type} initValue;"

    methods = build_update_methods(prefix, fields, state)
    if state == "scalar":
        methods = methods.replace("TODO", scalar_type)

    return f"""{annotation}class {vm_name} extends FrViewModel<{model_type}> {{
{service_field}{init}

{ctor}

{methods}
}}
"""


def build_view(
    prefix: str,
    fields: list[Field],
    state: str,
    scalar_type: str,
    scalar_initial: str,
    di: bool,
) -> str:
    view_name = f"{prefix}View"
    vm_name = f"{prefix}ViewModel"
    if state == "scalar":
        model_type = scalar_type
        init_arg = scalar_initial
        text_expr = "s.data.toString()"
    else:
        model_type = f"{prefix}Model"
        const_ok = state == "immutable" and all(
            is_const_literal(normalize_default(field)) for field in fields
        )
        init_arg = init_model_literal(model_type, fields, const_ok=const_ok)
        first = fields[0].name if fields else "toString()"
        text_expr = f"s.data.{first}.toString()"

    if di:
        provider_open = f"FrProvider<{vm_name}>.di("
    else:
        provider_open = f"""FrProvider(
      (c) => {vm_name}(
        initValue: {init_arg},
      ),"""

    return f"""class {view_name} extends StatelessWidget {{
  const {view_name}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return {provider_open}
      child: FrView<{vm_name}, {model_type}>(
        builder: (context, s, child) => Text({text_expr}),
      ),
    );
  }}
}}
"""


def build_service(prefix: str) -> str:
    service_name = f"{prefix}ApiService"
    feature = to_snake_case(prefix)
    return f"""import 'package:flowr/flowr_mvvm.dart';

class {service_name} extends FrService {{
  Future<void> fetch() async {{
    await runCatching(
      () async {{
        logger('fetch {feature}');
        // TODO: call API/client/repository.
      }},
      mutexTag: '{feature}_fetch',
    );
  }}
}}
"""


def build_vm_file(args: argparse.Namespace, fields: list[Field]) -> str:
    prefix = args.class_prefix or to_pascal_case(args.feature)
    imports = ["import 'package:flowr/flowr_mvvm.dart';"]
    if args.with_view:
        imports.append("import 'package:flutter/material.dart';")
    if args.with_service:
        service_file = f"{to_snake_case(args.feature)}_api.srv.dart"
        imports.append(f"import '{service_file}';")

    model = build_model(prefix, fields, args.state, args.di)
    vm = build_view_model(
        prefix=prefix,
        fields=fields,
        state=args.state,
        scalar_type=args.scalar_type,
        scalar_initial=args.scalar_initial,
        di=args.di,
        with_service=args.with_service,
    )
    view = (
        build_view(
            prefix,
            fields,
            args.state,
            args.scalar_type,
            args.scalar_initial,
            args.di,
        )
        if args.with_view
        else ""
    )
    return "\n".join(imports) + "\n\n" + "\n".join(p for p in [model, vm, view] if p)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FlowR MVVM Dart code.")
    parser.add_argument("feature", help="feature/module name, e.g. profile")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="target directory; defaults to lib/service/<feature>",
    )
    parser.add_argument(
        "--state",
        choices=["immutable", "mutable", "scalar"],
        default="immutable",
        help="state shape to generate",
    )
    parser.add_argument(
        "--field",
        action="append",
        type=parse_field,
        default=[],
        help="state field as name:Type or name:Type=default",
    )
    parser.add_argument("--scalar-type", default="int", help="Dart scalar type")
    parser.add_argument("--scalar-initial", default="0", help="Dart scalar initial value")
    parser.add_argument("--class-prefix", default=None, help="class prefix override")
    parser.add_argument("--with-view", action="store_true", help="include simple View")
    parser.add_argument("--with-service", action="store_true", help="create API service")
    parser.add_argument("--di", action="store_true", help="generate injectable/GetIt VM")
    parser.add_argument("--dry-run", action="store_true", help="print files without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    feature_dir = to_snake_case(args.feature)
    out_dir = Path(args.output_dir or Path("lib") / "service" / feature_dir)

    if args.state != "scalar" and not args.field:
        raise SystemExit("at least one --field is required for model state")

    vm_file = out_dir / f"{feature_dir}.vm.dart"
    files = {vm_file: build_vm_file(args, args.field)}
    if args.with_service:
        prefix = args.class_prefix or to_pascal_case(args.feature)
        files[out_dir / f"{feature_dir}_api.srv.dart"] = build_service(prefix)

    if args.dry_run:
        for path, content in files.items():
            print(f"--- {path} ---")
            print(content)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.write_text(content)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
