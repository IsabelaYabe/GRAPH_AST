from __future__ import annotations
import ast
from pathlib import Path
from astcore.pass_registry import register_pass
from astcore.model import TNode, Ctx
from astcore.phase import Phase

from logger import logger

def _compute_pkg_module(root: Path | None, file_path: Path) -> tuple[str | None, str]:
    """Return (package, module)."""
    if root is None:
        root = file_path.parent

    rel = file_path.relative_to(root) if file_path.is_absolute() and root.exists() else file_path.name
    rel_path = Path(rel) if isinstance(rel, (str,)) else rel

    parts = list(rel_path.parts)
    if not parts:
        return None, file_path.stem

    *dirs, fname = parts
    module = Path(fname).stem

    pkg_parts: list[str] = []
    cur = root
    for d in dirs:
        cur = cur / d
        if (cur / "__init__.py").exists():
            pkg_parts.append(d)
        else:
            pkg_parts = []

    package = ".".join(pkg_parts) if pkg_parts else ( ".".join(dirs) if dirs else None )
    return package, module

@register_pass(
    name="file_path_info",
    phase=Phase.ENRICH,
    order=5, 
    node_types=(ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
    provides=("file_path","rel_path","dir_path","package","module","depth","ext"),
)
def pass_file_path_info(t: TNode, n: ast.AST, ctx: Ctx) -> None:
    p: Path | None = ctx.file_path if hasattr(ctx, "file_path") else None
    r: Path | None = ctx.root_path if hasattr(ctx, "root_path") else None
    if p is None:
        return

    abs_file = p.resolve()
    abs_dir  = abs_file.parent.resolve()
    ext      = abs_file.suffix

    if r is not None and r.exists():
        rel = abs_file.relative_to(r.resolve())
        depth = len(rel.parents) - 1  
        rel_str = str(rel).replace("\\", "/")
    else:
        rel_str = abs_file.name
        depth = 0

    package, module = _compute_pkg_module(r.resolve() if r else None, abs_file)

    t.file_path = str(abs_file)
    t.dir_path  = str(abs_dir)
    t.rel_path  = rel_str
    t.package   = package
    t.module    = module
    t.depth     = depth
    t.ext       = ext
