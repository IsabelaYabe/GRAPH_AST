import ast
from typing import Protocol, runtime_checkable, Callable, Optional
from dataclasses import dataclass, field
from src.model import TNode  

passes_creation_funcs: dict[str, Callable[..., ]]


@dataclass
class Ctx:
    """Contexto durante a construção da árvore AST enriquecida."""
    class_stack: list[str] = field(default_factory=list)
    func_stack: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    comments_by_line: dict[int, list] = field(default_factory=dict)

@runtime_checkable
class Enricher(Protocol):
    """Protocolo para funções que enriquecem TNode com informações adicionais."""
    def __call__(self, tnode: TNode, py_node: ast.AST, ctx: Ctx) -> None: ...

ENRICHERS: list[Enricher] = []  # Chain of Responsibility

def register(enricher: Enricher) -> None:
    ENRICHERS.append(enricher)
