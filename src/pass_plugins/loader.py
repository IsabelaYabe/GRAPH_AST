import importlib
from typing import Iterable, Callable

class PluginInterface:
    @staticmethod
    def initialize() -> None:
        """Initialize the plugin."""
        ...

def import_module(name: str) -> PluginInterface:
    return importlib.import_module(name)

def load_pass_plugins(plugins: Iterable[str]) -> None:
    """ 
    Load and initialize pass plugins.
    """
    for plugin_name in plugins:
        plugin = import_module(plugin_name)
        init = getattr(plugin, "initialize", None)
        if Callable(init):
            init() # Deve chamar register_pass internamente
        else:
            raise RuntimeError(f"Plugin {plugin_name} does not have an 'initialize' function.")