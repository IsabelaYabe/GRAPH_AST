from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import json
import os
import re

from dataclasses import dataclass, asdict
from logger import logger
from utils import split_identifier  

_WORD = re.compile(r"[A-Za-z0-9_]+")

@dataclass
class Tokens:
    name: str
    type: str
    params: List[str]
    docstring: List[str]
    leading_comments: List[str]
    class_kind: str | None
    method_kind: str | None
    visibility: str | None
    is_dataclass: bool
    is_final: bool
    base_classes: List[str]
    decorators: List[str]
    package: str | None
    module: str | None
    rel_path: str | None

    @property
    def flat(self) -> List[str]:
        tokens: list[str] = []
        if self.type:
            tokens.append(f"ast_{self.type.lower()}")

        tokens += split_identifier(self.name)
        tokens += self.params
        tokens += self.docstring
        tokens += self.leading_comments

        if self.class_kind:
            tokens.append(f"class_{self.class_kind}")
        if self.method_kind:
            tokens.append(f"method_{self.method_kind}")
        if self.visibility:
            tokens.append(f"vis_{self.visibility}")
        if self.is_dataclass:
            tokens.append("tag_dataclass")
        if self.is_final:
            tokens.append("tag_final")

        tokens += self.base_classes
        tokens += self.decorators

        for part in filter(None, [self.package, self.module, self.rel_path]):
            tokens += _split_path_to_tokens(str(part))

        return tokens


def _tokenize_text(text: str | None) -> list[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD.finditer(text)]


def _split_path_to_tokens(path: str) -> list[str]:
    parts = path.replace("\\", "/").split("/")
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        base, _ext = os.path.splitext(p)
        for piece in base.split("."):
            if piece:
                out += split_identifier(piece)
    return out


def _build_tokens_for_node_dict(node: Dict[str, Any]) -> Tokens | None:
    """
    Constrói UMA instância de Tokens a partir de um nó (dict) da AST.
    """
    name = node.get("name") or ""
    if name == "":
        return None

    py_node = node.get("py_node") or {}
    node_type = py_node.get("type") or ""

    params: list[str] = []
    for p in node.get("params") or []:
        pname = p.get("name")
        if pname:
            params += split_identifier(str(pname))

    docstring = _tokenize_text(node.get("docstring"))

    leading_comments: list[str] = []
    leading_block = node.get("leading_comment_block")
    if leading_block:
        if isinstance(leading_block, str):
            leading_comments += _tokenize_text(leading_block)
        else:
            for line in leading_block:
                leading_comments += _tokenize_text(str(line))

    base_classes = [
        tok
        for b in (node.get("base_classes") or [])
        for tok in split_identifier(str(b))
    ]

    decorators = [
        tok
        for d in (node.get("decorators") or [])
        for tok in split_identifier(str(d))
    ]

    class_kind  = node.get("class_kind")
    method_kind = node.get("method_kind")
    visibility  = node.get("names_visibility") or node.get("visibility")
    is_dc       = bool(node.get("is_dataclass"))
    is_final    = bool(node.get("is_final"))

    package = node.get("package")
    module = node.get("module")
    rel_path = node.get("rel_path")

    return Tokens(
        name=name,
        type=node_type,
        params=params,
        docstring=docstring,
        leading_comments=leading_comments,
        class_kind=class_kind,
        method_kind=method_kind,
        visibility=visibility,
        is_dataclass=is_dc,
        is_final=is_final,
        base_classes=base_classes,
        decorators=decorators,
        package=package,
        module=module,
        rel_path=rel_path,
    )

def collect_tokens_from_payload(payload: Dict[str, Any]) -> List[Tokens]:
    all_tokens: list[Tokens] = []
    for file_block in payload.get("results", []):
        for node in file_block.get("nodes", []):
            t = _build_tokens_for_node_dict(node)
            if t is not None:
                all_tokens.append(t)
    return all_tokens
# aqui
def collect_tokens_from_payload(payload: Dict[str, Any]) -> List[Tokens]:
    all_tokens: list[Tokens] = []
    for file_block in payload.get("results", []):
        for node in reversed(file_block.get("nodes", [])):
            t = _build_tokens_for_node_dict(node)
            if t is not None:
                all_tokens.append(t)
    return all_tokens

def collect_tokens_from_file(in_path: str | Path) -> List[Tokens]:
    """
    Lê o JSON exportado pelo service e devolve uma lista de instâncias de Tokens.
    """
    in_p = Path(in_path)
    data = json.loads(in_p.read_text(encoding="utf-8"))
    return collect_tokens_from_payload(data)


def export_tokens_as_json(
    in_path: str | Path,
    out_path: str | Path | None = None,
) -> Path:
    """
    Gera um JSON só com os Tokens (cada entrada é um dict do dataclass Tokens).
    Útil se você quiser inspecionar / salvar dataset intermediário.
    """
    in_p = Path(in_path)
    tokens_list = collect_tokens_from_file(in_p)

    if out_path is None:
        logger.info(f"Nenhum caminho de saída fornecido, salvando em {in_p.stem}_tokens.json")
        out_p = in_p.with_name(in_p.stem + "_tokens.json")
    else:
        out_p = Path(out_path)

    serializable = [asdict(t) for t in tokens_list]
    out_p.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_p

