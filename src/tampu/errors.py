class TampuError(Exception):
    """A public error with a stable code and controlled message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
