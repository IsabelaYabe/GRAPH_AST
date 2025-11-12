"""passes para extrair informações de nomes, visibilidade, tipos de métodos e classes, docstrings e comentários."""

import ast
from src.model import TNode
from src.context import Ctx, register
from src.utils import (
    unparse_safe, decorator_to_str, classify_visibility,
    any_name_like, is_name_like,
    leading_comment_block, first_docstring_span,
    split_identifier, detect_naming_style
)

# 1) nomes / visibilidade / qname
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

register(pass_names_visibility)

# 1.1) naming (camel/snake) — novo
def pass_naming_conventions(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Extrai convenções de nomenclatura (camelCase, snake_case) dos nomes."""
    if t.name:
        t.orig_name = t.name
        t.name_tokens = split_identifier(t.name)
        t.naming_style = detect_naming_style(t.name)

register(pass_naming_conventions)

# 2) método.kind
def pass_method_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Determina o tipo de método (instance, classmethod, staticmethod, property)."""
    if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and t.is_method):
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

register(pass_method_kind)

# 3) class_kind + flags
def pass_class_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Determina o tipo de classe (abstract, concrete, protocol) e flags associadas."""
    if not isinstance(n, ast.ClassDef): return
    t.base_classes = [unparse_safe(b) or "<unknown>" for b in n.bases]
    for kw in (n.keywords or []):
        if kw.arg == "metaclass":
            t.metaclass = unparse_safe(kw.value)

    decs = t.decorators or []
    t.is_dataclass = any(d.split(".")[-1].lower() == "dataclass" for d in decs)
    t.is_final     = any(d.split(".")[-1].lower() == "final"     for d in decs)
    t.is_enum      = any((b or "").split(".")[-1] in {"Enum", "IntEnum", "StrEnum"} for b in t.base_classes)

    is_protocol = any((b or "").split(".")[-1] == "Protocol" for b in t.base_classes)
    has_abc_base = any((b or "").split(".")[-1] == "ABC" for b in t.base_classes)
    has_abc_meta = (t.metaclass or "").split(".")[-1] == "ABCMeta"

    abs_methods = []
    for stmt in n.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sdecs = [decorator_to_str(d) for d in stmt.decorator_list]
            if any(sd.split(".")[-1] in {"abstractmethod", "abstractproperty"} for sd in sdecs):
                abs_methods.append(stmt.name)
    t.abstract_methods = abs_methods

    if is_protocol:
        t.class_kind = "protocol"
    elif has_abc_base or has_abc_meta or abs_methods:
        t.class_kind = "abstract"
    else:
        t.class_kind = "concrete"

register(pass_class_kind)

# 4) docstrings + comentários
def pass_docs_comments(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    """Extrai docstrings e comentários associados ao nó."""
    if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        t.docstring = ast.get_docstring(n)
    if t.lineno is not None:
        t.leading_comment_block = leading_comment_block(ctx.lines, ctx.comments_by_line, t.lineno)
        defline = ctx.comments_by_line.get(t.lineno, [])
        if defline:
            t.defline_comment = [c["text"] or c["raw"].lstrip("#").strip() for c in defline]
    if t.lineno is not None and t.end_lineno is not None:
        ds_span = first_docstring_span(n)
        for ln in range(t.lineno, t.end_lineno + 1):
            for c in ctx.comments_by_line.get(ln, []):
                if ds_span and ds_span[0] <= ln <= ds_span[1]: continue
                if ln == t.lineno: continue
                t.inline_comments.append(c)

register(pass_docs_comments)
