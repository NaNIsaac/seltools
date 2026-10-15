from collections.abc import Hashable
from typing import Any


class Selection:
    """Callable that picks `data[key]`; the key may be an index, slice or mapping key."""

    def __init__(self, key: Hashable | slice) -> None:
        self.key = key

    def __call__(self, data: Any) -> Any:
        if not hasattr(data, "__getitem__"):
            raise TypeError(f"'{type(data).__name__}' object is not subscriptable")
        return data[self.key]

    def __repr__(self) -> str:
        return f"Selection({self.key!r})"
