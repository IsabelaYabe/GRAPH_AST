import ast
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase
from utils import split_identifier, detect_naming_style
from logger import logger
@register_pass(
    name="naming_conventions",
    phase=Phase.ENRICH,
    order=20,
    requires=("names_visibility",),           
    node_types=(ast.AST,)
)
def pass_naming_conventions(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    logger.info(f"Starting naming_conventions pass for node: {t.name}, this plugin analyzes naming conventions")
    if t.name:
        t.orig_name = t.name
        logger.debug(f"Node {t.name} original name: {t.orig_name}")
        t.name_tokens = split_identifier(t.name)
        logger.debug(f"Node {t.name} name tokens: {t.name_tokens}")
        t.naming_style = detect_naming_style(t.name)
        logger.debug(f"Node {t.name} naming style: {t.naming_style}")
