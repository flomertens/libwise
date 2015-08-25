'''
Created on Feb 10, 2012

@author: fmertens
'''
import datetime
import numpy as np
from scipy.signal import convolve2d

from libwise import nputils
from libwise import nputils_c
from libwise.nputils import assert_equal, assert_raise


def _a(x):
    return np.array(x)


def test_get_points_around():
    l = np.zeros([10, 10])

    res = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)]
    assert nputils.get_points_around(l, [2, 2]) == res

    res = [(3, 1), (3, 2), (3, 3)]
    assert nputils.get_points_around(l, [2, 2], direction=[1, 0]) == res

    res = [(2, 3), (3, 2), (3, 3)]
    assert nputils.get_points_around(l, [2, 2], direction=[1, 1]) == res

    res = [(1, 1), (2, 1), (3, 1)]
    assert nputils.get_points_around(l, [2, 2], direction=[0, -1]) == res

    res = [(1, 1), (1, 2), (2, 1)]
    assert nputils.get_points_around(l, [2, 2], direction=[-1, -1]) == res


# def test_diff_around():
#     l = np.arange(9).reshape([3, 3])

#     res = ([(1, 2), (2, 1), (2, 2)], [6, 2, 4])
#     assert nputils.diff_around(l, [0, 0], [1, 1]) == res


def test_upscale():
    assert_equal(nputils.upsample([1, 2, 3, 4], 2),
                 [1, 0, 2, 0, 3, 0, 4, 0])
    assert_equal(nputils.upsample([1, 2, 3, 4], 2, 1),
                 [0, 1, 0, 2, 0, 3, 0, 4])
    assert_equal(nputils.upsample([1, 2, 3, 4], 1),
                 [1, 2, 3, 4])
    assert_raise(ValueError, nputils.upsample, [1, 2, 3, 4], 0)
    assert_raise(ValueError, nputils.upsample, [1, 2, 3, 4], -20)
    assert_equal(nputils.upsample([1, 2, 3], 3),
                 [1, 0, 0, 2, 0, 0, 3, 0, 0])
    assert_equal(nputils.upsample([1, 2, 3], 3, 1),
                 [0, 1, 0, 0, 2, 0, 0, 3, 0])
    a = [[1, 2], [3, 4]]
    exp = [[1, 0, 2, 0], [0, 0, 0, 0], [3, 0, 4, 0], [0, 0, 0, 0]]
    assert_equal(nputils.upsample(a, 2, 0), exp)
    exp = [[1, 0, 2, 0], [3, 0, 4, 0]]
    assert_equal(nputils.upsample(a, 2, 0, axis=1), exp)
    exp = [[0, 0], [1, 2], [0, 0], [3, 4]]
    assert_equal(nputils.upsample(a, 2, 1, axis=0), exp)


def test_atrou():
    assert_equal(nputils.atrou([1, 2, 3, 4], 2),
                 [1, 0, 2, 0, 3, 0, 4])
    assert_equal(nputils.atrou([1, 2, 3, 4], 3),
                 [1, 0, 0, 2, 0, 0, 3, 0, 0, 4])
    assert_equal(nputils.atrou([1, 2, 3, 4, 5], 2),
                 [1, 0, 2, 0, 3, 0, 4, 0, 5])
    assert_equal(nputils.atrou([1, 2, 3, 4, 5], 3),
                 [1, 0, 0, 2, 0, 0, 3, 0, 0, 4, 0, 0, 5])


def test_downscale():
    assert_equal(nputils.downsample([1, 2, 3, 4, 5, 6], 2),
                 [1, 3, 5])
    assert_equal(nputils.downsample([1, 2, 3, 4, 5, 6, 7], 2),
                 [1, 3, 5, 7])
    assert_equal(nputils.downsample([1, 2, 3, 4], 1),
                 [1, 2, 3, 4])
    assert_raise(ValueError, nputils.downsample, [1, 2, 3, 4], 0)
    assert_raise(ValueError, nputils.downsample, [1, 2, 3, 4], -20)
    assert_equal(nputils.downsample([1, 2, 3, 4, 5, 6, 7], 3),
                 [1, 4, 7])
    v = np.array([0, 1, 2, 3])
    a = np.outer(v, v)
    exp = np.array([[0, 0], [0, 4]])
    assert_equal(nputils.downsample(a, 2), exp)
    exp = np.array([[0, 0, 0, 0], [0, 2, 4, 6]])
    assert_equal(nputils.downsample(a, 2, axis=0), exp)
    exp = np.array([[0, 0], [0, 2], [0, 4], [0, 6]])
    assert_equal(nputils.downsample(a, 2, axis=1), exp)


