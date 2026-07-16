#!/usr/bin/env python3
"""Collect project BFF contracts into a deterministic ZIP archive."""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import tempfile
import zipfile
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = {".git", ".dart_tool", "build"}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(ValueError):
    """Raised when BFF contracts cannot be packaged safely."""


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def is_excluded(relative_path: Path, patterns: tuple[str, ...]) -> bool:
    if any(part in DEFAULT_EXCLUDED_DIRS for part in relative_path.parts[:-1]):
        return True
    if relative_path.parts[:2] == (".agents", ".cache"):
        return True
    value = relative_path.as_posix()
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def collect_bff_files(
    project_root: Path, *, excludes: tuple[str, ...]
) -> list[tuple[Path, Path]]:
    """Return sorted `(source, project-relative path)` entries."""

    root = project_root.resolve()
    if not root.is_dir():
        raise PackageError(f"project root does not exist or is not a directory: {root}")
    entries: list[tuple[Path, Path]] = []
    for candidate in root.rglob("*.bff.md"):
        relative = candidate.relative_to(root)
        if is_excluded(relative, excludes):
            continue
        if candidate.is_symlink():
            raise PackageError(f"refusing to package symlinked BFF contract: {relative}")
        resolved = candidate.resolve()
        if not is_relative_to(resolved, root):
            raise PackageError(f"BFF contract escapes project root: {relative}")
        if not candidate.is_file():
            continue
        entries.append((resolved, relative))
    entries.sort(key=lambda entry: entry[1].as_posix())
    if not entries:
        raise PackageError(f"no *.bff.md contracts found under {root}")
    return entries


def write_archive(entries: list[tuple[Path, Path]], output: Path) -> None:
    """Write a stable archive to a temporary file and replace on success."""

    output = output.resolve()
    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for source, relative in entries:
                info = zipfile.ZipInfo(relative.as_posix(), date_time=ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source.read_bytes(), compresslevel=9)
        temporary.replace(output)
    except Exception as error:
        raise PackageError(
            f"failed to create BFF archive; existing output was preserved: {error}"
        ) from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/bff-contracts.zip"),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional project-relative glob to exclude. May be repeated.",
    )
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output = args.output
    if not output.is_absolute():
        output = project_root / output
    try:
        if output.suffix.lower() != ".zip":
            raise PackageError(f"BFF archive output must use the .zip suffix: {output}")
        excludes = tuple(args.exclude)
        entries = collect_bff_files(project_root, excludes=excludes)
        write_archive(entries, output)
    except PackageError as error:
        print(f"package error: {error}", file=sys.stderr)
        return 2
    print(f"BFF archive: {output.resolve()}")
    print(f"contracts: {len(entries)}")
    for _, relative in entries:
        print(f"  - {relative.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
