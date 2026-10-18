"""Index-only building blocks.

Every tool touches `data` only through `len(data)` and `data[i]` / `data[a:b]`.
That is the protocol list, tuple, str, numpy arrays and most Sequence-likes
share, so the same call gives the same elements whatever the container.

- Single picks return what the container returns (list slice -> list,
  ndarray slice -> view). Nothing is converted.
- Multi picks return lazy iterators of elements, never a new container.
"""

from collections.abc import Hashable, Iterator
from typing import Any


class Selection:
    """`data[key]` as a value: build the key once, apply it to any container."""

    def __init__(self, key: Hashable | slice) -> None:
        self.key = key

    def __call__(self, data: Any) -> Any:
        return data[self.key]

    def __repr__(self) -> str:
        return f"Selection({self.key!r})"


def cyclic(data: Any, i: int) -> Any:
    """`data[i]` with `i` wrapped around `len(data)`."""
    n = len(data)
    if n == 0:
        raise IndexError("cyclic index into empty data")
    return data[i % n]


def circular_pairs(data: Any) -> Iterator[tuple[Any, Any]]:
    """`(data[0], data[1]), ..., (data[-1], data[0])`: the edges of a closed loop."""
    n = len(data)
    return ((data[i], data[(i + 1) % n]) for i in range(n))
