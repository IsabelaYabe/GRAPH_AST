from enum import Enum

class Phase(str, Enum):
    """
    Phases of AST processing.
        PRE: before AST enrichment TNode
        ENRICH: during AST enrichment TNode
        POST: after AST enrichment TNode
    """ 
    PRE = "pre" 
    ENRICH = "enrich"
    POST = "post"