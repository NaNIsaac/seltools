import pytest

from seltools import Selection, circular_getitem, circular_pairwise, circular_windowed

CONTAINERS = ["abcd", list("abcd"), tuple("abcd")]


@pytest.mark.parametrize("data", CONTAINERS)
@pytest.mark.parametrize(("i", "expected"), [(0, "a"), (3, "d"), (4, "a"), (-5, "d"), (9, "b")])
def test_getitem_wraps(data, i, expected):
    assert circular_getitem(data, i) == expected


def test_getitem_empty_raises():
    with pytest.raises(IndexError):
        circular_getitem([], 0)


@pytest.mark.parametrize("data", CONTAINERS)
def test_pairwise_closes_the_ring(data):
    assert list(circular_pairwise(data)) == [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]


def test_pairwise_single_element_pairs_with_itself():
    assert list(circular_pairwise([7])) == [(7, 7)]


@pytest.mark.parametrize("data", CONTAINERS)
def test_windowed_starts_at_every_index(data):
    assert list(circular_windowed(data, 3)) == [
        ("a", "b", "c"),
        ("b", "c", "d"),
        ("c", "d", "a"),
        ("d", "a", "b"),
    ]


def test_windowed_longer_than_data_goes_round_again():
    assert list(circular_windowed("ab", 3)) == [("a", "b", "a"), ("b", "a", "b")]


def test_windowed_zero_gives_empty_windows():
    assert list(circular_windowed("abc", 0)) == [(), (), ()]


def test_windowed_negative_raises():
    with pytest.raises(ValueError, match="n must be >= 0"):
        circular_windowed("abc", -1)


@pytest.mark.parametrize("data", CONTAINERS)
def test_selection_is_reusable(data):
    pick = Selection([0, -1])
    assert pick(data) == ["a", "d"]
    assert pick(data) == ["a", "d"]


def test_selection_slice_and_index_pass_through():
    assert Selection(slice(1, None))("abcd") == "bcd"
    assert Selection(2)("abcd") == "c"


def test_selection_bool_mask():
    assert Selection([True, False, False, True])("abcd") == ["a", "d"]
    with pytest.raises(IndexError, match="boolean index of length 2"):
        Selection([True, False])("abcd")
