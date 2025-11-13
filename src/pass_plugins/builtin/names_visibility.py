import ast
from astcore.model import TNode, Ctx
from astcore.pass_registry import register_pass
from astcore.phase import Phase
from utils import decorator_to_str, classify_visibility

@register_pass(
    name="names_visibility",
    phase=Phase.ENRICH,
    order=10,
    node_types=(ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
    provides=("name", "qname", "decorators", "visibility", "is_method", "args")
    )
def pass_names_visibility(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Preenche nomes, visibilidade e nomes qualificados (qname)."""
    if isinstance(n, ast.ClassDef):
        t.is_class = True
        t.name = n.name
        if ctx.class_stack:
            t.qname = ".".join(ctx.class_stack + [n.name])
        else:
            t.qname = n.name
        t.decorators = [decorator_to_str(d) for d in n.decorator_list]
        t.visibility = classify_visibility(n.name)
    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        t.name = n.name
        t.decorators = [decorator_to_str(d) for d in n.decorator_list]
        t.visibility = classify_visibility(n.name)
        t.is_method = bool(ctx.class_stack)
        args = n.args.posonlyargs + n.args.args
        t.args = [a.arg for a in args]
        stack = ctx.class_stack + ctx.func_stack
        if stack:
            t.qname = ".".join(stack + [n.name])
        else:
            t.qname = n.name