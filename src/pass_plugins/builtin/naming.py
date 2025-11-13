import ast
from src.astcore.pass_registry import register_pass
from src.astcore.model import TNode, Ctx
from src.astcore.phase import Phase
from src.utils import split_identifier, detect_naming_style

@register_pass(
    name="naming_conventions",
    phase=Phase.ENRICH,
    order=20,
    requires=("names_visibility",),           
    node_types=(ast.AST,)
)
def pass_naming_conventions(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    if t.name:
        t.orig_name = t.name
        t.name_tokens = split_identifier(t.name)
        t.naming_style = detect_naming_style(t.name)