class UnsupportedFileTypeError(Exception):
    """Raised when the file type is not supported."""
    pass

class UnexpectedFormatValueError(Exception):
    """Raised where the file format is unexpected"""


__all__ = [
    "UnsupportedFileTypeError",
    "UnexpectedFormatValueError"
]