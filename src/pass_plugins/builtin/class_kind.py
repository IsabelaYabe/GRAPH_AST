import ast
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase
from utils import unparse_safe, decorator_to_str

from logger import logger

@register_pass(
    name="class_kind",
    phase=Phase.ENRICH,
    order=40,
    node_types=(ast.ClassDef,),
)
def pass_class_kind(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    logger.info(f"Starting class_kind pass for class: {t.name}, this plugin determines class kinds by analyzing bases and decorators")
    t.base_classes = [unparse_safe(b) or "<unknown>" for b in n.bases]
    logger.debug(f"Class {t.name} bases: {t.base_classes}")

    for kw in (n.keywords or []):
        logger.debug(f"Class {t.name} keyword argument: {getattr(kw, 'arg', None)}")
        if getattr(kw, "arg", None) == "metaclass":
            logger.debug(f"Class {t.name} metaclass found")
            t.metaclass = unparse_safe(kw.value)

    decs = t.decorators or []
    logger.debug(f"Class {t.name} decorators: {decs}")
    t.is_dataclass = any(d.split(".")[-1].lower() == "dataclass" for d in decs)    
    logger.debug(f"Class {t.name} is_dataclass: {t.is_dataclass}")
    t.is_final = any(d.split(".")[-1].lower() == "final" for d in decs)
    logger.debug(f"Class {t.name} is_dataclass: {t.is_dataclass}, is_final: {t.is_final}")
    t.is_enum = any((b or "").split(".")[-1] in {"Enum", "IntEnum", "StrEnum"} for b in t.base_classes)
    logger.debug(f"Class {t.name} is_enum: {t.is_enum}")
    is_protocol = any((b or "").split(".")[-1] == "Protocol" for b in t.base_classes)
    logger.debug(f"Class {t.name} is_protocol: {is_protocol}")
    has_abc_base = any((b or "").split(".")[-1] == "ABC" for b in t.base_classes)
    logger.debug(f"Class {t.name} has_abc_base: {has_abc_base}")
    has_abc_meta = (t.metaclass or "").split(".")[-1] == "ABCMeta"
    logger.debug(f"Class {t.name} has_abc_meta: {has_abc_meta}")

    abs_methods = []
    for stmt in n.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sdecs = [decorator_to_str(d) for d in stmt.decorator_list]
            if any(sd.split(".")[-1] in {"abstractmethod", "abstractproperty"} for sd in sdecs):
                abs_methods.append(stmt.name)
    t.abstract_methods = abs_methods
    logger.debug(f"Class {t.name} abstract_methods: {t.abstract_methods}")

    if is_protocol:
        t.class_kind = "protocol"
        logger.debug(f"Class {t.name} is_protocol: {is_protocol}")
    elif has_abc_base or has_abc_meta or abs_methods:
        t.class_kind = "abstract"
        logger.debug(f"Class {t.name} is_abstract: True")
    else:
        t.class_kind = "concrete"
        logger.debug(f"Class {t.name} is_concrete: True")
