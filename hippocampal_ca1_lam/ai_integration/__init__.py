import ai_integration as _ai_integration

__path__ = getattr(_ai_integration, "__path__", [])
__spec__ = getattr(_ai_integration, "__spec__", None)
__all__ = getattr(_ai_integration, "__all__", [])


def __getattr__(name):
    return getattr(_ai_integration, name)
