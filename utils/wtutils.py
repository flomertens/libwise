def dwt(signal, wavelet, boundary, level=None, initial_signal=None, axis=None):
    '''
    Perform a one level dwt
    Result is len k + l + 1 if len(s) = 2k  and len(hkd) = 2l
        it is len k + l if len(s) = 2k + 1

    '''
    hkd = get_wavelet_obj(wavelet).get_dec_hk()
    gkd = get_wavelet_obj(wavelet).get_dec_gk()

    a_conv = nputils.convolve(signal, hkd, boundary, axis=axis)
    d_conv = nputils.convolve(signal, gkd, boundary, axis=axis)

    a = nputils.downsample(a_conv, 2, oddeven=1, axis=axis)
    d = nputils.downsample(d_conv, 2, oddeven=1, axis=axis)

    return (a, d)


def idwt(a, d, wavelet, boundary, level=None, axis=None):
    '''
    Perform a one level idwt
    Result len is always 2 * len(a) - len(hkr) + 1

    Warning: if len(s) = 2k + 1, then idwt(dwt(s)) will give one element
             too much which will be zero. There is no way to know the
             parity of the original signal. It can be safely removed.
             For this reason, if len(a) is bigger than len(d) to 1, we strip
             this last element
    '''
    if len(a) == len(d) + 1:
        a = a[:-1]

    hkr = get_wavelet_obj(wavelet).get_rec_hk()
    gkr = get_wavelet_obj(wavelet).get_rec_gk()

    a_upsample = nputils.upsample(a, 2, oddeven=1, lastzero=True, axis=axis)
    d_upsample = nputils.upsample(d, 2, oddeven=1, lastzero=True, axis=axis)

    c1 = nputils.convolve(a_upsample, hkr, boundary, axis=axis, mode='valid')
    c2 = nputils.convolve(d_upsample, gkr, boundary, axis=axis, mode='valid')

    return c1 + c2


def stationary_dwt(signal, wavelet, boundary, level, initial_signal=None, axis=None):
    hkd = nputils.atrou(get_wavelet_obj(wavelet).get_dec_hk(), pow(2, level))
    gkd = nputils.atrou(get_wavelet_obj(wavelet).get_dec_gk(), pow(2, level))

    a = nputils.convolve(signal, hkd, boundary, axis=axis)
    d = nputils.convolve(signal, gkd, boundary, axis=axis)

    return (a, d)


def stationary_idwt(a, d, wavelet, boundary, level, initial_signal=None, axis=None):
    hkr = nputils.atrou(get_wavelet_obj(wavelet).get_rec_hk(), pow(2, level))
    gkr = nputils.atrou(get_wavelet_obj(wavelet).get_rec_gk(), pow(2, level))

    c1 = nputils.convolve(a, hkr, boundary, axis=axis, mode="valid")
    c2 = nputils.convolve(d, gkr, boundary, axis=axis, mode="valid")

    return 1 / 2. * (c1 + c2)


def starck_dwt(signal, wavelet, boundary, level, initial_signal=None, axis=None):
    hkd = nputils.atrou(get_wavelet_obj(wavelet).get_dec_hk(), pow(2, level))

    a = nputils.convolve(signal, hkd, boundary, axis=axis)

    a = nputils.resize_like(a, signal, 'center')
    d = signal - a

    return (a, d)


# def starck_log_dwt(signal, wavelet, boundary, level, initial_signal=None, axis=None):
#     hkd = nputils.atrou(get_wavelet_obj(wavelet).get_dec_hk(), pow(2, level))

#     a = nputils.convolve(signal, hkd, boundary, axis=axis)

#     a = nputils.resize_like(a, signal, 'center')
#     d = signal - a

#     d = np.sign(d) * np.log(np.abs(d))

#     return (a, d)


# def dog_pyramid(signal, wavelet, boundary, level, initial_signal, axis=None):
#     win_fct = lambda m: spsignal.gaussian(2 * m + 1, 1 + pow(2, level) / 2.3)
#     if level == 0:
#         a1 = initial_signal
#     else:
#         a1 = nputils.smooth(initial_signal, 1 + pow(2, level), mode='same', window_fct=win_fct)
#     a2 = nputils.smooth(initial_signal, 1 + pow(2, level) + 2, mode='same', window_fct=win_fct)

#     return a2, a1 - a2


