# seltools

Wrap-around access for anything with `len()` and `[]`.

Iterator tools (`itertools`, `more_itertools`) cannot wrap around: going past the end needs the length and random access. seltools asks for exactly those two things, so list, tuple, str, range and numpy arrays all give the same elements.

## Rules

- Each name is `circular_` + the stdlib or more_itertools name of the non-wrapping version, with the same argument order.
- Elements come back as `data[i]` returns them; nothing is converted (an ndarray row stays a view).
- Multi-element results are lazy iterators that read each index once per lap.
- The only requirement is the `Indexable` protocol: `__len__` and `__getitem__(int)`. A dict also satisfies it structurally and fails at runtime with `KeyError`, as with `reversed()`.

Not added, because the standard tools already do it on any container:

| Need | Use |
|---|---|
| `data[key]` as a callable | `operator.itemgetter(key)` |
| index of max / min, with `key=` | `more_itertools.argmax` / `argmin` |
| type-preserving chunks | `more_itertools.sliced` |
| non-wrapping pairs / windows | `itertools.pairwise`, `more_itertools.windowed` |

## Usage

```python
from seltools import circular_getitem, circular_pairwise, circular_windowed

circular_getitem("abc", 4)            # 'b'
circular_getitem(range(5), -6)        # 4, the wrapped index itself
list(circular_pairwise("abc"))        # [('a', 'b'), ('b', 'c'), ('c', 'a')]
list(circular_windowed("abcd", 3))    # [('a', 'b', 'c'), ('b', 'c', 'd'), ('c', 'd', 'a'), ('d', 'a', 'b')]
```

`pure-py-engine` uses `circular_pairwise` for polygon edges (area, centroid, inertia, SAT axes) and `circular_windowed(vertices, 3)` for the convexity check.

## Rust iterators

`src/seltools/core.py` is the reference implementation, built from `itertools` so the loops run in C. `rust/` builds an optional extension, `_seltools` (PyO3), with the same `circular_pairwise` and `circular_windowed`; `seltools` uses it when installed, the way `heapq` uses `_heapq`. `circular_getitem` stays Python: it is one call with no loop, and Python ints have no size limit.

Measured on Windows, Python 3.14, per full iteration (`for _ in ...: pass`):

| | n | generator (before) | core.py | Rust |
|---|---|---|---|---|
| pairwise, list | 4 | 0.92 us | 1.06 us | 0.46 us |
| pairwise, ndarray rows | 4 | 1.85 us | 1.99 us | 0.97 us |
| windowed 3, list | 4 | 3.07 us | 2.53 us | 0.54 us |
| pairwise, list | 1000 | 108 us | 67 us | 60 us |
| pairwise, ndarray rows | 1000 | 345 us | 212 us | 152 us |
| windowed 3, list | 1000 | 715 us | 100 us | 62 us |

ndarray rows stay slow in every version because `ndarray.__getitem__` itself costs about 0.15 us. The Rust iterator indexes objects that have `sq_item` (list, tuple, str, ndarray, classes defining `__getitem__`) with a C integer, and everything else through `data[i]`, so a dict still raises `KeyError`.

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/). No runtime dependencies, not on PyPI. From another project in this repo:

```toml
[tool.uv.sources]
seltools = { path = "../seltools", editable = true }
```

With the Rust iterators (needs a Rust toolchain):

```bash
uv sync --group rust
```

## Test

```bash
uv run --exact --no-group rust pytest   # Python only
uv run --exact --group rust pytest      # Python and Rust
```

Runs the docstring examples and `test_seltools.py` against each installed implementation: list / tuple / ndarray parity, results equal to `itertools.pairwise` and `more_itertools.windowed`, and the number of `data[i]` reads.

## Structure

```
src/seltools/
  core.py       Indexable, circular_getitem, circular_pairwise, circular_windowed
  __init__.py   re-exports, swapping in _seltools when installed
rust/
  src/lib.rs    _seltools: circular_pairwise, circular_windowed
  _seltools.pyi
test_seltools.py
```

## Citation

See [CITATION.cff](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
