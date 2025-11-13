def initialize() -> None:
    # importar submódulos para acionar os @register_pass
    from . import names_visibility   # noqa
    from . import naming             # noqa
    from . import method_kind        # noqa
    from . import class_kind         # noqa
    from . import docs_comments      # noqa
