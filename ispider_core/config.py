# ispider_core/config.py

import copy
import importlib
import types

from ispider_core import settings as default_settings

class Settings:
    def __init__(self):
        self._defaults = default_settings
        self._overrides = {}

    def __getattr__(self, key):
        if key in self._overrides:
            return self._overrides[key]
        return getattr(self._defaults, key)

    def configure(self, **kwargs):
        self._overrides.update(kwargs)

    import types

    def to_dict(self):
        result = {}
        for k in dir(self._defaults):
            if k.startswith("_"):
                continue
            v = getattr(self, k)

            if isinstance(v, types.ModuleType):
                continue

            result[k] = v

        result.update(self._overrides)
        return result

