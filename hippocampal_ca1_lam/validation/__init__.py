import validation as _validation

__path__ = getattr(_validation, "__path__", [])
__spec__ = getattr(_validation, "__spec__", None)
__all__ = getattr(_validation, "__all__", [])


def __getattr__(name):
    return getattr(_validation, name)
