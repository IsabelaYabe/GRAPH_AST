"""Modelo de dados para representar nós na AST com informações adicionais."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class TNode:
    # base
    type: str
    children: List[int]
    lineno: Optional[int] = None 
    col: Optional[int] = None
    end_lineno: Optional[int] = None
    end_col: Optional[int] = None

    # nomes
    name: Optional[str] = None
    qname: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    visibility: Optional[str] = None

    # função/método
    is_method: Optional[bool] = None
    method_kind: Optional[str] = None
    args: List[str] = field(default_factory=list)
 
    # classe
    is_class: Optional[bool] = None
    class_kind: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    metaclass: Optional[str] = None
    is_dataclass: Optional[bool] = None
    is_final: Optional[bool] = None
    is_enum: Optional[bool] = None
    abstract_methods: List[str] = field(default_factory=list)

    # docstrings / comentários
    docstring: Optional[str] = None
    leading_comment_block: List[str] = field(default_factory=list)
    defline_comment: List[str] = field(default_factory=list)
    inline_comments: List[Dict] = field(default_factory=list)

    # naming (novo: p/ camelCase/snake_case)
    orig_name: Optional[str] = None
    name_tokens: List[str] = field(default_factory=list)
    naming_style: Optional[str] = None
