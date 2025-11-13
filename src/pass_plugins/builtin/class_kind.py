import ast
from src.astcore.pass_registry import register_pass
from src.astcore.model import TNode, Ctx
from src.astcore.phases import Phase
from src.utils import unparse_safe, decorator_to_str

@register_pass(
    name="class_kind",
    phase=Phase.ENRICH,
    order=40,
    node_types=(ast.ClassDef,),
)
def pass_class_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    t.base_classes = [unparse_safe(b) or "<unknown>" for b in n.bases]
    for kw in (n.keywords or []):
        if getattr(kw, "arg", None) == "metaclass":
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
