from logger import logger

class PluginError(Exception):
    """Base class for plugin-related errors."""
    def __init__(self, message="Plugin error occurred"):
        logger.error(message)
        super().__init__(message)
    

class PassDependencyError(PluginError): 
    """Raised when there is a dependency issue with passes."""
    def __init__(self, message="Pass dependency error"):
        super().__init__(message)

class PassRegistrationError(PluginError): 
    """Raised when there is an error during pass registration."""
    def __init__(self, message="Pass registration error"):
        super().__init__(message)