def test_per_ext():
    v = np.array([0, 1, 2, 3, 5])
    exp = np.array([5, 0, 1, 2, 3, 5])
    assert_equal(nputils.per_extension(v, 1, 0), exp)
    # check that argument has not been changed
    assert_equal(v, np.array([0, 1, 2, 3, 5]))
    exp = np.array([3, 5, 0, 1, 2, 3, 5])
    assert_equal(nputils.per_extension(v, 2, 0), exp)
    exp = np.array([0, 1, 2, 3, 5, 0, 1, 2])
    assert_equal(nputils.per_extension(v, 0, 3), exp)
    v = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
    exp = np.array([[7, 4, 5, 6, 7], [3, 0, 1, 2, 3], [7, 4, 5, 6, 7]])
    assert_equal(nputils.per_extension(v, 1, 0), exp)
    exp = np.array([[3, 0, 1, 2, 3], [7, 4, 5, 6, 7]])
    assert_equal(nputils.per_extension(v, 1, 0, axis=1), exp)
    exp = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 2, 3]])
    assert_equal(nputils.per_extension(v, 0, 1, axis=0), exp)


def test_symm_ext():
    v = np.array([0, 1, 2, 3, 5])
    exp = np.array([0, 0, 1, 2, 3, 5])
    assert_equal(nputils.symm_extension(v, 1, 0), exp)
    # check that argument has not been changed
    assert_equal(v, np.array([0, 1, 2, 3, 5]))
    exp = np.array([1, 0, 0, 1, 2, 3, 5])
    assert_equal(nputils.symm_extension(v, 2, 0), exp)
    exp = np.array([0, 1, 2, 3, 5, 5, 3, 2])
    assert_equal(nputils.symm_extension(v, 0, 3), exp)
    v = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
    exp = np.array([[0, 0, 1, 2, 3], [0, 0, 1, 2, 3], [4, 4, 5, 6, 7]])
    assert_equal(nputils.symm_extension(v, 1, 0), exp)
    exp = np.array([[0, 0, 1, 2, 3], [4, 4, 5, 6, 7]])
    assert_equal(nputils.symm_extension(v, 1, 0, axis=1), exp)
    exp = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [4, 5, 6, 7]])
    assert_equal(nputils.symm_extension(v, 0, 1, axis=0), exp)


def test_zero_ext():
    v = np.array([0, 1, 2, 3, 5])
    exp = np.array([0, 0, 1, 2, 3, 5])
    assert_equal(nputils.fill_extension(v, 1, 0), exp)
    # check that argument has not been changed
    assert_equal(v, np.array([0, 1, 2, 3, 5]))
    exp = np.array([0, 0, 0, 1, 2, 3, 5])
    assert_equal(nputils.fill_extension(v, 2, 0), exp)
    exp = np.array([0, 1, 2, 3, 5, 0, 0, 0])
    assert_equal(nputils.fill_extension(v, 0, 3), exp)
    v = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
    exp = np.array([[0, 0, 0, 0, 0], [0, 0, 1, 2, 3], [0, 4, 5, 6, 7]])
    assert_equal(nputils.fill_extension(v, 1, 0), exp)
    exp = np.array([[0, 0, 1, 2, 3], [0, 4, 5, 6, 7]])
    assert_equal(nputils.fill_extension(v, 1, 0, axis=1), exp)
    exp = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 0, 0, 0]])
    assert_equal(nputils.fill_extension(v, 0, 1, axis=0), exp)
    exp = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [1.5, 1.5, 1.5, 1.5]])
    assert_equal(nputils.fill_extension(v, 0, 1, fillvalue=1.5, axis=0), exp)


