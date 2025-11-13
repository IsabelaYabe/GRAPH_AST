import ast
from src.astcore.model import Ctx
from src.astcore.walker import walk_module
from src.pass_plugins.loader import load_pass_plugins

source = """
class A:
    def m(self): pass
"""

def main():
    load_pass_plugins([
        "pass_plugins.builtin",   # ou "src.pass_plugins.builtin" conforme seu pacote
    ])

    tree = ast.parse(source)
    ctx = Ctx(lines=source.splitlines(), comments_by_line={})
    tnodes = walk_module(tree, ctx)
    # faça o que precisar com tnodes

if __name__ == "__main__":
    main()
