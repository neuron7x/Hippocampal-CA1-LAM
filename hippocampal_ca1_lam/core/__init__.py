import core as _core

__path__ = getattr(_core, "__path__", [])
__spec__ = getattr(_core, "__spec__", None)
__all__ = getattr(_core, "__all__", [])


def __getattr__(name):
    return getattr(_core, name)