def test_resize_like():
    pass


def test_gaussien_noise():
    noise = nputils.gaussian_noise(1000000, 0, 10)
    assert np.abs(noise.std() - 10) < 1
    noise = nputils.gaussian_noise((1024, 1024), 5, 5)
    assert np.abs(noise.std() - 5) < 1
    assert np.abs(noise.std() - 5) < 1


def test_clipreplace():
    l = np.arange(9)
    exp = l.copy()
    exp[-1] = 666
    assert_equal(nputils.clipreplace(l, 0, 7, 666), exp)
    exp[0:2] = 666
    assert_equal(nputils.clipreplace(l, 2, 7, 666), exp)


def test_index():
    l = np.arange(9)
    assert_equal(nputils.get_index(l, np.s_[1:]), l[1:])
    assert_equal(nputils.get_index(l, np.s_[1:-2]), l[1:-2])
    assert_equal(nputils.get_index(l, np.s_[1:-2:-1]), l[1:-2:-1])
    l = np.arange(9).reshape([3, 3])
    assert_equal(nputils.get_index(l, np.s_[1:-2:-1]),
                 l[1:-2:-1, 1:-2:-1])
    assert_equal(nputils.get_index(l, np.s_[1:-2:-1], 0),
                 l[1:-2:-1, :])
    assert_equal(nputils.get_index(l, np.s_[1:-2:-1], 1),
                 l[:, 1:-2:-1])


def test_get_extended_index():
    data = [
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["zero"], 5, 5],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["zero"], -2, -2],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["zero"], 12, 12],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 5, 5],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 0, 0],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], -1, 0],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], -3, 2],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], -4, 3],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 10, 9],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 11, 8],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 12, 7],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 15, 4],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 5, 5],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 0, 0],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], -1, 9],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], -2, 8],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], -3, 7],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], -5, 5],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 9, 9],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 10, 0],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 11, 1],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 12, 2],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 13, 3],
        [10, 4, nputils_c.CONV_BOUNDARY_MAP["wrap"], 15, 5],
        [11, 4, nputils_c.CONV_BOUNDARY_MAP["symm"], 11, 10]]
    for (size, ext_size, ext_type, index, expected) in data:
        res = nputils_c.get_extended_index(index, size, ext_size, ext_type)
        print size, ext_size, ext_type, index, expected, res
        assert res == expected


def test_convolve():

    def do_test(a, v):
        assert_equal(nputils.convolve(a, v, boundary='zero'), np.convolve(a, v))
        assert_equal(nputils.convolve(a, v, boundary='zero', mode="full"), np.convolve(a, v))
        assert_equal(nputils.convolve(a, v, boundary='zero', mode='same'), np.convolve(a, v, mode='same'))
        assert_equal(nputils.convolve(a, v, boundary='zero', mode='valid'), np.convolve(a, v, mode='valid'))

        aext = nputils.symm_extension(a, len(v) - 1, len(v) - 1)
        assert_equal(nputils.convolve(a, v, boundary='symm', mode='full'), np.convolve(aext, v, mode='valid'))

        aext = nputils.per_extension(a, len(v) - 1, len(v) - 1)
        assert_equal(nputils.convolve(a, v, boundary='wrap', mode='full'), np.convolve(aext, v, mode='valid'))

    do_test(np.random.random(20), np.random.random(5))
    do_test(np.random.random(21), np.random.random(5))
    do_test(np.random.random(21), np.random.random(4))
    do_test(np.random.random(10), np.random.random(4))

    a = np.random.random([50, 50])
    v = np.random.random([4, 4])
    assert_equal(nputils.convolve(a, v, boundary='zero'), convolve2d(a, v))

    v = np.array([[1, 2, 2, 1, 2]])
    assert_equal(nputils.convolve(a, v[0], boundary='zero', mode='same'), convolve2d(a, v * v.T, mode='same'))


