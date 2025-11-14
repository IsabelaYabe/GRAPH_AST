from __future__ import annotations
import ast
from dataclasses import dataclass, field
from heapq import heappush, heappop
from typing import Callable, Iterable, Optional, Protocol, Any, TYPE_CHECKING

from .model import TNode, Ctx
from .phase import Phase
from .errors import PassDependencyError

from logger import logger


class PassFn(Protocol):
    def __call__(self, tnode: TNode, n: ast.AST, ctx: Ctx) -> None: ...

WhenFn = Callable[[TNode, ast.AST, Ctx], bool]

@dataclass(order=True)
class PassSpec:
    sort_index: tuple[int, str] = field(init=False, repr=False)
    name: str
    fn: PassFn
    requires: tuple[str, ...] 
    phase: Phase = Phase.ENRICH
    order: int = 100
    node_types: tuple[type[ast.AST], ...] = (ast.AST,) # enquais nós roda
    when: Optional[WhenFn] = None
    provides: tuple[str, ...] = () # campos que este pass garante

    def __post_init__(self):
        self.sort_index = (self.order, self.name) 
        # Basic validations
        if not self.name:
            raise ValueError("PassSpec name cannot be empty")
        if self.name in self.requires:
            raise PassDependencyError(f"Pass '{self.name}' cannot require itself")
        for t in self.node_types:
            if not(isinstance(t, type) and issubclass(t, ast.AST)):
                raise TypeError(f"invalid node_type: {t}")
        if len(set(self.provides)) != len(self.provides):
            raise ValueError(f"Provides list contains duplicates: {self.provides}")

class PassRegistry:
    def __init__(self):
        self._passes: dict[Phase, list[PassSpec]] = {p: [] for p in Phase}
        self._index: dict[str, PassSpec] = {}

    def register(self, spec: PassSpec) -> None:
        if spec.name in self._index:
            raise ValueError(f"Pass with name '{spec.name}' is already registered")
        self._index[spec.name] = spec
        self._passes[spec.phase].append(spec)
        self._passes[spec.phase].sort()

    def get_for_phase(self, phase: Phase) -> list[PassSpec]:
        return list(self._passes[phase])
    
    def topological(self, specs: Iterable[PassSpec]) -> list[PassSpec]:
        """Return the passes sorted topologically according to dependencies and order."""
        specs = list(specs)  
        name_to_spec = {s.name: s for s in specs}
        self._validate_dependencies(specs, name_to_spec)
        incoming_count, dependents = self._build_graph(specs)
        heap = self._init_heap(specs, incoming_count)
        return self._drain_heap(heap, incoming_count, dependents, name_to_spec, len(specs))

    @staticmethod
    def _validate_dependencies(specs: list[PassSpec], name_to_spec: dict[str, PassSpec]) -> None:
        """Validate dependencies exist and no self-dependencies."""
        unknown = {req for s in specs for req in s.requires if req not in name_to_spec}
        if unknown:
            raise PassDependencyError(f"Dependencies not found: {sorted(unknown)}")
        for s in specs:
            if s.name in s.requires:
                raise PassDependencyError(f"{s.name} cannot require itself")
    
    @staticmethod
    def _build_graph(specs: list[PassSpec]) -> tuple[dict[str, int], dict[str, list[str]]]:
            """
            Build the dependency graph.
            Returns a tuple of:
            - incoming_count: dict mapping pass name to number of incoming edges (dependencies)
            - dependents: dict mapping pass name to list of dependent pass names
            """
            incoming_count = {s.name: len(s.requires) for s in specs}
            dependents: dict[str, list[str]] = {s.name: [] for s in specs}
            for s in specs:
                for req in s.requires:
                    dependents[req].append(s.name)
            return incoming_count, dependents

    @staticmethod
    def _init_heap(specs: list[PassSpec], incoming_count: dict[str, int]) -> list[tuple[int, str, PassSpec]]:
        """Initialize the heap with ready passes (no incoming edges), prioritizing (order, name)."""
        heap: list[tuple[int, str, PassSpec]] = []
        for s in specs:
            if incoming_count[s.name] == 0:
                heappush(heap, (s.order, s.name, s))
        return heap
    
    @staticmethod
    def _drain_heap(heap: list[tuple[int, str, PassSpec]], incoming_count: dict[str, int], dependents: dict[str, list[str]], name_to_spec: dict[str, PassSpec], expected_len: int) -> list[PassSpec]:
        """Process the heap (Kahn with priority)."""
        out: list[PassSpec] = []
        while heap:
            _, _, cur = heappop(heap)
            out.append(cur)
            for dep_name in dependents[cur.name]:
                incoming_count[dep_name] -= 1
                if incoming_count[dep_name] == 0:
                    dep = name_to_spec[dep_name]
                    heappush(heap, (dep.order, dep.name, dep))

        if len(out) != expected_len:
            remaining = [n for n, c in incoming_count.items() if c > 0]
            raise PassDependencyError(f"Cycle detected among: {sorted(remaining)}")
        return out

REGISTRY = PassRegistry()

def register_pass(
    *,
    name: str,
    phase: Phase = Phase.ENRICH,
    order: int = 100,
    requires: tuple[str, ...] = (),
    node_types: tuple[type[ast.AST], ...] = (ast.AST,),
    when: Optional[WhenFn] = None,
    provides: tuple[str, ...] = (),
) -> Callable[[PassFn], PassFn]:
    def deco(fn: PassFn):
        REGISTRY.register(PassSpec(
            name=name, fn=fn, phase=phase, order=order,
            requires=requires, node_types=node_types, when=when, provides=provides
        ))
        return fn
    return deco