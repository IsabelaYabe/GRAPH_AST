#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ast_step3_classkind.py
# Passo 3 (integrado): Classificar classes (abstract|concrete|protocol) + enriquecer com
# docstrings e comentários, além de nomes, qname, decoradores, visibilidade e tipo de método.

import ast
import argparse
import json
import tokenize
from io import BytesIO
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ---------------- util ----------------

def unparse_safe(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None

def decorator_to_str(d: ast.AST) -> str:
    try:
        if isinstance(d, ast.Name):
            return d.id
        if isinstance(d, ast.Attribute):
            return ast.unparse(d)
        if isinstance(d, ast.Call):
            return decorator_to_str(d.func)
        return ast.unparse(d)
    except Exception:
        return "<unknown>"

def classify_visibility(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    if name.startswith("__") and name.endswith("__"):
        return "special"
    if name.startswith("__"):
        return "private"
    if name.startswith("_"):
        return "protected"
    return "public"

def is_name_like(s: str, targets: List[str]) -> bool:
    s_low = s.split(".")[-1].lower()
    return s_low in {t.lower() for t in targets}

def any_name_like(seq: List[str], targets: List[str]) -> bool:
    return any(is_name_like(x, targets) for x in seq)

# --------- comentários/docstrings ----------

def collect_comments(source: str) -> List[dict]:
    """Coleta todos os comentários (# ...) com linha/coluna."""
    out = []
    buf = BytesIO(source.encode("utf-8"))
    try:
        for tok in tokenize.tokenize(buf.readline):
            if tok.type == tokenize.COMMENT:
                out.append({
                    "text": tok.string.lstrip("#").strip(),
                    "raw": tok.string,
                    "line": tok.start[0],
                    "col": tok.start[1],
                })
    except tokenize.TokenError:
        pass
    return out

def comments_by_line(comments: List[dict]) -> Dict[int, List[dict]]:
    m: Dict[int, List[dict]] = {}
    for c in comments:
        m.setdefault(c["line"], []).append(c)
    return m

def leading_comment_block(lines: List[str], line_to_comments: Dict[int, List[dict]], node_lineno: int) -> List[str]:
    """
    Bloco de comentários imediatamente acima do nó (linhas só com '#').
    Para ao encontrar linha em branco ou linha não-comentário.
    """
    res = []
    i = node_lineno - 1
    while i-1 >= 0:
        prev_line = lines[i-1]
        stripped = prev_line.lstrip()
        if stripped.startswith("#"):
            line_no = i
            for c in line_to_comments.get(line_no, []):
                res.append(c["text"] or c["raw"].lstrip("#").strip())
            i -= 1
            continue
        if stripped == "":
            break
        break
    res.reverse()
    return res

def first_docstring_span(node: ast.AST) -> Optional[Tuple[int, int]]:
    # Docstrings só existem em Module, ClassDef, FunctionDef e AsyncFunctionDef
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return None

    body = getattr(node, "body", None)
    if not isinstance(body, list) or not body:
        return None

    first = body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        ln = getattr(first, "lineno", None)
        en = getattr(first, "end_lineno", ln)
        if ln is not None and en is not None:
            return (ln, en)
    return None

# --------------- modelo ---------------

@dataclass
class TNode:
    type: str
    children: List[int]
    lineno: Optional[int] = None
    col: Optional[int] = None
    end_lineno: Optional[int] = None
    end_col: Optional[int] = None

    # comuns
    name: Optional[str] = None
    qname: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    visibility: Optional[str] = None

    # função/método
    is_method: Optional[bool] = None
    method_kind: Optional[str] = None
    args: List[str] = field(default_factory=list)

    # classe
    is_class: Optional[bool] = None
    class_kind: Optional[str] = None               # "abstract" | "concrete" | "protocol"
    base_classes: List[str] = field(default_factory=list)
    metaclass: Optional[str] = None
    is_dataclass: Optional[bool] = None
    is_final: Optional[bool] = None
    is_enum: Optional[bool] = None
    abstract_methods: List[str] = field(default_factory=list)

    # docstrings e comentários
    docstring: Optional[str] = None
    leading_comment_block: List[str] = field(default_factory=list)
    defline_comment: List[str] = field(default_factory=list)
    inline_comments: List[dict] = field(default_factory=list)

# --------------- construção da AST ---------------

def build_ast_tree(source: str) -> Tuple[List[TNode], int, Optional[str], List[dict]]:
    py_ast = ast.parse(source)
    lines = source.splitlines()
    all_comments = collect_comments(source)
    by_line = comments_by_line(all_comments)

    nodes: List[TNode] = []
    index_map: Dict[ast.AST, int] = {}

    class_stack: List[str] = []
    func_stack: List[str] = []

    def add_node(a: ast.AST) -> int:
        idx = len(nodes)
        index_map[a] = idx
        base = TNode(
            type=type(a).__name__,
            children=[],
            lineno=getattr(a, "lineno", None),
            col=getattr(a, "col_offset", None),
            end_lineno=getattr(a, "end_lineno", None),
            end_col=getattr(a, "end_col_offset", None),
        )

        # ------- nomes/metadados básicos -------
        if isinstance(a, ast.ClassDef):
            base.is_class = True
            base.name = a.name
            base.qname = ".".join(class_stack + [a.name]) if class_stack else a.name
            base.decorators = [decorator_to_str(d) for d in a.decorator_list]
            base.visibility = classify_visibility(a.name)
            base.base_classes = [unparse_safe(b) or "<unknown>" for b in a.bases]
            for kw in a.keywords or []:
                if kw.arg == "metaclass":
                    base.metaclass = unparse_safe(kw.value)

            base.is_dataclass = any_name_like(base.decorators, ["dataclass"])
            base.is_final = any_name_like(base.decorators, ["final"])
            base.is_enum = any_name_like(base.base_classes, ["Enum", "IntEnum", "StrEnum"])

            is_protocol = any_name_like(base.base_classes, ["Protocol"])
            has_abc_base = any_name_like(base.base_classes, ["ABC"])
            has_abc_meta = base.metaclass is not None and is_name_like(base.metaclass, ["ABCMeta"])

            abs_methods: List[str] = []
            for stmt in a.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decos = [decorator_to_str(d) for d in stmt.decorator_list]
                    if any_name_like(decos, ["abstractmethod", "abstractproperty"]):
                        abs_methods.append(stmt.name)
            base.abstract_methods = abs_methods

            is_abstract = is_protocol or has_abc_base or has_abc_meta or (len(abs_methods) > 0)
            if is_protocol:
                base.class_kind = "protocol"
            elif is_abstract:
                base.class_kind = "abstract"
            else:
                base.class_kind = "concrete"

        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)):
            base.name = a.name
            base.visibility = classify_visibility(a.name)
            base.decorators = [decorator_to_str(d) for d in a.decorator_list]
            base.args = [arg.arg for arg in (a.args.posonlyargs + a.args.args)]
            base.is_method = len(class_stack) > 0
            stack_for_qname = class_stack + func_stack
            base.qname = ".".join(stack_for_qname + [a.name]) if stack_for_qname else a.name

            if base.is_method:
                if any_name_like(base.decorators, ["staticmethod"]):
                    base.method_kind = "staticmethod"
                elif any_name_like(base.decorators, ["classmethod"]):
                    base.method_kind = "classmethod"
                elif any(d.endswith(".setter") or d.endswith(".deleter") or d == "property" for d in base.decorators):
                    base.method_kind = "property"
                elif base.args and base.args[0] == "self":
                    base.method_kind = "instance"
                elif base.args and base.args[0] == "cls":
                    base.method_kind = "classmethod"
                else:
                    base.method_kind = "instance"

        # ------- docstrings e comentários -------
        if isinstance(a, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            base.docstring = ast.get_docstring(a)
        else:
            base.docstring = None

        if base.lineno is not None:
            base.leading_comment_block = leading_comment_block(lines, by_line, base.lineno)
            defline = by_line.get(base.lineno, [])
            if defline:
                base.defline_comment = [c["text"] or c["raw"].lstrip("#").strip() for c in defline]

        if base.lineno is not None and base.end_lineno is not None:
            span_start, span_end = base.lineno, base.end_lineno
            ds_span = first_docstring_span(a)
            for ln in range(span_start, span_end + 1):
                for c in by_line.get(ln, []):
                    if ds_span and ds_span[0] <= ln <= ds_span[1]:
                        continue
                    if ln == base.lineno:
                        continue
                    base.inline_comments.append(c)

        nodes.append(base)
        return idx

    def visit(a: ast.AST) -> int:
        # cria nó com os stacks atuais (sem o próprio nome)
        idx = add_node(a)

        # empilha escopo DEPOIS, para que filhos vejam o escopo correto
        pushed_class = pushed_func = False
        if isinstance(a, ast.ClassDef):
            class_stack.append(a.name); pushed_class = True
        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_stack.append(a.name); pushed_func = True

        for child in ast.iter_child_nodes(a):
            cidx = visit(child)
            nodes[idx].children.append(cidx)

        if pushed_func: func_stack.pop()
        if pushed_class: class_stack.pop()
        return idx

    root_idx = visit(py_ast)
    module_doc = ast.get_docstring(py_ast)
    return nodes, root_idx, module_doc, all_comments

# --------------- saída ---------------

def to_json(nodes: List[TNode], root_idx: int, module_docstring: Optional[str], all_comments: List[dict]) -> dict:
    return {
        "root": root_idx,
        "module_docstring": module_docstring,
        "nodes": [
            {
                "id": i,
                "type": n.type,
                "children": n.children,
                "lineno": n.lineno,
                "col": n.col,
                "end_lineno": n.end_lineno,
                "end_col": n.end_col,
                "name": n.name,
                "qname": n.qname,
                "decorators": n.decorators,
                "visibility": n.visibility,
                "is_method": n.is_method,
                "method_kind": n.method_kind,
                "args": n.args,
                "is_class": n.is_class,
                "class_kind": n.class_kind,
                "base_classes": n.base_classes,
                "metaclass": n.metaclass,
                "is_dataclass": n.is_dataclass,
                "is_final": n.is_final,
                "is_enum": n.is_enum,
                "abstract_methods": n.abstract_methods,
                "docstring": n.docstring,
                "leading_comment_block": n.leading_comment_block,
                "defline_comment": n.defline_comment,
                "inline_comments": n.inline_comments,
            }
            for i, n in enumerate(nodes)
        ],
        "comments_flat": all_comments,
    }

# --------------- CLI ---------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Caminho para um arquivo .py")
    ap.add_argument("--save", type=str, default="", help="Prefixo para salvar JSON (sem extensão)")
    args = ap.parse_args()

    src = open(args.file, "r", encoding="utf-8").read()
    nodes, root, mod_doc, comments = build_ast_tree(src)
    data = to_json(nodes, root, mod_doc, comments)

    print(f"[OK] Nós: {len(nodes)} | raiz: {root} | module_docstring={bool(mod_doc)}")
    print("[OK] Amostra (classes): id name kind bases metaclass flags doc? lead? inline#")
    shown = 0
    for i, n in enumerate(nodes):
        if n.is_class:
            print(f"  {i} {n.name!r} {n.class_kind!r} bases={n.base_classes} meta={n.metaclass!r} "
                  f"dataclass={n.is_dataclass} final={n.is_final} enum={n.is_enum} "
                  f"doc={bool(n.docstring)} lead={bool(n.leading_comment_block)} inline={len(n.inline_comments)}")
            shown += 1
            if shown >= 8:
                break

    if args.save:
        from pathlib import Path
        outp = Path(args.save).with_suffix(".ast.classkind+docs.json")
        outp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[SALVO] {outp}")

if __name__ == "__main__":
    main()
