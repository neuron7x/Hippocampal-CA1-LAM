import plasticity as _plasticity

__path__ = getattr(_plasticity, "__path__", [])
__spec__ = getattr(_plasticity, "__spec__", None)
__all__ = getattr(_plasticity, "__all__", [])


def __getattr__(name):
    return getattr(_plasticity, name)
