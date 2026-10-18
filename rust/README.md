# seltools-rs

Rust (PyO3) versions of `seltools.circular_pairwise` and `seltools.circular_windowed`, imported as `_seltools`.

Install it through the main package and `seltools` uses it automatically:

```bash
pip install "seltools[rust]"
```

Results and errors match the pure-Python implementation; `seltools`'s test suite runs against both. The two packages are released together with the same version.

MIT licensed.
