import numpy as np
from utils import imgutils, nputils


def test_gaussien_cylinder_no_arg():
    try:
        imgutils.gaussian_cylinder(100)
        assert False
    except ValueError:
        pass


def do_gaussien_cylinder(exp, size, nsigma=None, width=None,
                         center_offset=0, angle=None):
    res = imgutils.gaussian_cylinder(size, nsigma=nsigma,
                                     width=width, center_offset=center_offset,
                                     angle=angle)
    print (res * 1000).astype(np.int)
    print exp
    return np.equal(exp, (res * 1000).astype(np.int)).all()


def test_gaussien_cylinder_nsigma():
    nsigma = 2
    exp = np.array([[278, 278, 278, 278, 278],
                    [ 726, 726, 726, 726, 726],
           [1000, 1000, 1000, 1000, 1000],
           [726, 726, 726, 726, 726],
           [278, 278, 278, 278, 278]])

    assert do_gaussien_cylinder(exp, 5, nsigma=nsigma)


def test_gaussien_cylinder_nsigma_fct():
    nsigma = lambda y: 1 + y
    exp = np.array([[726, 278, 56, 5, 0],
             [923, 726, 486, 278, 135],
             [1000, 1000, 1000, 1000, 1000],
             [923, 726, 486, 278, 135],
             [726, 278, 56, 5, 0]])

    assert do_gaussien_cylinder(exp, 5, nsigma=nsigma)
    assert not do_gaussien_cylinder(exp, 5, nsigma=nsigma, width=10)


def test_gaussien_cylinder_width():
    width = 2
    exp = np.array([[  62, 62, 62, 62, 62],
                 [ 500, 500, 500, 500, 500],
                 [1000, 1000, 1000, 1000, 1000],
                 [ 500, 500, 500, 500, 500],
                 [  62, 62, 62, 62, 62]])

    assert do_gaussien_cylinder(exp, 5, width=width)
    # precedence over nsigma
    assert do_gaussien_cylinder(exp, 5, width=width, nsigma=10)

    exp = np.vstack(([1] * 5, exp))
    exp = np.hstack((exp, exp[:,-2:-1]))

    assert do_gaussien_cylinder(exp, 6, width=width)


def test_gaussien_cylinder_width_fct():
    width = lambda y: 1 + y
    exp = np.array([[   0, 62, 291, 500, 641],
         [  62, 500, 734, 840, 895],
         [1000, 1000, 1000, 1000, 1000],
         [  62, 500, 734, 840, 895],
         [   0, 62, 291, 500, 641]])

    assert do_gaussien_cylinder(exp, 5, width=width)


def test_gaussien_cylinder_fct():
    width = 2
    fct = lambda y: 0.5 * y

    exp = np.array([[  62, 210, 500, 840, 1000],
             [ 500, 840, 1000, 840, 500],
             [1000, 840, 500, 210, 62],
             [ 500, 210, 62, 13, 1],
             [  62, 13, 1, 0, 0]])

    assert do_gaussien_cylinder(exp, 5, width=width, center_offset=fct)

    angle = np.pi / 4.

    exp = np.array([[  62, 500, 1000, 500, 62],
             [ 500, 1000, 500, 62, 1],
             [1000, 500, 62, 1, 0],
             [ 500, 62, 1, 0, 0],
             [  62, 1, 0, 0, 0]])

    assert do_gaussien_cylinder(exp, 5, width=width, angle=angle)


def test_gaussien_no_arg():
    try:
        imgutils.gaussian(5)
        assert False
    except ValueError:
        pass


def do_gaussien(exp, size, nsigma=None, width=None):
    res = imgutils.gaussian(size, nsigma=nsigma, width=width)
    return np.equal(exp, (res * 1000).astype(np.int)).all()


def test_gaussien_nsigma():
    nsigma = 2
    exp = np.array([[  18, 82, 135, 82, 18],
             [  82, 367, 606, 367, 82],
             [ 135, 606, 1000, 606, 135],
             [  82, 367, 606, 367, 82],
             [  18, 82, 135, 82, 18]])

    assert do_gaussien(exp, 5, nsigma=nsigma)
    assert not do_gaussien(exp, 5, nsigma=nsigma, width=10)


