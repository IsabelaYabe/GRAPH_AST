from __future__ import annotations
import ast
from enum import Enum, auto
from collections import deque
from typing import Iterator, Protocol, Tuple

class Event(Enum):
    ENTER = auto()
    EXIT  = auto()

EventTuple = Tuple[Event, ast.AST]

class TraversalStrategy(Protocol):
    def walk(self, root: ast.AST) -> Iterator[EventTuple]:
        ...

class RecursivePreOrder(TraversalStrategy):
    def walk(self, root: ast.AST) -> Iterator[EventTuple]:
        def visit(n: ast.AST):
            yield (Event.ENTER, n)
            for ch in ast.iter_child_nodes(n):
                yield from visit(ch)
            yield (Event.EXIT, n)
        yield from visit(root)

class RecursivePostOrder(TraversalStrategy):
    def walk(self, root: ast.AST) -> Iterator[EventTuple]:
        def visit(n: ast.AST):
            for ch in ast.iter_child_nodes(n):
                yield from visit(ch)
            yield (Event.ENTER, n)
            yield (Event.EXIT, n)
        yield from visit(root)

class IterativePreOrder(TraversalStrategy):
    """
    Traversal the AST in pre-order using an explicit stack.
    """
    def walk(self, root: ast.AST) -> Iterator[EventTuple]:
        # pilha de (node, iterator dos filhos, entrou?)
        stack: list[tuple[ast.AST, list[ast.AST], bool]] = [(root, list(ast.iter_child_nodes(root)), False)]
        while stack:
            node, children, entered = stack[-1]
            if not entered:
                stack[-1] = (node, children, True)
                yield (Event.ENTER, node)
                if children:
                    ch = children.pop(0)
                    stack.append((ch, list(ast.iter_child_nodes(ch)), False))
                else:
                    # sem filhos -> já sai
                    yield (Event.EXIT, node)
                    stack.pop()
            else:
                if children:
                    ch = children.pop(0)
                    stack.append((ch, list(ast.iter_child_nodes(ch)), False))
                else:
                    yield (Event.EXIT, node)
                    stack.pop()

class BFSWithExit(TraversalStrategy):
    """
    Traversal the AST in breadth-first order, yielding EXIT events after all children have been processed.
    """
    def walk(self, root: ast.AST) -> Iterator[EventTuple]:
        q = deque([root])
        order: list[ast.AST] = []  # para EXIT depois
        while q:
            n = q.popleft()
            yield (Event.ENTER, n)
            order.append(n)
            for ch in ast.iter_child_nodes(n):
                q.append(ch)
        # EXIT em ordem inversa de ENTER para manter "fecha depois":
        for n in reversed(order):
            yield (Event.EXIT, n)

TRAVERSAL_STRATEGIES = {
    "recursive_pre": RecursivePreOrder,
    "recursive_post": RecursivePostOrder,
    "iterative_pre": IterativePreOrder,
    "bfs": BFSWithExit
    }