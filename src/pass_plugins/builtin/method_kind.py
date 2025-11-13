import ast
from src.astcore.pass_registry import register_pass
from src.astcore.model import TNode, Ctx
from src.astcore.phases import Phase

@register_pass(
    name="method_kind",
    phase=Phase.ENRICH,
    order=30,
    requires=("names_visibility",),   # precisa de t.is_method, t.args, t.decorators
    node_types=(ast.FunctionDef, ast.AsyncFunctionDef),
)
def pass_method_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    if not t.is_method:
        return
    decs = t.decorators or []
    if any("staticmethod" in d.split(".") for d in decs):
        t.method_kind = "staticmethod"
    elif any("classmethod" in d.split(".") for d in decs):
        t.method_kind = "classmethod"
    elif any(d == "property" or d.endswith(".setter") or d.endswith(".deleter") for d in decs):
        t.method_kind = "property"
    elif t.args and t.args[0] == "self":
        t.method_kind = "instance"
    elif t.args and t.args[0] == "cls":
        t.method_kind = "classmethod"
    else:
        t.method_kind = "instance"
