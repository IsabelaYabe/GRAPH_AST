"""
Initialize builtin pass plugins:
    names_visibility
    naming
    method_kind
    class_kind
    docs_comments
To manager the plugins, we import the modules here.
"""
from logger import logger

def initialize() -> None:
    from . import names_visibility   
    from . import naming             
    from . import method_kind        
    from . import class_kind         
    from . import docs_comments  
    from . import io_signature    
    from . import path_info
    