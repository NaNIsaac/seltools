//! Rust versions of the seltools iterators. Same contract as `seltools.core`:
//! only `len(data)` and `data[i]`, each index read once per lap.

use std::collections::VecDeque;

use pyo3::exceptions::{PyMemoryError, PyValueError};
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::{PyTraverseError, PyVisit};
use pyo3::types::PyTuple;

/// Iterator returned by `circular_pairwise` and `circular_windowed`.
#[pyclass(module = "_seltools")]
struct CircularWindowed {
    // None once the garbage collector has cleared it
    data: Option<Py<PyAny>>,
    size: usize,
    // has sq_item: index with a C integer instead of a new Python int per read
    is_sequence: bool,
    n: usize,
    produced: usize,
    next_index: usize,
    window: VecDeque<Py<PyAny>>,
}

impl CircularWindowed {
    fn read_next(&mut self, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let index = self.next_index % self.size;
        let item = if self.is_sequence {
            // SAFETY: data is a live object and index < len(data) fits in Py_ssize_t
            unsafe { Bound::from_owned_ptr_or_err(data.py(), ffi::PySequence_GetItem(data.as_ptr(), index as ffi::Py_ssize_t))? }
        } else {
            data.get_item(index)?
        };
        self.window.push_back(item.unbind());
        self.next_index += 1;
        Ok(())
    }
}

#[pymethods]
impl CircularWindowed {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__<'py>(&mut self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        let Some(data) = &self.data else {
            return Ok(None);
        };
        if self.produced == self.size {
            return Ok(None);
        }
        // read lazily, so an error from data[i] surfaces on the window that needs it
        let data = data.bind(py).clone();
        if self.produced > 0 && self.n > 0 {
            self.window.pop_front();
            self.read_next(&data)?;
        }
        while self.window.len() < self.n {
            self.read_next(&data)?;
        }
        self.produced += 1;
        PyTuple::new(py, self.window.iter().map(|item| item.bind(py))).map(Some)
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.data)?;
        for item in &self.window {
            visit.call(item)?;
        }
        Ok(())
    }

    fn __clear__(&mut self) {
        self.data = None;
        self.window.clear();
    }
}

fn windowed(data: &Bound<'_, PyAny>, n: usize) -> PyResult<CircularWindowed> {
    // a failed allocation would abort the interpreter; raise MemoryError like tee() does
    let mut window = VecDeque::new();
    window.try_reserve_exact(n).map_err(|_| PyMemoryError::new_err(()))?;
    Ok(CircularWindowed {
        data: Some(data.clone().unbind()),
        size: data.len()?,
        // SAFETY: data is a live object; PySequence_Check only reads its type slots
        is_sequence: unsafe { ffi::PySequence_Check(data.as_ptr()) } == 1,
        n,
        produced: 0,
        next_index: 0,
        window,
    })
}

/// Like itertools.pairwise plus the closing pair (last, first).
#[pyfunction]
#[pyo3(signature = (data, /))]
fn circular_pairwise(data: &Bound<'_, PyAny>) -> PyResult<CircularWindowed> {
    windowed(data, 2)
}

/// Like more_itertools.windowed but windows wrap past the end; one window per index.
#[pyfunction]
#[pyo3(signature = (data, n, /))]
fn circular_windowed(data: &Bound<'_, PyAny>, n: isize) -> PyResult<CircularWindowed> {
    if n < 0 {
        return Err(PyValueError::new_err("n must be >= 0"));
    }
    windowed(data, n as usize)
}

#[pymodule]
fn _seltools(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(circular_pairwise, m)?)?;
    m.add_function(wrap_pyfunction!(circular_windowed, m)?)?;
    Ok(())
}
