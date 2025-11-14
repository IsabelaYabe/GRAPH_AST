import ast
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase
from logger import logger

@register_pass(
    name="method_kind",
    phase=Phase.ENRICH,
    order=30,
    requires=("names_visibility",),   # precisa de t.is_method, t.args, t.decorators
    node_types=(ast.FunctionDef, ast.AsyncFunctionDef),
)
def pass_method_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    logger.info(f"Starting method_kind pass for method: {t.name}, this plugin determines method kinds")
    if not t.is_method:
        return
    decs = t.decorators or []
    if any("staticmethod" in d.split(".") for d in decs):
        t.method_kind = "staticmethod"
        logger.debug(f"Method {t.name} is a staticmethod")
    elif any("classmethod" in d.split(".") for d in decs):
        t.method_kind = "classmethod"
        logger.debug(f"Method {t.name} is a classmethod")
    elif any(d == "property" or d.endswith(".setter") or d.endswith(".deleter") for d in decs):
        t.method_kind = "property"
        logger.debug(f"Method {t.name} is a property")
    elif t.args and t.args[0] == "self":
        t.method_kind = "instance"
        logger.debug(f"Method {t.name} is an instance method")
    elif t.args and t.args[0] == "cls":
        t.method_kind = "classmethod"
        logger.debug(f"Method {t.name} is a classmethod")
    else:
        t.method_kind = "instance"
        logger.debug(f"Method {t.name} is an instance method")