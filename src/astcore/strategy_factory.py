# src/astcore/strategy_factory.py
from __future__ import annotations
from typing import Literal
from .traversal import TraversalStrategy, TRAVERSAL_STRATEGIES

StrategyName = Literal["recursive_pre", "recursive_post", "iterative_pre", "bfs"]

def get_strategy(name: StrategyName = "recursive_pre") -> TraversalStrategy:
    strategy_cls = TRAVERSAL_STRATEGIES[name]
    if strategy_cls is None:
        raise ValueError(f"Unknown traversal strategy: {name}")
    return strategy_cls()
