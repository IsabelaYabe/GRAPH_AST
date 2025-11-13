from __future__ import annotations
import ast
from typing import Iterator, Iterable, Generic, TypeVar, Deque
from abc import ABC, abstractmethod
from collections import deque

N = TypeVar("N", bound=ast.AST)

class TreeIterator(ABC, Generic[N]):
    """Abstract base class for tree iterators."""
    @abstractmethod
    def __iter__(self) -> Iterator[N]: ...
    @abstractmethod
    def __next__(self) -> N: ...

class PreOrderIterator(TreeIterator[ast.AST]):
    def __init__(self, root: ast.AST) -> None:
        self._stack: list[ast.AST] = [root]

    def __iter__(self) -> Iterator[ast.AST]:
        return self

    def __next__(self) -> ast.AST:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        self._stack.extend(reversed(list(ast.iter_child_nodes(node))))
        return node

class BFSIterator(TreeIterator[ast.AST]):
    def __init__(self, root: ast.AST) -> None:
        self._q: Deque[ast.AST] = deque([root])

    def __iter__(self) -> Iterator[ast.AST]:
        return self

    def __next__(self) -> ast.AST:
        if not self._q:
            raise StopIteration
        node = self._q.popleft()
        self._q.extend(ast.iter_child_nodes(node))
        return node