def test_fill_at():
    a = np.arange(25).reshape([5, 5]) * 10
    b = np.arange(9).reshape([3, 3]) * 0.1

    exp = a.copy()
    exp[:3, :3] = b

    res = a.copy()
    nputils.fill_at(res, [0, 0], b)

    assert_equal(res, exp)

    exp = a.copy()
    exp[1:3 + 1, :3] = b

    res = a.copy()
    nputils.fill_at(res, [1, 0], b)

    assert_equal(res, exp)

    exp = a.copy()
    exp[3:, 2:] = b[:2, :]
    res = a.copy()

    nputils.fill_at(res, [3, 2], b)
    assert_equal(res, exp)

    exp = a.copy()
    exp[:1, :2] = b[2:, 1:]
    res = a.copy()

    nputils.fill_at(res, [-2, -1], b)
    assert_equal(res, exp)


def test_get_next_evenodd():
    assert nputils.get_next_odd(1) == 1
    assert nputils.get_next_odd(1.1) == 1
    assert nputils.get_next_odd(2) == 3
    assert nputils.get_next_odd(3) == 3

    assert nputils.get_next_even(1) == 2
    assert nputils.get_next_even(2) == 2
    assert nputils.get_next_even(3) == 4

    assert_equal(nputils.get_next_odd(_a([1, 2, 3, 4])), _a([1, 3, 3, 5]))
    assert_equal(nputils.get_next_odd(_a([1.2, 2.8, 3.3, 4.3])), _a([1, 3, 3, 5]))
    assert_equal(nputils.get_next_even(_a([1, 2, 3, 4])), _a([2, 2, 4, 4]))


def test_gaussian_support():
    fwhm = np.random.random()
    sigma = nputils.gaussian_fwhm_to_sigma(fwhm)
    assert np.allclose(sigma, fwhm * 1 / (2 * np.sqrt(2 * np.log(2))))
    assert np.abs(nputils.gaussian_sigma_to_fwhm(sigma) - fwhm) < 1e-8
    assert nputils.gaussian_support(sigma=1) == 8
    assert nputils.gaussian_support(sigma=1, nsigma=5) == 10
    assert nputils.gaussian_support(sigma=10) == 80
    assert nputils.gaussian_support(width=1) == 4
    assert nputils.gaussian_support(width=1, nsigma=5) == 5
    assert nputils.gaussian_support(width=10) == 34


def test_norm():
    values = np.random.random([10, 2])
    n1 = nputils.l2norm(values)
    n2 = np.apply_along_axis(np.linalg.norm, 1, values)

    assert_equal(n1, n2)

    values = np.random.random([2, 10])
    n1 = nputils.l2norm(values, axis=0)
    n2 = np.apply_along_axis(np.linalg.norm, 0, values)

    assert_equal(n1, n2)


def test_distance_from_border():
    r = nputils.distance_from_border([5, 10], [20, 20])
    assert r == [5, 14, 10, 9], r
    r = nputils.distance_from_border([5, 25], [20, 20])
    assert r == [5, 14, 25, -6], r


def test_display_measure():
    assert nputils.display_measure(5.23, "Hz") == "5.23 Hz"
    assert nputils.display_measure(5.23, "m") == "5.23 m"
    assert nputils.display_measure(0.00523, "m") == "5.23 mm"
    assert nputils.display_measure(0.0000523, "m") == "52.30 microm"
    assert nputils.display_measure(0.000000523, "m") == "523.00 nanom"
    assert nputils.display_measure(0.00000000523, "m") == "5.23 nanom"
    assert nputils.display_measure(0.0000000000523, "m") == "0.05 nanom"
    assert nputils.display_measure(0.00023, "m") == "230.00 microm"
    assert nputils.display_measure(523, "m") == "523.00 m"
    assert nputils.display_measure(5230, "Hz") == "5.23 kHz"
    assert nputils.display_measure(523000, "Hz") == "523.00 kHz"
    assert nputils.display_measure(52300000, "Hz") == "52.30 MHz"
    assert nputils.display_measure(5230000000, "Hz") == "5.23 GHz"
    assert nputils.display_measure(523000000000, "Hz") == "523.00 GHz"
    assert nputils.display_measure(52300000000000, "Hz") == "52.30 THz"
    assert nputils.display_measure(5230000000000000, "Hz") == "5230.00 THz"


