import ast
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase
from utils import leading_comment_block, first_docstring_span
from logger import logger

def has_lineno(t: TNode, n: ast.AST, ctx: Ctx) -> bool:
    logger.debug(f"Checking if node {t.name} has lineno: {t.lineno is not None}")
    return t.lineno is not None

@register_pass(
    name="docs_comments",
    phase=Phase.ENRICH,
    order=50,
    node_types=(ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
    when=has_lineno,
)
def pass_docs_comments(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    logger.info(f"Starting docs_comments pass for node: {t.name}, this plugin extracts docstrings and comments")
    if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        t.docstring = ast.get_docstring(n)
        logger.debug(f"Node {t.name} docstring: {t.docstring}")

    if t.lineno is not None:
        t.leading_comment_block = leading_comment_block(ctx.lines, ctx.comments_by_line, t.lineno)
        defline = ctx.comments_by_line.get(t.lineno, [])
        logger.debug(f"Node {t.name} defline comments: {defline}")
        if defline:
            t.defline_comment = [c["text"] or c["raw"].lstrip("#").strip() for c in defline]

    if t.lineno is not None and t.end_lineno is not None:
        ds_span = first_docstring_span(n)
        for ln in range(t.lineno, t.end_lineno + 1):
            for c in ctx.comments_by_line.get(ln, []):
                if ds_span and ds_span[0] <= ln <= ds_span[1]: 
                    continue
                if ln == t.lineno: 
                    continue
                t.inline_comments.append(c)
        logger.debug(f"Node {t.name} inline comments: {t.inline_comments}")
