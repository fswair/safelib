"""
Exceptions module for safelib.
"""


class EntityNotFound(Exception):
    """Exception raised when an entity is not found."""

    def __init__(self, entity_name: str, namespace: str):
        super().__init__(
            f"Entity '{entity_name}' not found in namespace '{namespace}'."
        )
        self.entity_name = entity_name
        self.namespace = namespace
        self.add_note(
            f"Check if the entity exists in the specified namespace: {namespace}."
        )


class NamespaceNotFound(Exception):
    """Exception raised when a namespace is not found."""

    def __init__(self, main: bool = False, fallback: bool = False):
        if main or fallback:
            ns = "Main" if main else "Fallback"
        super().__init__(f"{ns} module required but not specified.")
        self.add_note(
            f"Ensure the {ns} module specified in the configuration correctly."
        )
