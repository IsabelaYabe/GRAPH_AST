# build_ast_tree.py
"""Constrói uma árvore AST enriquecida (TNode) a partir do código-fonte Python, aplicando vários passes de enriquecimento."""
import ast, json
from pathlib import Path
from typing import Optional
from src.model import TNode
from src.context import Ctx, ENRICHERS
from src.utils import collect_comments, comments_by_line

from src import passes  # IMPORTANTE: registra os passes no ENRICHERS
from src.pass_plugins import load_pass_plugins #Plugin system

def build_ast_tree(source: str, plugins: list[str]) -> tuple[list[TNode], int, Optional[str], list[dict]]:
    if plugins:
        load_pass_plugins(plugins)
        
    py_ast = ast.parse(source)
    lines = source.splitlines()
    all_comments = collect_comments(source)
    by_line = comments_by_line(all_comments)

    nodes: list[TNode] = []
    index_map: dict[ast.AST, int] = {}
    ctx = Ctx(lines=lines, comments_by_line=by_line)

    def add_node(a: ast.AST) -> int:
        idx = len(nodes)
        index_map[a] = idx
        t = TNode(
            type=type(a).__name__,
            children=[],
            lineno=getattr(a, "lineno", None),
            col=getattr(a, "col_offset", None),
            end_lineno=getattr(a, "end_lineno", None),
            end_col=getattr(a, "end_col_offset", None),
        )
        for enricher in ENRICHERS:
            enricher(t, a, ctx)
        nodes.append(t)
        return idx

    def visit(a: ast.AST) -> int:
        idx = add_node(a)
        pushed_class = pushed_func = False
        if isinstance(a, ast.ClassDef):
            ctx.class_stack.append(a.name); pushed_class = True
        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ctx.func_stack.append(a.name); pushed_func = True
        for child in ast.iter_child_nodes(a):
            cidx = visit(child)
            nodes[idx].children.append(cidx)
        if pushed_func: ctx.func_stack.pop()
        if pushed_class: ctx.class_stack.pop()
        return idx

    root_idx = visit(py_ast)
    module_doc = ast.get_docstring(py_ast)
    return nodes, root_idx, module_doc, all_comments

# opcional: helper p/ salvar JSON
def to_json(nodes: list[TNode], root_idx: int, module_docstring: Optional[str], all_comments: list[dict]) -> dict:
    return {
        "root": root_idx,
        "module_docstring": module_docstring,
        "nodes": [t.__dict__ | {"id": i} for i, t in enumerate(nodes)],
        "comments_flat": all_comments,
    }
