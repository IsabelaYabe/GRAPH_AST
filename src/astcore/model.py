import ast
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pathlib import Path

@dataclass
class Ctx:
    class_stack: list[str] = field(default_factory=list)
    func_stack: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    comments_by_line: dict[int, list] = field(default_factory=dict) #rever optional bela
    root_path: Path | None = None    
    file_path: Path | None = None
    # Space for plugins to store temporary data
    scratch: dict[str, Any] = field(default_factory=dict)

@dataclass
class TNode:
    py_node: ast.AST
    lineno: Optional[int] = None
    end_lineno: Optional[int] = None

    # campos que seus passes já usam:
    is_class: bool = False # names_visibility
    is_method: bool = False # names_visibility
    name: Optional[str] = None # names_visibility
    qname: Optional[str] = None # names_visibility
    decorators: list[str] = field (default_factory=list) # names_visibility
    visibility: Optional[str] = None # names_visibility
    args: list[str] = field(default_factory=list) # names_visibility
    
    method_kind: Optional[str] = None # method_kind

    base_classes: list[str] = field (default_factory=list) # class_kind
    metaclass: Optional[str] = None # class_kind
    is_dataclass: bool = False # class_kind
    is_final: bool = False # class_kind
    is_enum: bool = False # class_kind
    class_kind: Optional[str] = None # class_kind
    abstract_methods: list[str] = field (default_factory=list) # class_kind

    docstring: Optional[str] = None # docs_comments
    leading_comment_block: Optional[str] = None # docs_comments
    defline_comment: list[str] = field(default_factory=list) # docs_comments
    inline_comments: list[dict] = field(default_factory=list) # docs_comments

    orig_name: Optional[str] = None # naming
    name_tokens: list[str] = field(default_factory=list) # naming
    naming_style: Optional[str] = None # naming

    params: list[dict] = field(default_factory=list)           # io_signature
    return_annotation: Optional[str] = None                    # io_signature
    is_generator: bool = False                                 # io_signature
    raises: list[str] = field(default_factory=list)            # io_signature

    rel_path: str | None = None        # path_info
    file_path: str | None = None       # path_info
    dir_path: str | None = None        # path_info
    package: str | None = None         # path_info
    module: str | None = None          # path_info
    depth: int = 0                     # path_info
    ext: str | None = None             # path_info