def test_affine_transform():
    tr, itr = nputils.affine_transform(-2, 2, 0, 100)
    assert tr(-2) == 0
    assert tr(2) == 100
    assert tr(0) == 50
    assert tr(-1) == 25
    tr, itr = nputils.affine_transform(-5, 10, 0, 100)
    assert tr(-5) == 0
    assert tr(10) == 100
    assert tr(0) == 100 / 3.
    tr, itr = nputils.affine_transform(5, -10, -100, 100)
    assert tr(5) == -100
    assert tr(-10) - 100 < 1e-10
    assert tr(0) == -100 + 200 / 3.


def test_datetime_epoch():
    d = datetime.datetime(1995, 11, 06, 0, 0)
    e = "1995.84600"
    assert d == nputils.epoch_to_datetime(e), nputils.epoch_to_datetime(e)
    assert e == nputils.datetime_to_epoch(d), nputils.datetime_to_epoch(d)

    d = datetime.datetime(1996, 1, 19, 0, 0)
    e = "1996.04928"
    assert d == nputils.epoch_to_datetime(e)
    assert e == nputils.datetime_to_epoch(d)

    d = datetime.datetime(1998, 1, 03, 0, 0)
    e = "1998.00548"
    assert d == nputils.epoch_to_datetime(e)
    assert e == nputils.datetime_to_epoch(d)

    d = datetime.datetime(2000, 8, 11, 0, 0)
    e = "2000.61054"
    assert d == nputils.epoch_to_datetime(e), nputils.epoch_to_datetime(e)
    assert e == nputils.datetime_to_epoch(d), nputils.datetime_to_epoch(d)


def test_local_sum():
    # a = np.random.random([5, 4])
    a = np.arange(20).reshape(5, 4)
    # mask = np.array([[1, 1, 1], [1, 1, 1]])
    mask = np.ones_like(a)

    ls = nputils.local_sum(a, mask.shape, mode="full")
    ls_conv = nputils.convolve(a, mask, boundary="zero")

    assert np.allclose(ls, ls_conv)

    ls = nputils.local_sum(a, mask.shape, mode="same")
    ls_conv = nputils.convolve(a, mask, boundary="zero", mode='same')

    assert np.allclose(ls, ls_conv)

    ls = nputils.local_sum(a, mask.shape, mode="valid")
    ls_conv = nputils.convolve(a, mask, boundary="zero", mode='valid')

    assert np.allclose(ls, ls_conv)


def test_xcorr_fast():
    a = np.random.random([5, 4])
    b = np.random.random([5, 4])

    assert np.allclose(nputils.xcorr_fast(a, b, method='fft'), nputils.xcorr_fast(a, b, method='conv'))


def test_ssd_fast():
    # a = np.random.random([5, 4])
    # b = np.random.random([5, 4])
    a = np.arange(12).reshape((3, 4))
    b = np.arange(12).reshape((3, 4))
    ssd = nputils.ssd_fast(b, a)

    print ssd

    for i in range(a.shape[0]):
        for j in range(b.shape[1]):
            shifted = nputils.shift2d(b, [a.shape[0] / 2 - i - 1, a.shape[1] / 2 - j - 1])
            diff = ((a - shifted) ** 2).sum()
            print diff
            # nputils.assert_close(diff,  ssd[i, j])


def test_norm_ssd_fast():
    a = np.random.random([5, 4])
    b = np.random.random([5, 4])

    assert np.allclose(nputils.norm_ssd_fast(a, b), 2 - 2 * nputils.norm_xcorr2(a, b))


def test_norm_xcorr():
    a = np.random.random([5, 4])
    b = np.random.random([5, 4])

    corr = nputils.norm_xcorr2(a, a, method='fft', mode='full')
    print nputils.coord_max(corr)

    assert False


