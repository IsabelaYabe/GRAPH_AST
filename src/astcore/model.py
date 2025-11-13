import ast
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

@dataclass
class Ctx:
    class_stack: list[str] = field(default_factory=list)
    func_stack: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    comments_by_lines: dict[int, list] = field(default_factory=dict)

    # Space for plugins to store temporary data
    scratch: dict[str, Any] = field(default_factory=dict)

@dataclass
class TNode:
    py_node: ast.AST
    lineno: Optional[int] = None
    end_lineno: Optional[int] = None

    # campos que seus passes já usam:
    is_class: bool = False
    is_method: bool = False
    name: Optional[str] = None
    qname: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    visibility: Optional[str] = None
    args: list[str] = field(default_factory=list)
    method_kind: Optional[str] = None
    base_classes: list[str] = field(default_factory=list)
    metaclass: Optional[str] = None
    is_dataclass: bool = False
    is_final: bool = False
    is_enum: bool = False
    class_kind: Optional[str] = None
    abstract_methods: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    leading_comment_block: Optional[str] = None
    defline_comment: list[str] = field(default_factory=list)
    inline_comments: list[dict] = field(default_factory=list)

    # extras dos passes de naming:
    orig_name: Optional[str] = None
    name_tokens: list[str] = field(default_factory=list)
    naming_style: Optional[str] = None