def test_gaussien_width():
    width = 2
    exp = np.array([[   3, 31, 62, 31, 3],
             [  31, 250, 500, 250, 31],
             [  62, 500, 1000, 500, 62],
             [  31, 250, 500, 250, 31],
             [   3, 31, 62, 31, 3]])

    assert do_gaussien(exp, 5, width=width)
    assert do_gaussien(exp, 5, nsigma=10, width=width)


def test_gaussien_width_even():
    width = 2
    exp = np.array([[   3, 31, 62, 31],
             [  31, 250, 500, 250],
             [  62, 500, 1000, 500],
             [  31, 250, 500, 250]])

    assert do_gaussien(exp, 4, width=width)
    assert do_gaussien(exp, 4, nsigma=10, width=width)


def test_mask():
    m1 = np.ones([5, 5])

    m2 = np.zeros([5, 5])
    m2[2:3, 2:4] = 1

    m3 = np.zeros([5, 5])
    m3[1:3, 0:] = 1

    assert np.allclose(m1, imgutils.Mask(m1).get_mask())
    assert imgutils.Mask(m2).get_area() == m2.sum()

    assert np.allclose(imgutils.Mask(m1).intersection(imgutils.Mask(m2)).get_mask(), m2)

    assert np.allclose(imgutils.Mask(m2).union(imgutils.Mask(m3)).get_mask(), (m2 + m3).astype(bool).astype(int))

    assert np.allclose(imgutils.Mask.from_mask_list([imgutils.Mask(m2), imgutils.Mask(m3)]).get_mask(), (m2 + m3).astype(bool).astype(int))

    region1 = imgutils.Region([5, 5])
    region1.add_rectangle([2, 2], [2, 3])

    assert np.allclose(region1.get_mask(), m2)

    region2 = imgutils.Region([5, 5])
    region2.add_rectangle([1, 0], [2, 4])

    assert np.allclose(region2.get_mask(), m3)

    region2.add_rectangle([2, 2], [2, 3])

    assert np.allclose(region2.get_mask(), (m2 + m3).astype(bool).astype(int))


def test_region_image():
    m2 = np.zeros([5, 5])
    m2[2:3, 2:4] = 1

    img1 = imgutils.gaussian(100, width=6, angle=-0.5, center=[70, 55])
    img1[img1 < 0.1] = 0
    seg1, index = nputils.crop_threshold(img1, output_index=True)

    region1 = imgutils.ImageRegion(img1, index)

    assert np.allclose(region1.get_region(), seg1)
    assert np.allclose(region1.get_data(), img1)

    assert region1.get_shape() == img1.shape
    assert region1.get_shift() == [0, 0]
    assert region1.get_index() == index
    assert list(region1.get_center()) == [70, 55]

    region1.set_shift([-5, -4])

    img2 = imgutils.gaussian(100, width=6, angle=-0.5, center=[65, 51])
    img2[img2 < 0.1] = 0
    seg2, index2 = nputils.crop_threshold(img2, output_index=True)

    assert np.allclose(region1.get_region(), seg2)
    assert np.allclose(region1.get_data(), img2)
    assert list(region1.get_center()) == [65, 51], region1.get_center()

    region1.set_shift([-70, 10])

    img3 = imgutils.gaussian(100, width=6, angle=-0.5, center=[0, 65])
    img3[img3 < 0.1] = 0
    seg3, index = nputils.crop_threshold(img3, output_index=True)

    assert np.allclose(region1.get_region(), seg3)
    assert np.allclose(region1.get_data(), img3)
    assert list(region1.get_center()) == [0 + 6 / 2, 65]

    region1.set_shift([30, 10])

    img3 = imgutils.gaussian(100, width=6, angle=-0.5, center=[100, 65])
    img3[img3 < 0.1] = 0
    seg3, index = nputils.crop_threshold(img3, output_index=True)

    assert np.allclose(region1.get_region(), seg3)
    assert np.allclose(region1.get_data(), img3)
    assert list(region1.get_center()) == [100 - 5 / 2, 65], (region1.get_center(), seg3.shape)

    region1.set_shift([20, 10])

    img3 = imgutils.gaussian(100, width=6, angle=-0.5, center=[90, 65])
    img3[img3 < 0.1] = 0
    seg3, index = nputils.crop_threshold(img3, output_index=True)

    assert np.allclose(region1.get_region(), seg3)
    assert np.allclose(region1.get_data(), img3)
    assert list(region1.get_center()) == [90, 65]

    region2 = imgutils.ImageRegion(img2, index2)

    builder = imgutils.ImageBuilder()
    builder.add(region1)
    builder.add(region2)

    res = builder.get()

    seg4, index = nputils.crop_threshold(img2 + img3, output_index=True)

    assert res.get_shape() == img1.shape
    assert np.allclose(res.get_data(), img3 + img2)
    assert np.allclose(res.get_region(), seg4)
    assert res.get_index() == index


