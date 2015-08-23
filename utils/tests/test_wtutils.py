'''
Created on Feb 15, 2012

@author: fmertens
'''

import pywt
import numpy as np

from utils import nputils, wtutils, wavelets
from utils.nputils import assert_equal


def get_all_orthos_wavelets():
    orthos = [wavelets.DaubechiesWaveletFamily(),
              wavelets.SymletWaveletFamily(),
              wavelets.CoifletWaveletFamily()]
    for family in orthos:
        for order in family.get_orders():
            yield family.get_wavelet(order).get_name()


def get_all_boundaries():
    return [('zero', 'zpd'), ('symm', 'sym'), ('wrap', 'ppd')]


def test_dwt_idwt_1d():
    for w in get_all_orthos_wavelets():
        for b_wt, b_pywt in get_all_boundaries():
            s = nputils.random_walk(maxn=np.random.randint(500, 2000))

            (a, d) = wtutils.dwt(s, w, b_wt)
            (ae, de) = pywt.dwt(s, w, mode=b_pywt)

            assert_equal(a, ae)
            assert_equal(d, de)

            rs = wtutils.dwt_inv(a, d, w, b_wt)
            rse = pywt.idwt(ae, de, w, mode=b_pywt)

            assert_equal(rs, rse)
            if len(s) % 2 == 0:
                assert_equal(rs, s)
            else:
                assert_equal(rs[:-1], s)


def test_wavdec():
    for w in get_all_orthos_wavelets():
        for b_wt, b_pywt in get_all_boundaries():
            s = nputils.random_walk(maxn=np.random.randint(500, 2000))
            level = np.random.randint(3, 8)

            res = wtutils.wavedec(s, w, level=level, boundary=b_wt)
            rese = pywt.wavedec(s, w, mode=b_pywt, level=level)

            for d, de in zip(res, rese[::-1]):
                assert_equal(d, de)

            rs = wtutils.waverec(res, w, boundary=b_wt)
            rse = pywt.waverec(rese, w, mode=b_pywt)

            assert_equal(rs, rse)
            if len(s) % 2 == 0:
                assert_equal(rs, s)
            else:
                assert_equal(rs[:-1], s, atol=1e-5, rtol=1e-3)


def do_wavedec(dec, inv):
    for w in get_all_orthos_wavelets():
        for b_wt, b_pywt in get_all_boundaries():
            s = nputils.random_walk(maxn=np.random.randint(500, 2000))
            level = np.random.randint(3, 8)

            res = wtutils.wavedec(s, w, level=level, boundary=b_wt, dec=dec)

            rs = wtutils.waverec(res, w, boundary=b_wt, rec=inv)
            assert_equal(rs, s)


def test_wavedec_uwt():
    do_wavedec(wtutils.uwt, wtutils.uwt_inv)

def test_wavedec_iuwt():
    do_wavedec(wtutils.uiwt, wtutils.uiwt_inv)