# def log_pyramid(signal, wavelet, boundary, level, initial_signal, axis=None):
#     win_fct = lambda m: spsignal.gaussian(2 * m + 1, 1 + pow(2, level) / 2.3)
#     a = nputils.smooth(initial_signal, 1 + pow(2, level), mode='same', window_fct=win_fct)

#     d = laplace(a)

#     return a, - d


# def median_dwt(signal, wavelet, boundary, level, initial_signal, axis=None):
#     a = median_filter(initial_signal, size=1 + pow(2, level + 1))
#     d = signal - a
#     # signal = signal - minimum_filter(signal, size=1 + pow(2, level + 1))

#     # hkd = nputils.upsample(get_wavelet_obj(wavelet).get_dec_hk(), pow(2, level), False)

#     # a = nputils.convolve(signal, hkd, boundary, axis=axis)

#     # a = nputils.resize_like(a, signal, 'center')
#     # d = (signal - a).clip(0)

#     return (a, d)


# def gaussian_pyramid(signal, wavelet, boundary, level, initial_signal, axis=None):
#     a = initial_signal

#     d = nputils.smooth(initial_signal, 1 + pow(2, level + 1))

#     return a, d


# def laplacien_pyramid(signal, wavelet, boundary, level, initial_signal, axis=None):
#     # w = [[0.5, 1, 0.5], [1, -6, 1], [0.5, 1, 0.5]]
#     w = [-1, 2, -1]
#     w = nputils.upsample(w, pow(2, level))

#     a = nputils.convolve(signal, w)
#     a = nputils.resize_like(a, signal, 'center')
#     d = signal - a

#     return a, d


def starck_idwt(a, d, wavelet, boundary, level, axis=None):
    return a + d


def wavedec_iter(signal, wavelet, level, boundary="symm",
                 dec=dwt, axis=None):
    # max_level = get_wavelet_obj(wavelet).get_max_level(signal)
    # if level > max_level:
        # raise ValueError("Level should be < %s" % max_level)
    a = signal
    for j in range(int(level)):
        a, d = dec(a, wavelet, boundary, j, initial_signal=signal, axis=axis)
        yield d
    yield a


def wavedec(signal, wavelet, level, boundary="symm",
            dec=dwt, axis=None):
    return list(wavedec_iter(signal, wavelet, level, boundary, dec, axis))


def dogdec(signal, widths=None, angle=0, ellipticity=1, boundary="symm"):
    if widths is None:
        widths = np.arange(1, min(signal.shape) / 4)
    beams =  [imgutils.GaussianBeam(ellipticity * w, w, bpa=angle) for w in widths]
    filtered = [b.convolve(signal, boundary=boundary) for b in beams]
    res = [(el[0] - el[-1]) for el in nputils.nwise(filtered, 2)]
    for s in res:
        s[s <= 0] = 0
    res = [s - b2.convolve(s, boundary=boundary) for (s, (b1, b2)) in zip(res, nputils.nwise(beams, 2))]
    # res = [b1.convolve(s, boundary=boundary) - b2.convolve(s, boundary=boundary) for (s, (b1, b2)) in zip(res, nputils.nwise(beams, 2))]
    return res


def pyramiddec(signal, widths=None, angle=0, ellipticity=1, boundary="symm"):
    if widths is None:
        widths = np.arange(1, min(signal.shape) / 4)
    beams =  [imgutils.GaussianBeam(ellipticity * w, w, angle=angle) for w in widths]
    min_scale = beams[0].convolve(signal, boundary=boundary) - beams[1].convolve(signal, boundary=boundary)
    filtered_min = [b.convolve(min_scale, boundary=boundary) for b in beams]
    filtered_all = [b.convolve(signal, boundary=boundary) for b in beams]
    dog = [(el[0] - el[-1]) for el in nputils.nwise(filtered_all, 2)]
    return [v - k for k, v in  zip(filtered_min, dog)]


def waverec(coefs, wavelet, boundary="symm", rec=idwt,
            axis=None, shape=None):
    a = coefs[-1]
    for j in range(len(coefs) - 2, -1, -1):
        a = rec(a, coefs[j], wavelet, boundary, j, axis=axis)
    if shape and shape != a.shape:
        # See idwt() for an explaination
        a = nputils.index(a, np.s_[:-1], axis)
    return a
