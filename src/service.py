from __future__ import annotations
import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Optional

from astcore.model import Ctx, TNode
from astcore.walker import walk_module
from pass_plugins.loader import load_pass_plugins
from utils import collect_comments, comments_by_line

STRATEGIES = ("recursive_pre", "recursive_post", "iterative_pre", "bfs")

@dataclass(frozen=True)
class FileAnalysis:
    file: Path
    ctx: Ctx
    tnodes: List[TNode]
    nodes_json: List[Dict]

@dataclass(frozen=True)
class AnalysisResult:
    strategy: str
    files: List[FileAnalysis]

# ---------------------------
# Utils
# ---------------------------

def _read_text(p: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "latin-1")
    for enc in encodings:
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return p.read_bytes().decode(errors="ignore")

def _tnode_to_jsonable(t: TNode) -> Dict:
    d = asdict(t)
    py = t.py_node
    d["py_node"] = {
        "type": type(py).__name__,
        "fields": list(py._fields) if hasattr(py, "_fields") else [],
    }
    return d

def _iter_py_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    else:
        yield from (p for p in path.rglob("*.py") if p.is_file())

def _analyze_source(source: str, strategy: str, file_path: Path | None = None, root_path: Path | None = None) -> tuple[Ctx, List[TNode], List[Dict]]:
    tree = ast.parse(source)
    comms = collect_comments(source)
    ctx = Ctx(lines=source.splitlines(), comments_by_line=comments_by_line(comms),root_path=root_path, file_path=file_path)
    tnodes = walk_module(tree, ctx, strategy=strategy)
    nodes_json = [_tnode_to_jsonable(t) for t in tnodes]
    return ctx, tnodes, nodes_json

# ---------------------------
# Public API
# ---------------------------

def analyze_file(
    file_path: Path, *, strategy: str = "recursive_pre", root_path: Path | None = None) -> FileAnalysis:
    if strategy not in STRATEGIES:
        raise ValueError(f"Invalid strategy: {strategy}. Options: {STRATEGIES}")
    src = _read_text(file_path)
    ctx, tnodes, nodes_json = _analyze_source(src, strategy=strategy, file_path=file_path, root_path=root_path)
    return FileAnalysis(file=file_path, ctx=ctx, tnodes=tnodes, nodes_json=nodes_json)

def analyze_path(
    path: Path | str,
    *,
    strategy: str = "recursive_pre",
    plugins: Optional[Iterable[str]] = ("pass_plugins.builtin",),
) -> AnalysisResult:
    """
    Loads plugins, iterates over .py file(s) in the path, and returns Ctx/TNodes/JSON per file.
    """
    # Load passes/plugins only once
    if plugins:
        load_pass_plugins(list(plugins))

    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path não encontrado: {root}")

    files: List[FileAnalysis] = []
    for f in _iter_py_files(root):
        try:
            files.append(analyze_file(f, strategy=strategy, root_path=root))
        except SyntaxError as e:
            files.append(
                FileAnalysis(
                    file=f,
                    ctx=Ctx(lines=[], comments_by_line={}),
                    tnodes=[],
                    nodes_json=[{
                        "error": f"SyntaxError: {e.msg} at line {e.lineno} col {e.offset}"
                    }],
                )
            )
    return AnalysisResult(strategy=strategy, files=files)

def export_json(
    result: AnalysisResult,
    out_path: Path | str,
) -> Path:
    """
    Exports the AnalysisResult to a JSON file at out_path.
    Returns the Path to the output file.
    """
    payload = {
        "strategy": result.strategy,
        "results": [
            {
                "file": str(fr.file),
                "node_count": len(fr.nodes_json),
                "nodes": fr.nodes_json,
            }
            for fr in result.files
        ],
    }
    out = Path(out_path)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
