:mod:`!seltools` --- Wrap-around access for anything with ``len()`` and ``[]``
==============================================================================

.. module:: seltools
   :synopsis: Circular getitem, pairwise and windowed for indexable containers.

--------------

This module provides a small set of tools for walking a container as if its
end were joined to its beginning: the edges of a closed polygon, the neighbours
of a vertex in a ring buffer, the windows of a periodic signal.

The iterator modules :mod:`itertools` and `more_itertools
<https://more-itertools.readthedocs.io>`_ cannot do this on their own. Going
past the end needs the length of the data and random access to its start, and
an iterator has neither. These tools ask for exactly those two things and
nothing more, so a :class:`list`, :class:`tuple`, :class:`str`,
:class:`range`, NumPy :class:`~numpy.ndarray` or any class defining
:meth:`~object.__len__` and :meth:`~object.__getitem__` gives the same elements.

All tools follow the same rules:

* Each name is ``circular_`` followed by the name of the non-wrapping
  version in the standard library or more-itertools, with the same arguments
  in the same order.
* Elements are returned exactly as ``data[i]`` returns them. Nothing is
  converted: an ndarray row is still a view into the array.
* Multi-element results are lazy iterators, like those of :mod:`itertools`,
  and read each index once per lap around the data.

**Tools:**

==============================  ================  ==========================================  ===============================================================
Tool                            Arguments         Results                                     Example
==============================  ================  ==========================================  ===============================================================
:func:`circular_getitem`        data, i           ``data[i % len(data)]``                     ``circular_getitem('ABC', 4) → 'B'``
:func:`circular_pairwise`       data              (d[0], d[1]), ..., (d[-1], d[0])            ``circular_pairwise('ABC') → AB BC CA``
:func:`circular_windowed`       data, n           one *n*-tuple starting at each index        ``circular_windowed('ABCD', 3) → ABC BCD CDA DAB``
==============================  ================  ==========================================  ===============================================================


.. _seltools-functions:

Seltools functions
------------------

.. function:: circular_getitem(data, i, /)

   Return ``data[i]`` with *i* wrapped around ``len(data)``, so any integer is
   a valid index.  Raise :exc:`IndexError` if *data* is empty.

   Roughly equivalent to::

      def circular_getitem(data, i):
          return data[i % len(data)]

   Because the index is wrapped with ``%``, negative indices count from the
   end and may go round more than once::

      >>> from seltools import circular_getitem
      >>> circular_getitem('ABC', -4)
      'C'

   Pass a :class:`range` to get the wrapped index itself rather than an
   element::

      >>> circular_getitem(range(5), 12)
      2


