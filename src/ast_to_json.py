
#!/usr/bin/env python3
from __future__ import annotations
import ast, json, sys, argparse
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

# Project imports (expect your repo layout where these modules are importable)
from astcore.model import Ctx, TNode
from astcore.walker import walk_module
from pass_plugins.loader import load_pass_plugins
from utils import collect_comments, comments_by_line

# Valid strategies: recursive_pre, recursive_post, iterative_pre, bfs
STRATEGIES = ("recursive_pre", "recursive_post", "iterative_pre", "bfs")

def read_text(p: Path) -> str:
    # Try utf-8 first, then fallbacks common in repos
    encodings = ("utf-8", "utf-8-sig", "latin-1")
    for enc in encodings:
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    # Last resort: binary -> decode ignoring errors
    return p.read_bytes().decode(errors="ignore")

def tnode_to_jsonable(t: TNode) -> dict:
    d = asdict(t)
    # Replace non-serializable py_node with a compact description
    py = t.py_node
    d["py_node"] = {
        "type": type(py).__name__,
        "fields": list(py._fields) if hasattr(py, "_fields") else []
    }
    return d

def process_source(source: str, strategy: str) -> list[dict]:
    tree = ast.parse(source)
    # Build Ctx with comments to enrich docs_comments pass
    comms = collect_comments(source)
    ctx = Ctx(lines=source.splitlines(), comments_by_line=comments_by_line(comms))
    tnodes = walk_module(tree, ctx, strategy=strategy)  # list[TNode]
    return [tnode_to_jsonable(t) for t in tnodes]

def iter_py_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    else:
        for p in path.rglob("*.py"):
            if p.is_file():
                yield p

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Export enriched AST to JSON")
    parser.add_argument("path", help="Python file or directory")
    parser.add_argument("-s", "--strategy", default="recursive_pre", choices=STRATEGIES,
                        help="Traversal strategy (default: recursive_pre)")
    parser.add_argument("-o", "--output", help="Output JSON file (default: stdout)")
    parser.add_argument("--plugins", nargs="*", default=["pass_plugins.builtin"],
                        help="Plugin modules to load (default: pass_plugins.builtin)")
    args = parser.parse_args(argv)

    # Load passes
    load_pass_plugins(args.plugins)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Path not found: {root}", file=sys.stderr)
        return 2

    payload = {"strategy": args.strategy, "results": []}
    for file in iter_py_files(root):
        try:
            src = read_text(file)
            nodes = process_source(src, strategy=args.strategy)
            payload["results"].append({
                "file": str(file),
                "node_count": len(nodes),
                "nodes": nodes
            })
        except SyntaxError as e:
            payload["results"].append({
                "file": str(file),
                "error": f"SyntaxError: {e.msg} at line {e.lineno} col {e.offset}"
            })
        except Exception as e:
            payload["results"].append({
                "file": str(file),
                "error": f"{type(e).__name__}: {e}"
            })

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
