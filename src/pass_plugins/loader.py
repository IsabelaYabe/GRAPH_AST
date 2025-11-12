import importlib

class PluginInterface:
    @staticmethod
    def initialize() -> None:
        """Initialize the plugin."""
        ...

def import_module(name: str) -> PluginInterface:
    return importlib.import_module(name)

def load_pass_plugins(plugins: list[str]) -> None:
    """ 
    """
    for plugin_name in plugins:
        plugin = import_module(plugin_name)
        plugin.initialize()