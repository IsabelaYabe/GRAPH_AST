# src/embeddings/dataset.py
from pathlib import Path
from typing import List
import pandas as pd

from embeddings.tokens import collect_tokens_from_file, Tokens

def is_usecase_candidate(t: Tokens) -> bool:
    # refine depois se quiser
    if t.visibility not in (None, "public"):
        return False
    # ignora classes puras, se quiser focar em funções/métodos
    if t.type == "ClassDef":
        return False
    return True

def build_tokens_dataframe(ast_json_path: str | Path) -> pd.DataFrame:
    tokens_list: List[Tokens] = collect_tokens_from_file(ast_json_path)

    rows = []
    for t in tokens_list:
        if not is_usecase_candidate(t):
            continue

        rows.append({
            "name": t.name,
            "node_type": t.type,
            "class_kind": t.class_kind,
            "method_kind": t.method_kind,
            "visibility": t.visibility,
            "package": t.package,
            "module": t.module,
            "rel_path": t.rel_path,
            "tokens_list": t.flat,
            "tokens_str": " ".join(t.flat),
        })

    return pd.DataFrame(rows)
