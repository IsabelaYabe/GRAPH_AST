from pathlib import Path
from service import analyze_path, export_json

result = analyze_path(
    Path("exemplos/exemplos_curtos"),
    strategy="recursive_pre",
    plugins=["pass_plugins.builtin"],
)

first = result.files[0]
ctx = first.ctx
tnodes = first.tnodes

print("Exporting JSON to ast.json")
export_json(result, "ast.json")