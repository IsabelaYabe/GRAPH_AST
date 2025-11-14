"""
Loader for pass plugins.
"""
import importlib
from types import ModuleType
from typing import Iterable, Protocol, runtime_checkable
from logger import logger

@runtime_checkable
class PluginInterface(Protocol):
    @staticmethod
    def initialize() -> None:
        ...

def import_module(name: str) -> ModuleType | PluginInterface:
    return importlib.import_module(name)

def load_pass_plugins(plugins: Iterable[str]) -> None:
    """ 
    Load and initialize pass plugins.
    """
    for plugin_name in plugins:
        plugin = import_module(plugin_name)
        logger.debug(plugin)
        if isinstance(plugin, PluginInterface):
            logger.debug("sou um plugin")
        init = getattr(plugin, "initialize", None)
        if callable(init):
            logger.debug("sou chamado")
            init() 
        else:
            raise RuntimeError(f"Plugin {plugin_name} does not have an 'initialize' function.")