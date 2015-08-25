'''
Created on Mar 12, 2012

@author: fmertens
'''

import pyfits
import numpy as np
import matplotlib.pyplot as plt

from libwise import nputils, uiutils, imgutils, plotutils, wtutils, wavelets

import waveletsui


class WaveletTransform2D(uiutils.Experience):

    def __init__(self, img, wavelet_families=wavelets.get_all_wavelet_families()):
        gui = uiutils.UI(500, 500, "Wavelet Transform 2D")
        bv = gui.add_box(uiutils.VBox())
        self.ctl = bv.add(uiutils.HBox())
        self.view = bv.add(plotutils.BaseCustomCanvas(), True)
        bv.add(plotutils.ExtendedNavigationToolbar(self.view, gui))

        self.img = uiutils.OpenImage(self.ctl, self, img=img)
        self.wavelet = waveletsui.WaveletSelector(self.ctl, self,
                                                  wavelet_families)
        self.scale = uiutils.ScaleRangeParameter(self.ctl, self, "Scale:", 1, 6, 1, 2)
        decs = {"DWT": wtutils.dwt, "UWT": wtutils.uwt, "UIWT": wtutils.uiwt, "UIMWT": wtutils.uimwt}
        exts = {"Symmetry": "symm", "Zero": "zero", "Periodic": "wrap"}

        self.dec = uiutils.ListParameter(self.ctl, self, "Transform:", decs)
        self.ext = uiutils.ListParameter(self.ctl, self, "Boundary:", exts)

        self.ax1, self.ax2 = self.view.figure.subplots(1, 2)

        self.current_wavedec = None

        gui.start()

    def before_update(self, changed):
        if not isinstance(self.wavelet.get(), str) and isinstance(self.img.get(), imgutils.Image):
            maxs = min(8, self.wavelet.get().get_max_level(self.img.get().data) + 2)
            self.scale.set_max(maxs)

    def update(self, changed):
        if changed is not self.scale:
            scale_max = self.scale.get_max()
            data = self.img.get().data
            res = wtutils.wavedec(data, self.wavelet.get(), scale_max,
                                  dec=self.dec.get(), boundary=self.ext.get())
            self.current_wavedec = [imgutils.Image.from_image(self.img.get(), k) for k in res]

        return self.current_wavedec

    def after_update(self, result):
        self.ax1.clear()
        self.ax2.clear()
        scale = int(self.scale.get())
        plotutils.imshow_image(self.ax1, self.img.get(), title=False, norm=plotutils.Normalize())
        self.ax1.set_title('Original')
        plotutils.imshow_image(self.ax2, result[scale - 1], title=False, norm=plotutils.Normalize())
        self.ax2.set_title('Scale %s' % scale)

        self.view.draw()


if __name__ == '__main__':
    img = imgutils.galaxy()[::-1]

    # def get_img(e1_coord, e2_coord):
    #     img = imgutils.cylinder_fct(500, 100., lambda y: 20 * np.sin(y/100.))

    #     e1 = imgutils.ellipsoide(50, 10, 20) * 0.1
    #     e2 = imgutils.ellipsoide(10, 2, 4) * 0.1

    #     nputils.fill_at(img, e1_coord, e1)
    #     nputils.fill_at(img, e2_coord, e2)
    #     return img

    # img = np.zeros([512, 512])

    # e1 = imgutils.ellipsoide(50, 20, 20)
    # e2 = imgutils.ellipsoide(50, 10, 10)
    # e3 = imgutils.ellipsoide(50, 5, 5)
    # e4 = imgutils.ellipsoide(100, 50, 50)

    # nputils.fill_at(img, [100, 100], e1)
    # nputils.fill_at(img, [150, 150], e1)
    # nputils.fill_at(img, [180, 180], e2)
    # nputils.fill_at(img, [200, 250], e3)
    # nputils.fill_at(img, [350, 350], e4)s

    # img = get_img([250, 250], [250, 250])

    # FILE = "/homes/fmertens/data/crab/H1-WI.FITS"
    # img = pyfits.open(FILE)[0].data

    # img = img[480:600, 480:600]

    # img = imgutils.lena()[::-1]

    # from WaveletDenoise import Denoise
    # denoiser = Denoise('db1', 3, dec=wtutils.uwt, rec=wtutils.uwt_inv)
    # estimated_noise_sigma = nputils.k_sigma_noise_estimation(img)
    # denoised = denoiser.do(img, noise_sigma=estimated_noise_sigma, threashold_factor=3)

    w = WaveletTransform2D(imgutils.Image(denoised))
