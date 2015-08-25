import numpy as np
cimport numpy as np
from numpy import exp, pi


CONV_BOUNDARY_MAP = {"zero": 0,
                     "symm": 1,
                     "wrap": 2,
                     "border": 3}


cdef extern from "nputils.h":
    void nputils_convolve(double* a, double* v, long size_a, long size_v,
        unsigned boundary, double** res)

    long nputils_get_convolution_size(long size_a, long size_v)

    long nputils_get_extended_index(long index, long size, long ext_size,
        unsigned boundary)


cdef convolve_c(np.ndarray[double] a, np.ndarray[double] v, boundary):
    res_size = nputils_get_convolution_size(len(a), len(v))

    cdef np.ndarray[double] res = np.zeros(res_size, dtype=np.double)
    
    nputils_convolve(<double*> a.data, <double*> v.data, 
            len(a), len(v), boundary, <double**> &res.data)

    return res


def get_extended_index(index, size, ext_size, boundary):
    return nputils_get_extended_index(index, size, ext_size, boundary)


def convolve(a, v, boundary, mode):
    if a.dtype == np.complex:
        real = convolve(a.real, v, boundary, mode)
        imag = convolve(a.real, v, boundary, mode)
        res = real + 1j * imag
    else:
        v = np.asarray(v).astype(np.double)
        boundary = CONV_BOUNDARY_MAP[boundary]
        a = np.asarray(a).astype(np.double)
        res = convolve_c(a, v, boundary)
    
    if mode == 'same':
        l = (len(v) - 1) / 2
        r = (len(v) - 1) - l
        res = res[l:-r]
    elif mode == 'valid':
        res = res[len(v) - 1:-(len(v) - 1)]
    return res
