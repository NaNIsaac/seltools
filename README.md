# seltools

Moved into a private scratch repo; no longer maintained.

Early-stage Python package for callable selectors that index data.

It currently contains one class, `Selection` in `src/seltools/core.py`. A `Selection` holds a key (index, slice or mapping key) and returns `data[key]` when called; it raises `TypeError` if the data is not subscriptable. The package has no dependencies and is not published on PyPI.

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NaNIsaac/seltools.git
cd seltools
uv sync
```

## Usage

```python
from seltools import Selection

Selection(1)([10, 20, 30])        # 20
Selection(slice(0, 2))("abc")     # 'ab'
Selection("a")({"a": 5})          # 5
```

## Structure

```
src/seltools/
  core.py       Selection
  __init__.py   re-exports Selection
```

## Citation

See [CITATION.cff](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
