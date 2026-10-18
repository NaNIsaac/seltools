# seltools

Wrap-around access for anything with `len()` and `[]`.

Iterator tools (`itertools`, `more_itertools`) cannot wrap around: going past the end needs the length and random access. seltools asks for exactly those two things, so list, tuple, str, range and numpy arrays all give the same elements.

## Rules

- Each name is `circular_` + the stdlib or more_itertools name of the non-wrapping version, with the same argument order.
- Elements come back as `data[i]` returns them; nothing is converted (an ndarray row stays a view).
- Multi-element results are lazy iterators.
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

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/). No runtime dependencies, not on PyPI. From another project in this repo:

```toml
[tool.uv.sources]
seltools = { path = "../seltools", editable = true }
```

## Test

```bash
uv run pytest
```

Runs the docstring examples and `test_seltools.py`, which checks list / tuple / ndarray parity and compares results against `itertools.pairwise` and `more_itertools.windowed`.

## Structure

```
src/seltools/
  core.py       Indexable, circular_getitem, circular_pairwise, circular_windowed
  __init__.py   re-exports
test_seltools.py
```

## Citation

See [CITATION.cff](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
