from logger import logger
def initialize() -> None:
    logger.debug("Initializing builtin pass plugins.")
    from . import names_visibility   
    from . import naming             
    from . import method_kind        
    from . import class_kind         
    from . import docs_comments      
