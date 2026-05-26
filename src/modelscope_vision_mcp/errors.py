class VisionMcpError(Exception):
    """Base error for ModelScope Vision MCP."""


class ConfigError(VisionMcpError):
    """Raised when project configuration is invalid."""


class NoAvailableModelError(VisionMcpError):
    """Raised when no configured model can be used."""


class ModelCallError(VisionMcpError):
    """Raised when a ModelScope model call fails."""

    def __init__(self, model_id: str, reason: str, category: str = "model_error"):
        super().__init__(f"{model_id}: {reason}")
        self.model_id = model_id
        self.reason = reason
        self.category = category
