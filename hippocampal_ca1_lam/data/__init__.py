import data as _data

__path__ = getattr(_data, "__path__", [])
__spec__ = getattr(_data, "__spec__", None)
__all__ = getattr(_data, "__all__", [])


def __getattr__(name):
    return getattr(_data, name)