def test_crop_threshold():
    l = np.zeros([5, 5])
    l[2, 2] = 2
    l[2, 4] = 4
    l[0, 3] = 4

    res = np.array([[0, 4, 0], [0, 0, 0], [2, 0, 4]])
    np.array_equal(nputils.crop_threshold(l), res)

    res = np.array([[4, 0], [0, 0], [0, 4]])
    np.array_equal(nputils.crop_threshold(l, 3), res)
    cropped, index = nputils.crop_threshold(l, 3, output_index=True)
    nputils.assert_equal(cropped, res)
    assert index == [0, 3, 3, 5]
    nputils.assert_equal(cropped, l[nputils.index2slice(index)])

    array = np.arange(25).reshape([5, 5])
    res = array[0:3, 3:5]
    np.array_equal(nputils.crop_threshold(array, 3, crop_mask=l), res),\
        nputils.crop_threshold(array, 3, crop_mask=l)

    l = np.array([0, 0, 2, 4, 5, 5, 3, 0, 0, 4, 2, 3, 2, 0, 0])
    mask = np.zeros_like(l)
    mask[4:8] = 2

    res = np.array([2, 4, 5, 5, 3, 0, 0, 4, 2, 3, 2])
    np.array_equal(nputils.crop_threshold(l), res)

    res = np.array([4, 5, 5, 3, 0, 0, 4, 2, 3])
    np.array_equal(nputils.crop_threshold(l, 2), res)
    cropped, index = nputils.crop_threshold(l, 2, output_index=True)
    np.array_equal(cropped, res)
    assert index == [3, 12]
    nputils.assert_equal(cropped, l[nputils.index2slice(index)])

    res = l[4:8]
    np.array_equal(nputils.crop_threshold(l, 1, crop_mask=mask), res)


def test_combinations_multiple_r():
    array = [1, 2, 3]

    res = set([(1, 2), (1, 3), (1,), (2,), (3,), (2, 3), (1, 2, 3)])
    assert res == set(nputils.combinations_multiple_r(array, 1, 3))

    res = set([(1, 2), (1, 3), (2, 3), (1, 2, 3)])
    assert res == set(nputils.combinations_multiple_r(array, 2, 3))

    res = set([(1, 2), (1, 3), (1,), (2,), (3,), (2, 3)])
    assert res == set(nputils.combinations_multiple_r(array, 1, 2))

    for combi in nputils.combinations_multiple_r(array, 1, 2):
        assert combi in res


def test_count():
    l = [0, 0, 1, 1, 2, 3, 4, 5, 5, 5, 2, 1, 4, 9]
    res = [(0, 2), (1, 3), (2, 2), (3, 1), (4, 2), (5, 3), (9, 1)]

    assert nputils.count(l) == res, nputils.count(l)

    l = np.array([[0, 0, 1], [1, 2, 3], [4, 5, 5]])
    res = [(0, 2), (1, 2), (2, 1), (3, 1), (4, 1), (5, 2)]

    assert nputils.count(np.array(l).flatten()) == res, nputils.count(np.array(l).flatten())

    l = nputils.gaussian_noise([512, 512], 100000, 100)


def test_uniq_subsets():
    l = [[[1, 2, 3], [4]], [[1, 3, 2], [4]], [[4], [2, 1, 3]], [[1, 2], [3, 4]]]
    res = set([((1, 2, 3), (4,)), ((1, 2), (3, 4))])

    assert nputils.uniq_subsets(l) == res, nputils.uniq_subsets(l)


def test_k_subset():
    # l = [1, 2, 3]

    # res = (((1,), (2,), (3,)),)
    # assert nputils.k_subset(l, 3) == res

    # res = set([((1,), (2, 3)), ((1, 3), (2,)), ((1, 2), (3,))])
    # assert nputils.k_subset(l, 2) == res

    # res = set([((1, 2, 3),)])
    # assert nputils.k_subset(l, 1) == res

    # assert nputils.k_subset(l, 0) == set([])
    # assert nputils.k_subset(l, 4) == set([])

    l = [1, 2, 3, 4, 5]
    nputils.k_subset(l, 3, filter=lambda k: set(k) != set(()))
    # assert False


