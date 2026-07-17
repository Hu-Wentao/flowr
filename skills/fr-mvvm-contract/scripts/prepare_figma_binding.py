#!/usr/bin/env python3
"""Prepare deterministic Figma node metadata for a component contract."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from contract_core import ContractError
from contract_parser import parse_component


FIGMA_NAMESPACE = "flowr"
FIGMA_CONTRACT_KEY = "contract_path"
NODE_ID = re.compile(r"[0-9]+(?::[0-9]+)*")


@dataclass(frozen=True)
class FigmaContractBinding:
    fileKey: str
    nodeId: str
    figmaUrl: str
    componentName: str
    contractPath: str
    namespace: str
    key: str
    writeCode: str
    verifyCode: str


def parse_figma_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        hostname == "figma.com" or hostname.endswith(".figma.com")
    ):
        raise ContractError("Figma URL must be an https://figma.com URL")

    parts = [unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] not in {"design", "file"}:
        raise ContractError("Figma URL must target a design or file")
    file_key = parts[1]
    if len(parts) >= 4 and parts[2] == "branch":
        file_key = parts[3]

    values = parse_qs(parsed.query).get("node-id", [])
    if len(values) != 1 or not values[0]:
        raise ContractError("Figma URL must contain exactly one concrete node-id")
    node_id = values[0].replace("-", ":")
    if not NODE_ID.fullmatch(node_id):
        raise ContractError(f"invalid Figma node-id: {values[0]}")
    return file_key, node_id


def _contract_path(project_root: Path, contract_file: Path) -> tuple[Path, str]:
    root = project_root.resolve()
    candidate = contract_file if contract_file.is_absolute() else root / contract_file
    contract = candidate.resolve()
    if not contract.is_file():
        raise ContractError(f"component contract does not exist: {contract}")
    if not contract.name.endswith(".c.dart"):
        raise ContractError("Figma binding source must be a .c.dart contract")
    try:
        relative = contract.relative_to(root)
    except ValueError as error:
        raise ContractError("component contract must be inside the project root") from error
    return contract, relative.as_posix()


def _component_file(contract_file: Path) -> Path:
    return contract_file.with_name(
        contract_file.name.removesuffix(".c.dart") + ".dart"
    )


def _figma_code(node_id: str, contract_path: str) -> tuple[str, str]:
    node = json.dumps(node_id)
    path = json.dumps(contract_path)
    namespace = json.dumps(FIGMA_NAMESPACE)
    key = json.dumps(FIGMA_CONTRACT_KEY)
    lookup = (
        f"const node = await figma.getNodeByIdAsync({node});\n"
        f"if (!node) throw new Error('Figma node not found: ' + {node});\n"
    )
    write = (
        lookup
        + f"node.setSharedPluginData({namespace}, {key}, {path});\n"
        + f"const stored = node.getSharedPluginData({namespace}, {key});\n"
        + f"if (stored !== {path}) throw new Error('FlowR contract path write mismatch');\n"
        + "return { mutatedNodeIds: [node.id], nodeName: node.name, "
        + "nodeType: node.type, contractPath: stored };"
    )
    verify = (
        lookup
        + f"const stored = node.getSharedPluginData({namespace}, {key});\n"
        + f"if (stored !== {path}) throw new Error('FlowR contract path verification failed');\n"
        + "return { nodeId: node.id, nodeName: node.name, nodeType: node.type, "
        + "contractPath: stored, verified: true };"
    )
    return write, verify


def prepare_binding(
    *, project_root: Path, contract_file: Path
) -> FigmaContractBinding:
    contract, relative = _contract_path(project_root, contract_file)
    component = parse_component(_component_file(contract))
    figma_lines = component.sections.get("Figma", [])
    if not figma_lines:
        raise ContractError("component contract must declare a Figma node URL")
    figma_url = " ".join(figma_lines).strip().split(maxsplit=1)[0]
    file_key, node_id = parse_figma_url(figma_url)
    write_code, verify_code = _figma_code(node_id, relative)
    return FigmaContractBinding(
        fileKey=file_key,
        nodeId=node_id,
        figmaUrl=figma_url,
        componentName=component.view,
        contractPath=relative,
        namespace=FIGMA_NAMESPACE,
        key=FIGMA_CONTRACT_KEY,
        writeCode=write_code,
        verifyCode=verify_code,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--contract-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        binding = prepare_binding(
            project_root=args.project_root,
            contract_file=args.contract_file,
        )
    except ContractError as error:
        parser.error(str(error))
    print(json.dumps(asdict(binding), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
