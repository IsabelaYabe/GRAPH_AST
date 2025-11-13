import ast
from astcore.model import Ctx
from astcore.walker import walk_module
from pass_plugins.loader import load_pass_plugins

source = """
class A:
    def m(self): pass
"""

source = """
PI = 3.14

class Foo:
    _k = 0
    def __init__(self, x: int):
        self.x = x
    @staticmethod
    def util(z):
        return z*2
    @classmethod
    def make(cls, v):
        return cls(v)
    @property
    def valor(self):
        return self.x

def _aux(y): return y + 1
"""

def main(source):
    load_pass_plugins(["pass_plugins.builtin"])
    tree = ast.parse(source)
    ctx = Ctx(lines=source.splitlines(), comments_by_line={})

    # escolha a estratégia:
    tnodes = walk_module(tree, ctx, strategy="recursive_pre")   # ou "iterative_pre", "bfs"

    # faça algo com tnodes
    for t in tnodes:
        if t.qname:
            print(t.qname, t.method_kind or t.class_kind or "")

if __name__ == "__main__":
    main(source)