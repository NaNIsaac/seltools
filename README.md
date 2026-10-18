# seltools

Index-only building blocks, in the spirit of `itertools`.

Every tool touches data only through `len(data)` and `data[i]` / `data[a:b]`, the protocol list, tuple, str and numpy arrays share, so the same call gives the same elements whatever the container.

- Single picks return what the container returns (list slice is a list, ndarray slice is a view). Nothing is converted.
- Multi picks return lazy iterators of elements, never a new container.

No dependencies, not published on PyPI.

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NaNIsaac/seltools.git
cd seltools
uv sync
```

## Usage

```python
from seltools import Selection, circular_pairs, cyclic

Selection(1)([10, 20, 30])         # 20
Selection(slice(0, 2))("abc")      # 'ab'
cyclic([10, 20, 30], 4)            # 20
list(circular_pairs("abc"))        # [('a', 'b'), ('b', 'c'), ('c', 'a')]
```

`pure-py-engine` uses `circular_pairs` for polygon edges.

## Test

```bash
uv run --with numpy --with pytest pytest
```

## Structure

```
src/seltools/
  core.py       Selection, cyclic, circular_pairs
  __init__.py   re-exports
test_seltools.py  list / tuple / ndarray give the same elements
```

## Citation

See [CITATION.cff](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
