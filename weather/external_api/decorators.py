import os
from functools import wraps

from django.core.cache import cache


def cached_data(prefix: str, timeout: int = None):
    """
    Декоратор для кэширования данных погоды.
    Формирует ключ как: "<prefix>:<city.lower()>"
    """
    timeout = timeout or int(os.getenv("CACHE_TIMEOUT", 600))

    def decorator(func):
        @wraps(func)
        def wrapper(self, city: str, *args, **kwargs):
            cache_key = f"{prefix}:{city.lower()}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(self, city, *args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator
