from pathlib import Path
from typing import Union


class ResourcesReader:
    """
    A utility class to read resources.
    """
    resources_path = Path(__file__).parent

    @classmethod
    def resource_text(cls, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read a resource as text.
        """
        return (cls.resources_path/path).read_text(encoding=encoding)

    @classmethod
    def resource_bytes(cls,path: Union[str, Path]) -> bytes:
        """
        Read a resource as bytes.
        """
        return (cls.resources_path/path).read_bytes()

    @classmethod
    def resource_path(cls, path: Union[str, Path]) -> Path:
        """
        Get the resolved resource path.
        """
        return cls.resources_path/path

    @classmethod
    def resource_as_stream(cls, path: Union[str, Path], mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """
        Get a resource as a binary stream.
        """
        return (cls.resources_path/path).open(mode, buffering, encoding, errors, newline)

    @classmethod
    def is_resource_exists(cls, path: Union[str, Path]) -> bool:
        """
        Check if a resource exists.
        """
        return (cls.resources_path/path).exists()
