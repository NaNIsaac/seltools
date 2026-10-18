import importlib.util
from itertools import chain, cycle, islice, pairwise

import numpy as np
import pytest
from more_itertools import windowed

import seltools
from seltools import circular_getitem, core

ROWS = [[0, 1], [2, 3], [4, 5]]
HAS_RUST = importlib.util.find_spec("_seltools") is not None

if HAS_RUST:
    import _seltools

    IMPLS = [pytest.param(core, id="python"), pytest.param(_seltools, id="rust")]
else:
    IMPLS = [pytest.param(core, id="python")]


def plain(x):
    """Elements as plain lists, so list rows and ndarray rows compare equal."""
    if isinstance(x, tuple):
        return tuple(plain(v) for v in x)
    return x.tolist() if isinstance(x, np.ndarray) else x


class Counted:
    """Only `len` and `[]`, counting the reads."""

    def __init__(self, data):
        self.data = data
        self.reads = 0

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        self.reads += 1
        return self.data[i]


def test_package_uses_rust_when_installed():
    expected = _seltools if HAS_RUST else core
    assert seltools.circular_pairwise is expected.circular_pairwise
    assert seltools.circular_windowed is expected.circular_windowed


@pytest.mark.parametrize("data", [ROWS, tuple(ROWS), np.array(ROWS)], ids=["list", "tuple", "ndarray"])
def test_getitem_any_container(data):
    assert plain(circular_getitem(data, 4)) == [2, 3]
    assert plain(circular_getitem(data, -4)) == [4, 5]


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize("data", [ROWS, tuple(ROWS), np.array(ROWS), Counted(ROWS)], ids=["list", "tuple", "ndarray", "getitem-only"])
def test_same_elements_any_container(impl, data):
    assert [plain(p) for p in impl.circular_pairwise(data)] == [(ROWS[0], ROWS[1]), (ROWS[1], ROWS[2]), (ROWS[2], ROWS[0])]
    assert [plain(w) for w in impl.circular_windowed(data, 3)][-1] == (ROWS[2], ROWS[0], ROWS[1])


@pytest.mark.parametrize("impl", IMPLS)
def test_no_conversion(impl):
    arr = np.arange(6).reshape(3, 2)
    assert np.shares_memory(circular_getitem(arr, 3), arr)
    assert type(circular_getitem(range(3), 5)) is int
    assert all(np.shares_memory(row, arr) for pair in impl.circular_pairwise(arr) for row in pair)


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize("data", ["", "a", "ab", "abcde"])
def test_matches_iterator_tools(impl, data):
    assert list(impl.circular_pairwise(data)) == list(pairwise(chain(data, data[:1])))
    assert list(impl.circular_windowed(data, 0)) == [()] * len(data)
    for n in range(1, 7):
        expected = list(windowed(islice(cycle(data), len(data) + n - 1), n)) if data else []
        assert list(impl.circular_windowed(data, n)) == expected


@pytest.mark.parametrize("impl", IMPLS)
def test_reads_each_index_once_per_lap(impl):
    data = Counted("abcde")
    pairs = impl.circular_pairwise(data)
    assert data.reads == 0  # lazy
    list(pairs)
    assert data.reads == 6
    data.reads = 0
    list(impl.circular_windowed(data, 3))
    assert data.reads == 7


@pytest.mark.parametrize("impl", IMPLS)
def test_errors_like_builtins(impl):
    with pytest.raises(ValueError):
        impl.circular_windowed("ab", -1)
    with pytest.raises(TypeError):
        impl.circular_pairwise(5)
    with pytest.raises(KeyError):
        list(impl.circular_pairwise({0: "a", 2: "b"}))
    with pytest.raises(IndexError):
        circular_getitem([], 0)
