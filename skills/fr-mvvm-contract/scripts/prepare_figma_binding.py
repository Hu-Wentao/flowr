#!/usr/bin/env python3
"""Prepare deterministic machine-readable and visible Figma bindings."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from contract_core import ContractError
from contract_parser import parse_component
from figma_contract import (
    normalize_node_id,
    parse_figma_contract_nodes,
    parse_figma_url,
)


FIGMA_NAMESPACE = "flowr"
FIGMA_CONTRACT_KEY = "contract_binding"
FIGMA_BINDING_VERSION = 1


@dataclass(frozen=True)
class FigmaContractBinding:
    fileKey: str
    nodeId: str
    figmaRole: str
    figmaUrl: str
    componentNames: list[str]
    contractPaths: list[str]
    pagePaths: list[str]
    visiblePathLines: list[str]
    visibleCardName: str
    bindingVersion: int
    bindingValue: str
    namespace: str
    key: str
    writeCode: str
    verifyCode: str


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
        raise ContractError(
            "component contract must be inside the project root"
        ) from error
    return contract, relative.as_posix()


def _component_file(contract_file: Path) -> Path:
    return contract_file.with_name(contract_file.name.removesuffix(".c.dart") + ".dart")


def _figma_code(
    node_id: str,
    binding_value: str,
    visible_path_lines: list[str],
    visible_card_name: str,
    requires_page_frame: bool,
) -> tuple[str, str]:
    node = json.dumps(node_id)
    expected = json.dumps(binding_value, ensure_ascii=False)
    visible_lines = json.dumps(visible_path_lines, ensure_ascii=False)
    card_name = json.dumps(visible_card_name, ensure_ascii=False)
    namespace = json.dumps(FIGMA_NAMESPACE)
    key = json.dumps(FIGMA_CONTRACT_KEY)
    lookup = (
        f"const node = await figma.getNodeByIdAsync({node});\n"
        f"if (!node) throw new Error('Figma node not found: ' + {node});\n"
        + (
            "if (node.type !== 'FRAME') throw new Error('FlowR page binding "
            "must target a concrete Figma Frame');\n"
            if requires_page_frame
            else ""
        )
    )
    host_lookup = (
        "let host = node.parent;\n"
        "while (host && host.type !== 'SECTION' && host.type !== 'PAGE') "
        "host = host.parent;\n"
        "if (!host || (host.type !== 'SECTION' && host.type !== 'PAGE')) "
        "throw new Error('FlowR visible binding requires a Section or Page "
        "ancestor');\n"
    )
    write = (
        lookup
        + f"const expected = {expected};\n"
        + f"const visibleLines = {visible_lines};\n"
        + f"const cardName = {card_name};\n"
        + f"node.setSharedPluginData({namespace}, {key}, expected);\n"
        + f"const stored = node.getSharedPluginData({namespace}, {key});\n"
        + "if (stored !== expected) "
        + "throw new Error('FlowR contract binding write mismatch');\n"
        + host_lookup
        + "const createdNodeIds = [];\n"
        + "const mutatedNodeIds = [node.id];\n"
        + "const removedNodeIds = [];\n"
        + "let card = host.children.find(child => child.type === 'FRAME' "
        + "&& child.name === cardName);\n"
        + "if (!card) {\n"
        + "  card = figma.createAutoLayout('VERTICAL');\n"
        + "  card.name = cardName;\n"
        + "  host.appendChild(card);\n"
        + "  createdNodeIds.push(card.id);\n"
        + "} else {\n"
        + "  mutatedNodeIds.push(card.id);\n"
        + "}\n"
        + "let body = card.children.find(child => child.type === 'TEXT' "
        + "&& (child.name === 'Contract Path' || child.name === 'Paths'));\n"
        + "if (!body) { body = figma.createText(); "
        + "createdNodeIds.push(body.id); }\n"
        + "else mutatedNodeIds.push(body.id);\n"
        + "body.name = 'Contract Path';\n"
        + "const obsolete = card.children.filter(child => child !== body);\n"
        + "const textNodes = [body, ...obsolete.filter(child => "
        + "child.type === 'TEXT')];\n"
        + "const fonts = [];\n"
        + "for (const text of textNodes) {\n"
        + "  const segments = text.getStyledTextSegments(['fontName']);\n"
        + "  if (segments.length) {\n"
        + "    for (const segment of segments) fonts.push(segment.fontName);\n"
        + "  } else if (text.fontName !== figma.mixed) {\n"
        + "    fonts.push(text.fontName);\n"
        + "  }\n"
        + "}\n"
        + "const uniqueFonts = [...new Map(fonts.map(font => "
        + "[JSON.stringify(font), font])).values()];\n"
        + "await Promise.all(uniqueFonts.map(font => "
        + "figma.loadFontAsync(font)));\n"
        + "for (const child of obsolete) {\n"
        + "  removedNodeIds.push(child.id); child.remove();\n"
        + "}\n"
        + "const cardWidth = 'width' in node "
        + "? Math.min(Math.max(node.width, 360), 1800) : 360;\n"
        + "card.resize(cardWidth, Math.max(card.height, 56));\n"
        + "card.layoutSizingHorizontal = 'FIXED';\n"
        + "card.layoutSizingVertical = 'HUG';\n"
        + "card.paddingTop = 12; card.paddingRight = 12; "
        + "card.paddingBottom = 12; card.paddingLeft = 12;\n"
        + "card.itemSpacing = 0; card.cornerRadius = 10;\n"
        + "card.fills = [{ type: 'SOLID', color: { r: 1, g: 0.9569, "
        + "b: 0.8 } }];\n"
        + "card.strokes = [{ type: 'SOLID', color: { r: 0.9294, "
        + "g: 0.6588, b: 0.0745 } }];\n"
        + "card.strokeWeight = 2;\n"
        + "body.textAutoResize = 'HEIGHT'; "
        + "body.resize(cardWidth - 24, body.height);\n"
        + "body.characters = visibleLines.join('\\n');\n"
        + "body.fontSize = 12; body.lineHeight = { value: 16, "
        + "unit: 'PIXELS' };\n"
        + "body.fills = [{ type: 'SOLID', color: { r: 0.3216, "
        + "g: 0.2392, b: 0.0863 } }];\n"
        + "card.appendChild(body);\n"
        + "const others = host.children.filter(child => child !== card "
        + "&& 'x' in child && 'y' in child && 'width' in child "
        + "&& 'height' in child);\n"
        + "let x = 40; let targetTop = 40;\n"
        + "if (node.parent === host && 'x' in node && 'y' in node) {\n"
        + "  x = node.x; targetTop = node.y;\n"
        + "} else if (node.absoluteBoundingBox) {\n"
        + "  const hostX = host.type === 'PAGE' || !host.absoluteBoundingBox "
        + "? 0 : host.absoluteBoundingBox.x;\n"
        + "  const hostY = host.type === 'PAGE' || !host.absoluteBoundingBox "
        + "? 0 : host.absoluteBoundingBox.y;\n"
        + "  x = node.absoluteBoundingBox.x - hostX;\n"
        + "  targetTop = node.absoluteBoundingBox.y - hostY;\n"
        + "}\n"
        + "let y = targetTop - card.height - 16;\n"
        + "const overlaps = child => x < child.x + child.width "
        + "&& x + card.width > child.x && y < child.y + child.height "
        + "&& y + card.height > child.y;\n"
        + "for (let pass = 0; pass <= others.length; pass += 1) {\n"
        + "  const collision = others.find(overlaps);\n"
        + "  if (!collision) break;\n"
        + "  y = collision.y - card.height - 16;\n"
        + "}\n"
        + "card.x = x; card.y = y;\n"
        + "await card.screenshot({ scale: 0.5 });\n"
        + "return { createdNodeIds, removedNodeIds, "
        + "mutatedNodeIds: [...new Set("
        + "mutatedNodeIds)], nodeName: node.name, nodeType: node.type, "
        + "visibleCardId: card.id, visiblePaths: visibleLines, "
        + "binding: JSON.parse(stored) };"
    )
    verify = (
        lookup
        + f"const expected = {expected};\n"
        + f"const visibleLines = {visible_lines};\n"
        + f"const cardName = {card_name};\n"
        + f"const stored = node.getSharedPluginData({namespace}, {key});\n"
        + "if (stored !== expected) "
        + "throw new Error('FlowR contract binding verification failed');\n"
        + host_lookup
        + "const card = host.children.find(child => child.type === 'FRAME' "
        + "&& child.name === cardName);\n"
        + "if (!card || !card.visible) throw new Error('FlowR visible Dart "
        + "path card verification failed');\n"
        + "const body = card.children.find(child => child.type === 'TEXT' "
        + "&& child.name === 'Contract Path');\n"
        + "if (!body || !visibleLines.every(line => "
        + "body.characters.includes(line))) throw new Error('FlowR visible "
        + "Dart paths verification failed');\n"
        + "let targetTop = 0;\n"
        + "if (node.parent === host && 'y' in node) targetTop = node.y;\n"
        + "else if (node.absoluteBoundingBox) {\n"
        + "  const hostY = host.type === 'PAGE' || !host.absoluteBoundingBox "
        + "? 0 : host.absoluteBoundingBox.y;\n"
        + "  targetTop = node.absoluteBoundingBox.y - hostY;\n"
        + "}\n"
        + "if (card.y + card.height > targetTop) throw new Error('FlowR "
        + "contract card is not above its page');\n"
        + "await card.screenshot({ scale: 0.5 });\n"
        + "return { nodeId: node.id, nodeName: node.name, nodeType: node.type, "
        + "visibleCardId: card.id, visiblePaths: visibleLines, "
        + "binding: JSON.parse(stored), verified: true };"
    )
    return write, verify


def prepare_binding(
    *,
    project_root: Path,
    contract_files: list[Path],
    target_node_id: str | None = None,
) -> FigmaContractBinding:
    if not contract_files:
        raise ContractError("at least one component contract is required")

    requested_node_id = normalize_node_id(target_node_id) if target_node_id else None
    details: dict[str, tuple[str, str, str, str, str]] = {}
    for contract_file in contract_files:
        contract, relative = _contract_path(project_root, contract_file)
        component = parse_component(_component_file(contract))
        nodes = parse_figma_contract_nodes(component.sections)
        if requested_node_id is None:
            target = nodes.primary
        else:
            target = next(
                (node for node in nodes.bindable if node.node_id == requested_node_id),
                None,
            )
            if target is None:
                non_bindable = next(
                    (node for node in nodes.all if node.node_id == requested_node_id),
                    None,
                )
                if non_bindable is not None:
                    raise ContractError(
                        f"Figma {non_bindable.role} node {requested_node_id} "
                        "must not receive a contract binding"
                    )
                raise ContractError(
                    f"Figma node {requested_node_id} is not declared by {relative}"
                )
        details[relative] = (
            component.view,
            target.url,
            target.file_key,
            target.node_id,
            target.role,
        )

    ordered = sorted(details.items())
    targets = {(detail[2], detail[3]) for _, detail in ordered}
    if len(targets) != 1:
        raise ContractError("all component contracts must target the same Figma node")

    contract_paths = [relative for relative, _ in ordered]
    page_paths: list[str] = []
    visible_path_lines: list[str] = []
    root = project_root.resolve()
    for contract_path in contract_paths:
        contract = root / contract_path
        page = contract.with_name(contract.name.removesuffix(".c.dart") + ".page.dart")
        if page.is_file():
            page_path = page.relative_to(root).as_posix()
            page_paths.append(page_path)
        visible_path_lines.append(contract_path)
    if len(page_paths) > 1:
        raise ContractError(
            "prepare page contracts one at a time so each Figma Frame gets "
            "its own visible contract card"
        )
    component_names = [detail[0] for _, detail in ordered]
    figma_url = ordered[0][1][1]
    roles = {detail[4] for _, detail in ordered}
    figma_role = roles.pop() if len(roles) == 1 else "mixed"
    file_key, node_id = next(iter(targets))
    binding_value = json.dumps(
        {"version": FIGMA_BINDING_VERSION, "contracts": contract_paths},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    visible_card_name = f"FlowR · Dart Paths · {node_id}"
    write_code, verify_code = _figma_code(
        node_id,
        binding_value,
        visible_path_lines,
        visible_card_name,
        bool(page_paths),
    )
    return FigmaContractBinding(
        fileKey=file_key,
        nodeId=node_id,
        figmaRole=figma_role,
        figmaUrl=figma_url,
        componentNames=component_names,
        contractPaths=contract_paths,
        pagePaths=page_paths,
        visiblePathLines=visible_path_lines,
        visibleCardName=visible_card_name,
        bindingVersion=FIGMA_BINDING_VERSION,
        bindingValue=binding_value,
        namespace=FIGMA_NAMESPACE,
        key=FIGMA_CONTRACT_KEY,
        writeCode=write_code,
        verifyCode=verify_code,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--contract-file",
        type=Path,
        action="append",
        required=True,
        help="Final .c.dart binding set; repeat for split modules.",
    )
    parser.add_argument(
        "--target-node-id",
        help=(
            "Bind one declared primary or Figma States node. References and "
            "excluded nodes are never bindable. Defaults to the primary Figma node."
        ),
    )
    args = parser.parse_args()
    try:
        binding = prepare_binding(
            project_root=args.project_root,
            contract_files=args.contract_file,
            target_node_id=args.target_node_id,
        )
    except ContractError as error:
        parser.error(str(error))
    print(json.dumps(asdict(binding), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
