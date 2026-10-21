import gc
import importlib.util
import weakref
from itertools import chain, cycle, islice, pairwise

import numpy as np
import pytest
from more_itertools import windowed

import seltools
from seltools import Selection, circular_getitem, core

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


@pytest.mark.parametrize(
    "data",
    [ROWS, tuple(ROWS), np.array(ROWS), Counted(ROWS)],
    ids=["list", "tuple", "ndarray", "getitem-only"],
)
@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (-1, ROWS[2]),
        ([2, 0, 0], [ROWS[2], ROWS[0], ROWS[0]]),
        (np.array([2, -3]), [ROWS[2], ROWS[0]]),
        ([True, False, True], [ROWS[0], ROWS[2]]),
        (np.array([False, True, False]), [ROWS[1]]),
        ([], []),
    ],
)
def test_selection_same_elements_any_container(data, key, expected):
    assert plain(Selection(key)(data)) == expected


def test_selection_is_reusable_value():
    roi = Selection((slice(1, 3), slice(0, 1)))
    image = np.arange(12).reshape(3, 4)
    assert np.shares_memory(roi(image), image)
    assert roi(image).tolist() == [[4], [8]]
    assert roi == Selection((slice(1, 3), slice(0, 1)))
    assert {roi: "a"}[Selection((slice(1, 3), slice(0, 1)))] == "a"
    assert type(Selection(slice(1))([1, 2])) is list
    assert type(Selection(slice(1))("ab")) is str


def test_selection_errors_like_builtins():
    with pytest.raises(IndexError):
        Selection([True, False])("abc")
    with pytest.raises(IndexError):
        Selection([0, 5])("abc")
    with pytest.raises(TypeError):
        Selection(0)(5)
    with pytest.raises(TypeError):
        Selection([0.5])("abc")
    with pytest.raises(TypeError):
        Selection((0, 1))([[1, 2]])  # several axes need numpy


@pytest.mark.parametrize(
    "data", [ROWS, tuple(ROWS), np.array(ROWS)], ids=["list", "tuple", "ndarray"]
)
def test_getitem_any_container(data):
    assert plain(circular_getitem(data, 4)) == [2, 3]
    assert plain(circular_getitem(data, -4)) == [4, 5]


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize(
    "data",
    [ROWS, tuple(ROWS), np.array(ROWS), Counted(ROWS)],
    ids=["list", "tuple", "ndarray", "getitem-only"],
)
def test_same_elements_any_container(impl, data):
    assert [plain(p) for p in impl.circular_pairwise(data)] == [
        (ROWS[0], ROWS[1]),
        (ROWS[1], ROWS[2]),
        (ROWS[2], ROWS[0]),
    ]
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
    with pytest.raises(TypeError, match="not subscriptable"):
        list(impl.circular_pairwise(LenOnly()))
    with pytest.raises(TypeError):
        impl.circular_windowed("ab", 2.0)
    with pytest.raises(MemoryError):
        impl.circular_windowed("ab", 10**18)
    with pytest.raises(IndexError):
        circular_getitem([], 0)


class LenOnly:
    def __len__(self):
        return 3


@pytest.mark.parametrize("impl", IMPLS)
def test_reference_cycle_is_collected(impl):
    class Box(list):
        pass

    box = Box("ab")
    box.append(impl.circular_pairwise(box))
    ref = weakref.ref(box)
    del box
    gc.collect()
    assert ref() is None
