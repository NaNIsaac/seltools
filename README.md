# seltools

[![Tests](https://github.com/NaNIsaac/seltools/actions/workflows/ci.yml/badge.svg)](https://github.com/NaNIsaac/seltools/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Reusable selections and wrap-around access for anything with `len()` and `[]`.

`itertools` and `more_itertools` cannot wrap around: going past the end needs the length of the data and random access to its start, and an iterator has neither. seltools asks for exactly those two things, so a list, tuple, str, range, NumPy array or any class defining `__len__` and `__getitem__` gives the same elements.

```python
>>> from seltools import circular_getitem, circular_pairwise, circular_windowed
>>> circular_getitem("ABC", 4)
'B'
>>> list(circular_pairwise("ABCD"))
[('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A')]
>>> list(circular_windowed("ABCD", 3))
[('A', 'B', 'C'), ('B', 'C', 'D'), ('C', 'D', 'A'), ('D', 'A', 'B')]
```

## Selection

`Selection(key)` keeps an index as a value, the way a region of interest keeps its bounds: build it once, apply it to any container, store or compare it.

```python
>>> import numpy as np
>>> from seltools import Selection
>>> roi = Selection((slice(1, 3), slice(0, 2)))
>>> roi(np.arange(12).reshape(3, 4))
array([[4, 5],
       [8, 9]])
>>> ends = Selection([0, -1])
>>> ends("abc"), ends(np.array([10, 20, 30]))
(['a', 'c'], array([10, 30]))
>>> Selection([True, False, True])("abc")
['a', 'c']
```

Any key the container accepts is passed through as `data[key]`, so ndarray slices stay views. A list or array of ints or bools (fancy indexing) also works on list, tuple, str, range and anything else that takes a single index; the picks then come back as a list.

## Install

```bash
pip install seltools          # pure Python, no dependencies
pip install "seltools[rust]"  # adds the compiled iterators from seltools-rs
```

Requires Python 3.14.

From a clone of this repository, install it into a throwaway environment and check that it imports and wraps around. The command exits non-zero if it does not.

<!-- test -->
```sh
uv run --with . python -c "from seltools import circular_getitem; assert circular_getitem('ABC', 4) == 'B'"
```

## Tools

| Tool | Results | Non-wrapping version |
|---|---|---|
| `circular_getitem(data, i)` | `data[i % len(data)]` | `operator.getitem` |
| `circular_pairwise(data)` | `(d[0], d[1]), ..., (d[-1], d[0])` | `itertools.pairwise` |
| `circular_windowed(data, n)` | one `n`-tuple starting at each index | `more_itertools.windowed` |

`Indexable[T]` is the `typing.Protocol` they accept: `__len__` and `__getitem__` with an `int`.

All tools follow the same rules:

- Each name is `circular_` + the name of the non-wrapping version, with the same arguments in the same order.
- Elements come back exactly as `data[i]` returns them. Nothing is converted: an ndarray row is still a view.
- Multi-element results are lazy iterators that read each index once per lap, and raise the same errors as `data[i]` would.

Other non-wrapping tools are left to the libraries that already have them: `more_itertools.argmax` / `argmin`, `more_itertools.sliced`, `more_itertools.circular_shifts`.

## Rust iterators

`seltools.core` is the reference implementation, built from `itertools` so its loops run in C. The `seltools-rs` package provides the same `circular_pairwise` and `circular_windowed` as a PyO3 extension, `_seltools`; `seltools` uses it when it is installed, the way `heapq` uses `_heapq`. Both are tested against each other for results, errors, laziness and the number of `data[i]` reads. The extension supports free-threaded builds.

Measured on Windows with CPython 3.14, for a full iteration:

| Iteration | n | Pure Python | Rust |
|---|---|---|---|
| pairwise, list | 4 | 1.06 µs | 0.46 µs |
| pairwise, ndarray rows | 4 | 1.99 µs | 0.97 µs |
| windowed 3, list | 4 | 2.53 µs | 0.54 µs |
| pairwise, list | 1000 | 67 µs | 60 µs |
| pairwise, ndarray rows | 1000 | 212 µs | 152 µs |
| windowed 3, list | 1000 | 100 µs | 62 µs |

ndarray rows stay slow in both because `ndarray.__getitem__` itself costs about 0.15 µs.

## Documentation

The full reference, with "roughly equivalent" code for each tool and tested recipes (polygon area, perimeter, convexity, ring neighbours, periodic moving average), is in `docs/`, written for Sphinx with the theme of docs.python.org.

## Development

Uses [uv](https://docs.astral.sh/uv/). The Rust extension needs a Rust toolchain.

```bash
uv run --exact pytest                    # pure Python
uv run --exact --extra rust pytest       # pure Python and Rust
uv run --exact --group docs --group dev sphinx-build -W -b doctest docs docs/_build/doctest
uv run --exact --group docs --group dev sphinx-build -W -b html docs docs/_build/html
```

`seltools` and `seltools-rs` are released together with the same version; the `rust` extra pins it exactly.

```bash
uv build                                        # seltools sdist and wheel
cd rust && uvx maturin build --release --sdist  # seltools-rs, one wheel per interpreter
```

```
src/seltools/
  core.py         Indexable, circular_getitem, circular_pairwise, circular_windowed
  __init__.py     re-exports, swapping in _seltools when installed
rust/             seltools-rs: src/lib.rs, _seltools.pyi
docs/             Sphinx sources
test_seltools.py
```

## License

MIT. Citation metadata is in `CITATION.cff`.
