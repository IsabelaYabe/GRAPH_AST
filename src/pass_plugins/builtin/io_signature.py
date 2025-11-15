from __future__ import annotations
import ast
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase
from utils import unparse_safe

from logger import logger

def _mk_param(a: ast.arg | None, default_ast, kind: str) -> dict:
    if a is None:
        # *args / **kwargs podem ser None
        name = None
        ann  = None
    else:
        name = a.arg
        ann  = unparse_safe(getattr(a, "annotation", None))
    return {
        "name": name,
        "kind": kind,                       # posonly | pos | vararg | kwonly | varkw
        "annotation": ann,
        "default": unparse_safe(default_ast),
    }

def _has_yield(n: ast.AST) -> bool:
    for sub in ast.walk(n):
        if isinstance(sub, (ast.Yield, ast.YieldFrom)):
            return True
    return False

def _collect_raises(n: ast.AST) -> list[str]:
    out: list[str] = []
    for sub in ast.walk(n):
        if isinstance(sub, ast.Raise):
            # Python 3.11+: Raise(exc, cause)
            exc = getattr(sub, "exc", None)
            if exc is not None:
                out.append(unparse_safe(exc) or "<unknown>")
    return out

@register_pass(
    name="io_signature",
    phase=Phase.ENRICH,
    order=35,                                # depois de names_visibility (10/20) e perto de method_kind (30)
    requires=("names_visibility",),          # já traz t.is_method, t.args, decorators
    node_types=(ast.FunctionDef, ast.AsyncFunctionDef),
    provides=("params","return_annotation","is_generator","raises"),
)
def pass_io_signature(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    fn: ast.FunctionDef | ast.AsyncFunctionDef = n 

    a = fn.args
    params: list[dict] = []

    posonly = list(a.posonlyargs)
    pos = list(a.args)
    pos_defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)

    # posonly não tem defaults em Python (só via args.defaults se estiverem misturados antes dos keyword-only),
    # mas o parser separa: então tratamos posonly sem defaults explícitos:
    for arg in posonly:
        params.append(_mk_param(arg, None, "posonly"))

    for arg, d in zip(pos, pos_defaults):
        params.append(_mk_param(arg, d, "pos"))

    params.append(_mk_param(a.vararg, None, "vararg"))

    for kwarg, d in zip(a.kwonlyargs, a.kw_defaults):
        params.append(_mk_param(kwarg, d, "kwonly"))

    params.append(_mk_param(a.kwarg, None, "varkw"))

    params = [p for p in params if p["name"] is not None or p["kind"] in ("vararg","varkw")]

    ret_ann = unparse_safe(getattr(fn, "returns", None))
    is_gen  = _has_yield(fn)
    raises  = _collect_raises(fn)

    t.params = params
    t.return_annotation = ret_ann
    t.is_generator = is_gen
    t.raises = raises
