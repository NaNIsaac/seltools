import numpy as np
import pytest

from seltools import Selection, circular_pairs, cyclic

ROWS = [[0, 1], [2, 3], [4, 5]]
CONTAINERS = [ROWS, tuple(ROWS), np.array(ROWS)]


@pytest.mark.parametrize("data", CONTAINERS, ids=["list", "tuple", "ndarray"])
def test_same_elements_any_container(data):
    assert list(Selection(-1)(data)) == [4, 5]
    assert list(cyclic(data, 4)) == [2, 3]
    assert list(cyclic(data, -4)) == [4, 5]
    pairs = [(list(a), list(b)) for a, b in circular_pairs(data)]
    assert pairs == [([0, 1], [2, 3]), ([2, 3], [4, 5]), ([4, 5], [0, 1])]


def test_no_conversion():
    assert type(Selection(slice(1))([1, 2])) is list
    assert type(Selection(slice(1))("ab")) is str
    view = Selection(slice(1))(arr := np.arange(3))
    assert view.base is arr


def test_edges():
    assert list(circular_pairs([])) == []
    assert list(circular_pairs("a")) == [("a", "a")]
    with pytest.raises(IndexError):
        cyclic([], 0)
    with pytest.raises(TypeError):
        Selection(0)(5)
