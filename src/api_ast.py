from pathlib import Path
from service import analyze_path, export_json
from logger import logger
from embeddings import export_tokens_as_json

result = analyze_path(
    Path("exemplos/exemplos_curtos"),
    strategy="recursive_pre",
    plugins=["pass_plugins.builtin"],
)

first = result.files[0]
ctx = first.ctx
tnodes = first.tnodes

logger.debug("Exporting JSON to ast.json")
export_json(result, "ast.json")

ast_json_path = "ast.json"

logger.info(f"Lendo AST de {ast_json_path}")
export_tokens_as_json(ast_json_path)