def test_all_k_subset():
    l = [1, 2, 3]

    res = (((1,), (2,), (3,)),)
    assert tuple(nputils.all_k_subset(l, 3)) == res

    res = (((1,), (2,)), ((1,), (3,)), ((2,), (3,)), ((1,), (2, 3)), ((1, 3), (2,)), ((1, 2), (3,)))
    assert tuple(nputils.all_k_subset(l, 2)) == res

    res = (((1,),), ((2,),), ((3,),), ((1, 2),), ((1, 3),), ((2, 3),), ((1, 2, 3),))
    assert tuple(nputils.all_k_subset(l, 1)) == res

    assert tuple(nputils.k_subset(l, 0)) == ()
    assert tuple(nputils.k_subset(l, 4)) == ()


def test_lists_combinations():
    l1 = [1, 2, 3]
    l2 = [4, 5]

    res1 = ((((1,),), ((4,),)), (((1,),), ((5,),)), (((1,),), ((4, 5),)), (((2,),), ((4,),)),
           (((2,),), ((5,),)), (((2,),), ((4, 5),)), (((3,),), ((4,),)), (((3,),), ((5,),)),
           (((3,),), ((4, 5),)), (((1, 2),), ((4,),)), (((1, 2),), ((5,),)), (((1, 2),), ((4, 5),)),
           (((1, 3),), ((4,),)), (((1, 3),), ((5,),)), (((1, 3),), ((4, 5),)), (((2, 3),), ((4,),)),
           (((2, 3),), ((5,),)), (((2, 3),), ((4, 5),)), (((1, 2, 3),), ((4,),)), (((1, 2, 3),), ((5,),)),
            (((1, 2, 3),), ((4, 5),)))
    assert tuple(nputils.lists_combinations(l1, l2, k=1)) == res1

    res2 = ((((1,), (2,)), ((4,), (5,))), (((1,), (2,)), ((5,), (4,))), (((1,), (3,)), ((4,), (5,))),
           (((1,), (3,)), ((5,), (4,))), (((2,), (3,)), ((4,), (5,))), (((2,), (3,)), ((5,), (4,))),
           (((1,), (2, 3)), ((4,), (5,))), (((1,), (2, 3)), ((5,), (4,))), (((1, 3), (2,)), ((4,), (5,))),
           (((1, 3), (2,)), ((5,), (4,))), (((1, 2), (3,)), ((4,), (5,))), (((1, 2), (3,)), ((5,), (4,))))
    assert tuple(nputils.lists_combinations(l1, l2, k=2)) == res2

    assert set(nputils.lists_combinations(l1, l2)) == set(res1) | set(res2)

    assert tuple(nputils.lists_combinations(l1, l2, k=3)) == ()
    assert tuple(nputils.lists_combinations(l1, l2, k=0)) == ()


def test_shift2d():
    l = np.arange(5)

    assert np.array_equal(nputils.shift2d(l, [1]), np.array([0, 0, 1, 2, 3]))
    assert np.array_equal(nputils.shift2d(l, [2]), np.array([0, 0, 0, 1, 2]))
    assert np.array_equal(nputils.shift2d(l, [0]), l)
    assert np.array_equal(nputils.shift2d(l, [-2]), np.array([2, 3, 4, 0, 0]))

    l = np.array([[1, 2], [3, 4]])

    assert np.array_equal(nputils.shift2d(l, [1, 1]), np.array([[0, 0], [0, 1]]))
    assert np.array_equal(nputils.shift2d(l, [1, 0]), np.array([[0, 0], [1, 2]]))
    assert np.array_equal(nputils.shift2d(l, [0, 1]), np.array([[0, 1], [0, 3]]))
    assert np.array_equal(nputils.shift2d(l, [0, -1]), np.array([[2, 0], [4, 0]]))


def test_slice2index():
    def do_test(s, i):
        assert nputils.slice2index(s) == i
        assert nputils.index2slice(i) == s

    do_test([slice(1, 5), slice(2, 4)], [1, 2, 5, 4])
    do_test([slice(1, 5)], [1, 5])
    do_test([slice(1, 5), slice(2, 4), slice(3, 6)], [1, 2, 3, 5, 4, 6])


