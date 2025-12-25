import data as _data

__path__ = getattr(_data, "__path__", [])
__spec__ = getattr(_data, "__spec__", None)
from data import *  # noqa: F401,F403
__all__ = getattr(_data, "__all__", [])
