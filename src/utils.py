"""Utilitários para manipulação de AST e análise de código-fonte Python."""
import ast, re
from io import BytesIO
import tokenize
from typing import List, Dict, Optional, Tuple

def unparse_safe(node: Optional[ast.AST]) -> Optiona[str]:
    """
    Try to convert an AST node back to source code using ast.unparse.
    """
    if node is None:
        return None
    try: 
        return ast.unparse(node)
    except Exception:
        return None

def decorator_to_str(node: ast.AST) -> str:
    """
    Return a generic string representation of a decorator AST node, ignoring arguments.
    """
    try:
        # @f()() -> f
        while isinstance(node, ast.Call):
            node = node.func
        # @decorator[T] -> decorator
        if isinstance(node, ast.Subscript):
            node = node.value
        # nome simples
        if isinstance(node, ast.Name):
            return node.id
        # pkg.mod.decorator
        if isinstance(node, ast.Attribute):
            parts = []
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
                return ".".join(reversed(parts))
            # fallback (caso raro: atributo sobre algo não-Name)
            return ast.unparse(node)
        # último recurso
        return ast.unparse(node)
    except Exception:
        return "<unknown>"

def classify_visibility(name: Optional[str]) -> Optional[str]:
    """Classifica a visibilidade de um nome com base em convenções de nomenclatura Python."""   
    if not name: 
        return None
    if name.startswith("__") and name.endswith("__"): 
        return "special"
    if name.startswith("__"): 
        return "private"
    if name.startswith("_"):  
        return "protected"
    return "public"

def is_name_like(s: str, targets: List[str]) -> bool:
    """Verifica se um nome se assemelha a qualquer um dos alvos, ignorando diferenças de caso."""
    return s.split(".")[-1].lower() in {t.lower() for t in targets}

def any_name_like(seq: List[str], targets: List[str]) -> bool:
    """Verifica se algum nome em uma sequência se assemelha a qualquer um dos alvos."""
    return any(is_name_like(x, targets) for x in seq)

# ---- comentários ----
def collect_comments(source: str) -> List[dict]:
    """Coleta todos os comentários (# ...) com linha/coluna."""
    out = []
    buf = BytesIO(source.encode("utf-8"))
    try:
        for tok in tokenize.tokenize(buf.readline):
            if tok.type == tokenize.COMMENT:
                out.append({
                    "text": tok.string.lstrip("#").strip(),
                    "raw": tok.string,
                    "line": tok.start[0],
                    "col": tok.start[1],
                })
    except tokenize.TokenError:
        pass
    return out

def comments_by_line(comments: List[dict]) -> Dict[int, List[dict]]:
    """Agrupa comentários por número de linha."""
    m: Dict[int, List[dict]] = {}
    for c in comments:
        m.setdefault(c["line"], []).append(c)
    return m

def leading_comment_block(lines: List[str], line_to_comments: Dict[int, List[dict]], node_lineno: int) -> List[str]:
    """Extrai o bloco de comentários que precede imediatamente uma linha de nó."""
    res = []
    i = node_lineno - 1
    while i-1 >= 0:
        stripped = lines[i-1].lstrip()
        if stripped.startswith("#"):
            for c in line_to_comments.get(i, []):
                res.append(c["text"] or c["raw"].lstrip("#").strip())
            i -= 1 
            continue
        if stripped == "": 
            break
        break
    res.reverse()
    return res

def first_docstring_span(node: ast.AST) -> Optional[Tuple[int,int]]:
    """Retorna o intervalo da primeira docstring em um nó AST."""
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)): 
        return None
    body = getattr(node, "body", None)
    if not isinstance(body, list) or not body: 
        return None
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        ln = getattr(first, "lineno", None)
        en = getattr(first, "end_lineno", ln)
        if ln is not None and en is not None: 
            return ln, en
    return None

# ---- naming: camelCase/snake_case ----
_CAMEL_SPLIT: re.Pattern = re.compile(r'''
    (?<=[A-Za-z])(?=[A-Z][a-z]) |   # AbcDef -> Abc | Def
    (?<=[a-z0-9])(?=[A-Z])      |   # fooBar -> foo | Bar
    _+                               # snake_case: separa nos underscores
''', re.X)

def split_identifier(name: str) -> list[str]:
    """Divide um identificador em tokens, lidando com camelCase e snake_case."""
    parts = [p for p in _CAMEL_SPLIT.split(name) if p and p != "_"]
    tokens = []
    for p in parts:
        # manter acrônimos como uma peça (HTTP) mas normalizar case no token final
        if p.isupper() and len(p) > 1:
            tokens.append(p.lower())
        else:
            tokens.append(p.lower())
    return tokens

def detect_naming_style(name: str) -> str:
    """Detecta o estilo de nomenclatura de um identificador."""
    if "_" in name: return "snake_case"
    if name[:1].isupper(): return "PascalCase"
    if any(ch.isupper() for ch in name): return "camelCase"
    return "lower"
