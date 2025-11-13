from __future__ import annotations
import ast
from typing import Iterable
from .model import TNode, Ctx
from .pass_registry import REGISTRY
from .phase import Phase

def _run_passes_for_node(phase: Phase, t: TNode, n: ast.AST, ctx: Ctx) -> None:
    specs = [s for s in REGISTRY.get_for_phase(phase) if any(isinstance(n, tp) for tp in s.node_types)]

    specs = REGISTRY.topological(specs)
    for s in specs:
        if s.when and not s.when(t,n, ctx):
            continue
        s.fn(t,n,ctx)

def walk_module(nodes: Iterable[ast.AST], ctx: Ctx) -> list[TNode]:
    tnodes: list[TNode] = []

    for n in nodes:
        t = TNode(py_node=n, lineon=getattr(n,"lineno", None),end_lineno=getattr(n, "end_lineno", None))

        #PRE
        _run_passes_for_node(Phase.PRE, t, n, ctx)
        push_class = isinstance(n, ast.ClassDef)
        push_func = isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        if push_class:
            ctx.class_stack.append(n.name)
        if push_func:
            ctx.func_stack.append(n.name)
        
        #ENRICH
        _run_passes_for_node(Phase.ENRICH, t, n, ctx)
        tnodes.append(t)

        # POST
        _run_passes_for_node(Phase.POST, t, n, ctx)
        if push_func:
            ctx.func_stack.pop()
        if push_class:
            ctx.class_stack.pop()

        return tnodes