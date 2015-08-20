#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <complex.h>

#include "nputils.h"


void nputils_convolve(double* a, double* v, long size_a, long size_v,
		unsigned ext_type, double** res)
{
	long size_res = nputils_get_convolution_size(size_a, size_v);
	long a_index = 0;
	double value = 0;

	long i, j;

	for (i = 0; i < size_res; i++)
	{
		value = 0;
		for (j = 0; j < size_v; j++)
		{
			a_index = nputils_get_extended_index(i - j, size_a, size_v -1, ext_type);
			if (a_index >= 0 && a_index < size_a)
			{
				value += v[j] * a[a_index];
			}
		}
		(*res)[i] = value;
	}
}


long nputils_get_convolution_size(long size_a, long size_v)
{
	return size_a + size_v - 1;
}


long nputils_get_extended_index(long index, long size, long ext_size,
		unsigned ext_type)
{
	if (index < 0)
	{
		switch (ext_type)
		{
		case EXT_SYMM:
			index = -index - 1;
			break;
		case EXT_PER:
			index = size + index;
			break;
		case EXT_BORDER:
			index = 0;
		default:
			break;
		}
	}
	else if (index >= size)
	{
		switch (ext_type)
		{
		case EXT_SYMM:
			index = 2 * size - index - 1;
			break;
		case EXT_PER:
			index = index - size;
			break;
		case EXT_BORDER:
			index = size - 1;
		default:
			break;
		}
	}
	return index;
}
