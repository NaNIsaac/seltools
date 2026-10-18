from typing import TYPE_CHECKING

from seltools.core import (
    Indexable,
    circular_getitem,
    circular_pairwise,
    circular_windowed,
)

if not TYPE_CHECKING:  # type checkers keep the reference signatures above
    try:
        from _seltools import circular_pairwise, circular_windowed
    except ImportError:
        pass

__all__ = ["Indexable", "circular_getitem", "circular_pairwise", "circular_windowed"]