.. function:: circular_pairwise(data, /)

   Return the successive overlapping pairs of *data*, followed by the pair
   that closes the loop, ``(data[-1], data[0])``.  There are ``len(data)``
   pairs; empty *data* gives none, and a single element is paired with
   itself.

   Roughly equivalent to::

      def circular_pairwise(data):
          return circular_windowed(data, 2)

   This is :func:`itertools.pairwise` for a closed loop::

      >>> from itertools import pairwise
      >>> from seltools import circular_pairwise
      >>> list(pairwise('ABCD'))
      [('A', 'B'), ('B', 'C'), ('C', 'D')]
      >>> list(circular_pairwise('ABCD'))
      [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A')]


.. function:: circular_windowed(data, n, /)

   Return the overlapping windows of width *n* over *data*, wrapping past the
   end.  One window starts at each index, so there are ``len(data)`` windows
   whatever *n* is; a window wider than the data goes round more than once.

   *n* must be a non-negative integer.  Raise :exc:`ValueError` if it is
   negative and :exc:`TypeError` if it is not an integer.

   Roughly equivalent to::

      from collections import deque

      def circular_windowed(data, n):
          size = len(data)
          if n == 0:
              yield from [()] * size
              return
          window = deque(maxlen=n)
          for k in range(size + n - 1 if size else 0):
              window.append(data[k % size])
              if len(window) == n:
                  yield tuple(window)

   Compared with :func:`more_itertools.windowed`, the last ``n - 1`` windows
   borrow from the start::

      >>> from more_itertools import windowed
      >>> from seltools import circular_windowed
      >>> list(windowed('ABCD', 3))
      [('A', 'B', 'C'), ('B', 'C', 'D')]
      >>> list(circular_windowed('ABCD', 3))
      [('A', 'B', 'C'), ('B', 'C', 'D'), ('C', 'D', 'A'), ('D', 'A', 'B')]


.. class:: Indexable[T]

   A :class:`typing.Protocol` for what the tools need from *data*:
   :meth:`~object.__len__` and :meth:`~object.__getitem__` with an
   :class:`int`.  Use it to annotate functions that accept the same
   containers::

      from seltools import Indexable, circular_pairwise

      def perimeter(points: Indexable[tuple[float, float]]) -> float:
          ...

   The protocol is narrower than :class:`collections.abc.Sequence`, which
   NumPy arrays are not registered as.  It is the same contract
   :func:`reversed` relies on, and has the same blind spot: a :class:`dict`
   matches it structurally, then fails at the first read with
   :exc:`KeyError`.


Containers and errors
---------------------

The tools read *data* only with :func:`len` and ``data[i]``, where *i* is a
non-negative :class:`int` below ``len(data)``.  The length is taken once, when
the tool is called.  Reads happen as the iterator advances, so an error from
``data[i]`` surfaces on the item that needs it:

.. doctest::

   >>> from seltools import circular_pairwise
   >>> it = circular_pairwise({0: 'a', 2: 'b'})
   >>> next(it)
   Traceback (most recent call last):
     ...
   KeyError: 1

Errors match the builtins: an object without :meth:`~object.__getitem__`
raises :exc:`TypeError` (``object is not subscriptable``), and data that
shrinks while it is being iterated raises :exc:`IndexError`.

NumPy arrays index along the first axis, so each element is a row view:

.. doctest::

   >>> import numpy as np
   >>> from seltools import circular_pairwise
   >>> square = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
   >>> a, b = next(circular_pairwise(square))
   >>> b
   array([1, 0])
   >>> np.shares_memory(b, square)
   True


Rust iterators
--------------

The functions documented above are implemented in pure Python with
:mod:`itertools`, so their loops run in C.  The optional ``seltools-rs``
package provides the same :func:`circular_pairwise` and
:func:`circular_windowed` as a compiled extension, ``_seltools``.  When it is
installed, :mod:`seltools` uses it automatically, in the way :mod:`heapq`
uses its C accelerator::

   pip install "seltools[rust]"

The two implementations are tested against each other for results, errors,
laziness and the number of ``data[i]`` reads.  The pure-Python versions stay
importable as :mod:`!seltools.core`.  :func:`circular_getitem` has no Rust
version: it is a single call with no loop, and Python integers have no size
limit.

Measured on Windows with CPython 3.14, for a full iteration
(``for _ in ...: pass``):

==========================  ======  ===========  ===========
Iteration                   n       Pure Python  Rust
==========================  ======  ===========  ===========
pairwise, list              4       1.06 µs      0.46 µs
pairwise, ndarray rows      4       1.99 µs      0.97 µs
windowed 3, list            4       2.53 µs      0.54 µs
pairwise, list              1000    67 µs        60 µs
pairwise, ndarray rows      1000    212 µs       152 µs
windowed 3, list            1000    100 µs       62 µs
==========================  ======  ===========  ===========

The extension supports free-threaded builds and does not re-enable the GIL.


What is not here
----------------

Tools that do not need to wrap around are left to the libraries that already
provide them for any container:

==========================================  =====================================================
Need                                        Use
==========================================  =====================================================
``data[key]`` as a callable                 :func:`operator.itemgetter`
Index of the largest or smallest item       :func:`more_itertools.argmax`, :func:`more_itertools.argmin`
Chunks that keep the container type         :func:`more_itertools.sliced`
Pairs and windows without wrapping          :func:`itertools.pairwise`, :func:`more_itertools.windowed`
Every rotation of the data                  :func:`more_itertools.circular_shifts`
==========================================  =====================================================


.. _seltools-recipes:

Seltools recipes
----------------

These recipes show the tools on closed shapes and rings.  They are written for
clarity rather than speed and are tested as part of the documentation.

.. testcode::

   import math
   from seltools import circular_getitem, circular_pairwise, circular_windowed

   def shoelace_area(points):
       "Signed area of a polygon; positive when the points run counter-clockwise."
       return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in circular_pairwise(points)) / 2

   def perimeter(points):
       "Length of the closed path through the points."
       return sum(math.dist(p, q) for p, q in circular_pairwise(points))

   def is_convex(points):
       "True if every turn of a counter-clockwise polygon is a left turn or straight."
       return all(
           (bx - ax) * (cy - by) - (by - ay) * (cx - bx) >= 0
           for (ax, ay), (bx, by), (cx, cy) in circular_windowed(points, 3)
       )

   def neighbours(data, i):
       "The items on either side of data[i] in a ring."
       return circular_getitem(data, i - 1), circular_getitem(data, i + 1)

   def rotated(data, k):
       "Iterate over data starting at index k and going round once."
       return (circular_getitem(data, k + j) for j in range(len(data)))

   def circular_moving_average(values, n):
       "Mean of each window of n values, treating the values as periodic."
       return [sum(window) / n for window in circular_windowed(values, n)]

.. doctest::

   >>> square = [(0, 0), (2, 0), (2, 2), (0, 2)]
   >>> shoelace_area(square), shoelace_area(square[::-1])
   (4.0, -4.0)
   >>> perimeter(square)
   8.0
   >>> is_convex(square), is_convex([(0, 0), (2, 0), (1, 0.5), (1, 2)])
   (True, False)
   >>> neighbours('ABCDE', 0)
   ('E', 'B')
   >>> ''.join(rotated('ABCDE', 3))
   'DEABC'
   >>> circular_moving_average([1, 2, 3, 4], 2)
   [1.5, 2.5, 3.5, 2.5]