def test_image_region_zoom():

    def do_test(c, sa, ri, sz):
        cx, cy = c
        a = np.zeros(sa)
        a[cx, cy] = 1
        print a

        a = imgutils.ImageRegion(a, ri)
        print a.get_region()

        za = a.zoom(c, sz)
        shift = c - za.get_center()
        zcx, zcy = np.array(za.get_region().shape) / 2 + shift
        print za.get_region()
        print shift, zcx, zcy
        assert za.get_region()[zcx, zcy] == 1

    do_test([2, 3], [8, 9], [1, 0, 7, 8], [2, 2])
    do_test([2, 3], [5, 6], [1, 0, 4, 5], [3, 3])
    do_test([2, 3], [5, 6], [1, 0, 4, 5], [5, 5])
    do_test([2, 3], [5, 6], [1, 0, 4, 5], [5, 6])
    do_test([1, 1], [5, 6], [1, 0, 4, 5], [5, 6])
    do_test([1, 1], [5, 6], [1, 0, 4, 5], [4, 3])
    do_test([3, 4], [5, 6], [1, 0, 4, 5], [5, 6])
    do_test([3, 4], [5, 6], [1, 0, 4, 5], [4, 4])


def test_get_ensemble_index():
    img1 = imgutils.ImageRegion(np.zeros([20, 20]), (2, 5, 3, 6))
    img2 = imgutils.ImageRegion(np.zeros([20, 20]), (3, 10, 1, 5))
    img3 = imgutils.ImageRegion(np.zeros([20, 20]), (2, 9, 4, 2))
    assert imgutils.get_ensemble_index([img1, img2, img3]) == [2, 5, 4, 6]

    img1 = imgutils.ImageRegion(np.zeros([20]), (2, 5))
    img2 = imgutils.ImageRegion(np.zeros([20]), (3, 10))
    img3 = imgutils.ImageRegion(np.zeros([20]), (2, 9))
    assert imgutils.get_ensemble_index([img1, img2, img3]) == [2, 10]


def zip_index():
    assert imgutils.zip_index((2, 3, 5, 7)) == ((2, 5), (3, 7))
    assert imgutils.zip_index((2, 5)) == ((2, 5))


def test_join_image_region():
    img1 = imgutils.ImageRegion(np.ones([6, 6]) * 1, (2, 3, 5, 6))
    img2 = imgutils.ImageRegion(np.ones([6, 6]) * 2, (3, 0, 6, 4))
    img3 = imgutils.ImageRegion(np.ones([6, 6]) * 3, (0, 2, 4, 4))

    builder = imgutils.ImageBuilder()
    builder.add(img1)
    builder.add(img2)
    builder.add(img3)

    print builder.get().get_region()

    assert np.allclose(builder.get().get_region(), imgutils.join_image_region([img1, img2, img3], [6, 6]))
    # assert imgutils.get_ensemble_index([img1, img2, img3]) == [0, 0, 7, 7]

    print imgutils.join_image_region([img1, img2, img3], [12, 12])
    print imgutils.join_image_region([img1, img2, img3], [7, 7])

    assert False


def test_stack_image():
    a = imgutils.Image(np.ones([5, 5]))
    b = imgutils.Image(np.ones([5, 5]) * 2)

    stacked = imgutils.StackedImage(a.data)
    stacked.add(b)
    print stacked.data

    stack_mgr = imgutils.StackedImageManager()
    stack_mgr.add(a)
    stack_mgr.add(b)
    print stack_mgr.get().data

    assert False