def test_zoom():
    a = np.random.random([5, 5])

    assert np.allclose(a[1:4, 1:4], nputils.zoom(a, [2, 2], [3, 3]))
    assert np.allclose(a[1:3, 1:3], nputils.zoom(a, [2, 2], [2, 2]))
    assert np.allclose(a[:4, :4], nputils.zoom(a, [2, 2], [4, 4]))
    assert np.allclose(a[:2, :4], nputils.zoom(a, [0, 2], [4, 4], pad=False))
    assert np.allclose(a[:3, :3], nputils.zoom(a, [1, 1], [4, 4], pad=False))
    assert np.allclose(a[1:, 2:], nputils.zoom(a, [3, 4], [4, 4], pad=False))
    assert np.allclose(a[2:, 2:], nputils.zoom(a, [3, 4], [3, 4], pad=False))

    a = np.random.random([8, 5])

    assert np.allclose(a[1:4, 1:4], nputils.zoom(a, [2, 2], [3, 3]))
    assert np.allclose(a[1:3, 1:3], nputils.zoom(a, [2, 2], [2, 2]))


def test_zoom_correlation():

    def do_test(sa, sb, c, pad=True):
        sx, sy = sa
        cx, cy = c
        a = np.zeros(sa)
        a[sx / 2, sy / 2] = 1

        b = np.zeros(sb)
        b[cx, cy] = 1

        zb = nputils.zoom(b, [cx, cy], a.shape, pad=pad)
        shift = np.array([cx, cy]) - np.array(zb.shape).shape
        print shift

        corr = nputils.xcorr_fast(a, zb)
        assert corr[corr.shape[0] / 2, corr.shape[1] / 2] == 1

    do_test([4, 3], [8, 9], [2, 1])
    do_test([4, 3], [8, 9], [7, 8])
    do_test([6, 5], [11, 5], [7, 0])


def test_find_peaks():
    a = np.zeros([20, 20])
    assert nputils.find_peaks(a, 2, 1) == []

    a[5, 5] = 1
    assert [k.tolist() for k in nputils.find_peaks(a, 2, 1)] == [[5, 5]]

    a[0, 0] = 2
    assert [k.tolist() for k in nputils.find_peaks(a, 2, 1)] == [[5, 5]]
    assert [k.tolist() for k in nputils.find_peaks(a, 2, 1, exclude_border=False)] == [[0, 0], [5, 5]]


def test_align_on_com():
    a1 = _a([1, 1, 2, 1, 1])
    a2 = _a([1, 2, 1, 0, 0])
    exp1 = _a([1, 1, 2, 1, 1, 0])
    exp2 = _a([0, 1, 2, 1, 0, 0])
    ou1, ou2 = nputils.align_on_com(a1, a2)
    assert nputils.assert_equal(exp1, ou1)
    assert nputils.assert_equal(exp2, ou2)

    a1 = _a([1, 1, 2, 1, 1])
    a2 = _a([0, 0, 1, 2, 1, 0, 0])
    exp1 = _a([0, 1, 1, 2, 1, 1, 0])
    exp2 = _a([0, 0, 1, 2, 1, 0, 0])
    ou1, ou2 = nputils.align_on_com(a1, a2)
    assert nputils.assert_equal(exp1, ou1)
    assert nputils.assert_equal(exp2, ou2)

    a1 = _a([0, 1, 1, 2, 1, 1])
    a2 = _a([0, 0, 1, 2, 1, 0, 0])
    ou1, ou2 = nputils.align_on_com(a1, a2)
    assert nputils.assert_equal(exp1, ou1)
    assert nputils.assert_equal(exp2, ou2)

# def test_weighted_norm_corr():
#     a = _a([0, 1, 1, 2, 2, 2, 1, 1, 0])
#     b = _a([0, 1, 1, 2, 0, 0, 0, 0, 0])
#     w = _a([0, 1, 1, 1, 0, 0, 0, 0, 0])

#     print nputils.norm_xcorr2(a, b)
#     print nputils.weighted_norm_xcorr2(a, b, w)

#     assert False


if __name__ == '__main__':
    for attr in __dict__:
        print attr
