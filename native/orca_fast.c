/* ============================================================================
 * File:    native/orca_fast.c
 * Purpose: CPython extension module providing a fast parser for the
 *          Orca binary sensor frame.
 *
 * Frame layout (little-endian):
 *
 *   offset  size  field
 *   ------  ----  ---------------------------------------------------------
 *   0       1     version    (must be 0x01)
 *   1       1     kind       (0=traffic, 1=air, 2=water, 3=energy, ...)
 *   2       2     sensor_id  (uint16)
 *   4       8     timestamp  (uint64, unix milliseconds)
 *   12      4     value      (float32)
 *   16      1     checksum   (XOR of bytes 0..15)
 *   ------  ----  ---------------------------------------------------------
 *   total:  17 bytes
 *
 * The Python API mirrors what a pure-Python parser would return:
 *
 *     >>> import orca_fast
 *     >>> orca_fast.parse_frame(buf)
 *     {'version': 1, 'kind': 0, 'sensor_id': 42,
 *      'timestamp_ms': 1717000000000, 'value': 12.5}
 *
 * Build:   see native/README.md
 * License: Apache 2.0 (same as the rest of Orca)
 * ==========================================================================*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>

#define FRAME_SIZE 17
#define FRAME_VERSION 0x01

/* Read a little-endian unsigned integer of N bytes from `p`. */
static inline uint64_t rd_le(const unsigned char *p, size_t n) {
    uint64_t v = 0;
    for (size_t i = 0; i < n; ++i) {
        v |= ((uint64_t)p[i]) << (8 * i);
    }
    return v;
}

/* Compute the XOR checksum over the first 16 bytes of the frame. */
static inline unsigned char xor_checksum(const unsigned char *p) {
    unsigned char c = 0;
    for (int i = 0; i < FRAME_SIZE - 1; ++i) c ^= p[i];
    return c;
}

/* parse_frame(buffer: bytes) -> dict
 *
 * Raises ValueError on malformed input. Returns a new dict on success.
 */
static PyObject *orca_parse_frame(PyObject *self, PyObject *args) {
    Py_buffer buf;
    (void)self;

    if (!PyArg_ParseTuple(args, "y*", &buf)) return NULL;

    if (buf.len != FRAME_SIZE) {
        PyBuffer_Release(&buf);
        PyErr_Format(PyExc_ValueError,
                     "expected %d bytes, got %zd", FRAME_SIZE, buf.len);
        return NULL;
    }

    const unsigned char *p = (const unsigned char *)buf.buf;

    if (p[0] != FRAME_VERSION) {
        PyBuffer_Release(&buf);
        PyErr_Format(PyExc_ValueError, "unsupported frame version: %u", p[0]);
        return NULL;
    }

    if (xor_checksum(p) != p[FRAME_SIZE - 1]) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "frame checksum mismatch");
        return NULL;
    }

    uint8_t  kind        = p[1];
    uint16_t sensor_id   = (uint16_t)rd_le(p + 2, 2);
    uint64_t timestamp   = rd_le(p + 4, 8);

    /* Memcpy into a float to honor strict aliasing rules. */
    float value;
    memcpy(&value, p + 12, sizeof(float));

    PyBuffer_Release(&buf);

    return Py_BuildValue(
        "{s:i, s:i, s:i, s:K, s:d}",
        "version",      (int)FRAME_VERSION,
        "kind",         (int)kind,
        "sensor_id",    (int)sensor_id,
        "timestamp_ms", (unsigned long long)timestamp,
        "value",        (double)value
    );
}

/* ---- Module boilerplate ------------------------------------------------- */

static PyMethodDef SmartcitoMethods[] = {
    {"parse_frame", orca_parse_frame, METH_VARARGS,
     "Parse a 17-byte Orca binary sensor frame into a dict."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef orca_module = {
    PyModuleDef_HEAD_INIT,
    "orca_fast",
    "Orca C accelerators (binary frame parser).",
    -1,
    SmartcitoMethods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_orca_fast(void) {
    return PyModule_Create(&orca_module);
}
