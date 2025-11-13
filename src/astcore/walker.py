from __future__ import annotations
import ast
from typing import Iterable
from .model import TNode, Ctx
from .pass_registry import REGISTRY
from .phase import Phase
from .traversal import Event
from .strategy_factory import get_strategy, StrategyName

def _run_passes_for_node(phase: Phase, t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Run all registered passes for a given node and phase."""
    ordered_specs = REGISTRY.topological(REGISTRY.get_for_phase(phase))
    
    for s in ordered_specs:
        if not isinstance(n, s.node_types):
            continue
        if s.when and not s.when(t, n, ctx):
            continue
        s.fn(t, n, ctx)

def walk_module(root: ast.AST, ctx: Ctx, strategy: StrategyName) -> list[TNode]:
    """Walk the AST rooted at `root`, applying registered passes."""
    tnodes: list[TNode] = []
    t_by_id: dict[int, TNode] = {}
    traversal_strategy = get_strategy(strategy)
    for ev, n in traversal_strategy.walk(root):
        if ev == Event.ENTER:
            t = TNode(py_node=n,
                      lineno=getattr(n, 'lineno', None),
                      end_lineno=getattr(n, 'end_lineno', None))
            t_by_id[id(n)] = t
            # PRE 
            _run_passes_for_node(Phase.PRE, t, n, ctx)
            if isinstance(n, ast.ClassDef):
                ctx.class_stack.append(n.name)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ctx.func_stack.append(n.name)
            # ENRICH
            _run_passes_for_node(Phase.ENRICH, t, n, ctx)
            tnodes.append(t)
        else:  
            # EXIT
            t = t_by_id[id(n)]
            # POST 
            _run_passes_for_node(Phase.POST, t, n, ctx)

            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ctx.func_stack.pop()
            if isinstance(n, ast.ClassDef):
                ctx.class_stack.pop()
    return tnodes