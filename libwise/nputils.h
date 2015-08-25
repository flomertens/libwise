typedef enum
{
	EXT_ZERO = 0, 
	EXT_SYMM = 1, 
	EXT_PER = 2,
    EXT_BORDER = 3
} Extension;


void nputils_convolve(double* a, double* v, long size_a, long size_v,
		unsigned ext_type, double** res);


long nputils_get_convolution_size(long size_a, long size_v);


long nputils_get_extended_index(long index, long size, long ext_size,
		unsigned ext_type);
