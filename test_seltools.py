from itertools import chain, cycle, islice, pairwise

import numpy as np
import pytest
from more_itertools import windowed

from seltools import circular_getitem, circular_pairwise, circular_windowed

ROWS = [[0, 1], [2, 3], [4, 5]]


def plain(x):
    """Elements as plain lists, so list rows and ndarray rows compare equal."""
    if isinstance(x, tuple):
        return tuple(plain(v) for v in x)
    return x.tolist() if isinstance(x, np.ndarray) else x


@pytest.mark.parametrize("data", [ROWS, tuple(ROWS), np.array(ROWS)], ids=["list", "tuple", "ndarray"])
def test_same_elements_any_container(data):
    assert plain(circular_getitem(data, 4)) == [2, 3]
    assert plain(circular_getitem(data, -4)) == [4, 5]
    assert [plain(p) for p in circular_pairwise(data)] == [(ROWS[0], ROWS[1]), (ROWS[1], ROWS[2]), (ROWS[2], ROWS[0])]
    assert [plain(w) for w in circular_windowed(data, 3)][-1] == (ROWS[2], ROWS[0], ROWS[1])


def test_no_conversion():
    arr = np.arange(6).reshape(3, 2)
    assert np.shares_memory(circular_getitem(arr, 3), arr)
    assert type(circular_getitem(range(3), 5)) is int


@pytest.mark.parametrize("data", ["", "a", "ab", "abcde"])
def test_matches_iterator_tools(data):
    assert list(circular_pairwise(data)) == list(pairwise(chain(data, data[:1])))
    for n in range(1, 7):
        expected = list(windowed(islice(cycle(data), len(data) + n - 1), n)) if data else []
        assert list(circular_windowed(data, n)) == expected


def test_errors_like_builtins():
    with pytest.raises(IndexError):
        circular_getitem([], 0)
    with pytest.raises(ValueError):
        circular_windowed("ab", -1)
    with pytest.raises(TypeError):
        circular_getitem(5, 0)
