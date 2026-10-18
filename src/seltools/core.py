"""Wrap-around access for anything with ``len()`` and ``[]``.

Iterator tools (itertools, more_itertools) cannot wrap around: going past the
end needs the length and random access. These tools ask for exactly that and
nothing more, so list, tuple, str, range and numpy arrays all give the same
elements.

- Each name is ``circular_`` + the stdlib or more_itertools name of the
  non-wrapping version, with the same argument order.
- Elements come back as ``data[i]`` returns them; nothing is converted.
- Multi-element results are lazy iterators, like itertools, and read each
  index once per lap.

This module is the reference implementation. ``seltools`` swaps in the Rust
versions from ``_seltools`` when that is installed.
"""

from collections.abc import Iterator
from itertools import cycle, islice, pairwise, repeat, tee
from typing import Protocol


class Indexable[T](Protocol):
    """What these tools need from `data`: ``len(data)`` and ``data[i]``."""

    def __len__(self) -> int: ...
    def __getitem__(self, i: int, /) -> T: ...


def circular_getitem[T](data: Indexable[T], i: int, /) -> T:
    """``data[i]`` with `i` wrapped around ``len(data)``.

    >>> circular_getitem("abc", 4)
    'b'
    >>> circular_getitem(range(5), -6)  # the wrapped index itself
    4
    """
    n = len(data)
    if n == 0:
        raise IndexError("circular index into empty data")
    return data[i % n]


def circular_pairwise[T](data: Indexable[T], /) -> Iterator[tuple[T, T]]:
    """Like ``itertools.pairwise`` plus the closing pair ``(last, first)``.

    >>> list(circular_pairwise("abc"))
    [('a', 'b'), ('b', 'c'), ('c', 'a')]
    """
    return pairwise(_laps(data, len(data) + 1))


def circular_windowed[T](data: Indexable[T], n: int, /) -> Iterator[tuple[T, ...]]:
    """Like ``more_itertools.windowed`` but windows wrap past the end.

    One window starts at each index, so there are ``len(data)`` windows.

    >>> list(circular_windowed("abcd", 3))
    [('a', 'b', 'c'), ('b', 'c', 'd'), ('c', 'd', 'a'), ('d', 'a', 'b')]
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    size = len(data)
    if n == 0:
        return repeat((), size)
    # n staggered copies of one stream, so each data[i] is read once per lap
    streams = tee(_laps(data, size + n - 1), n)
    return zip(*(islice(s, k, None) for k, s in enumerate(streams)))


def _laps[T](data: Indexable[T], count: int) -> Iterator[T]:
    """``data[0], data[1], ...`` going round, `count` items in all."""
    return map(data.__getitem__, islice(cycle(range(len(data))), count))
