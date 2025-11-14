import ast, json
from astcore.model import Ctx
from astcore.walker import walk_module
from pass_plugins.loader import load_pass_plugins

SRC = '''
from typing import Protocol
from abc import ABC, ABCMeta, abstractmethod

class A: pass
class B(A): pass
class P(Protocol): 
    def ok(self): ...
class C(ABC):
    @abstractmethod
    def run(self): ...
class D(metaclass=ABCMeta):
    def x(self): ...
'''

def test_passes_end_to_end():
    load_pass_plugins(["pass_plugins.builtin"])
    ctx = Ctx(lines=SRC.splitlines(), comments_by_line={})
    tnodes = walk_module(ast.parse(SRC), ctx, strategy="recursive_pre")

    by_name = {t.name: t for t in tnodes if t.name in {"A","B","P","C","D"}}
    assert by_name["A"].class_kind == "concrete"
    assert by_name["B"].class_kind == "concrete"
    assert by_name["P"].class_kind == "protocol"
    assert by_name["C"].class_kind == "abstract"
    assert "run" in (by_name["C"].abstract_methods or [])
    assert by_name["D"].class_kind == "abstract"
