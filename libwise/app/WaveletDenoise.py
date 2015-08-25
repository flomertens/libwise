'''
Created on May 23, 2012

@author: fmertens
'''
import itertools
import waveletsui
import numpy as np
import matplotlib.pyplot as plt

from libwise import imgutils, plotutils, nputils, wtutils, wavelets, uiutils


class Denoise:

    def __init__(self, wavelet='db1', level=3, boundary="symm",
                 dec=wtutils.uwt, rec=wtutils.uwt_inv, mode="hard"):
        self.wavelet = wavelet
        self.level = level
        self.boundary = boundary
        self.dec = dec
        self.rec = rec
        self.mode = mode
        self._noise_std = None
        self._noise_res = None

    def decompose(self, img):
        if self.dec == wtutils.uiwt:
            dec = wtutils.wavedec(img, self.wavelet, self.level,
                             self.boundary, self.dec)
            return [[k] for k in dec]
        else:
            return wtutils.wavedec2d(img, self.wavelet, self.level,
                                self.boundary, self.dec)

    def recompose(self, coeffs, img):
        if self.dec == wtutils.uiwt:
            coeffs = [k[0] for k in coeffs]
            return wtutils.waverec(coeffs, self.wavelet, self.boundary,
                              self.rec, img.shape)
        else:
            return wtutils.waverec2d(coeffs, self.wavelet, self.boundary,
                                self.rec, img.shape)

    def get_noise_factor(self, frame, noise_sigma, noise):
        if not self._noise_res:
            if noise is None:
                noise = nputils.gaussian_noise([300, 300], 0, noise_sigma)
            self._noise_res = [k.std() for k in itertools.chain(*self.decompose(noise))]
        return self._noise_res[frame]

    def do(self, img, noise_sigma=None, noise=None, threashold_factor=4):
        print "Denoising..."
        if noise is None and noise_sigma is None:
            noise_sigma = nputils.k_sigma_noise_estimation(img)

        res = self.decompose(img)

        for (i, frame) in enumerate(itertools.chain(*res[:-1])):
            threashold = threashold_factor * self.get_noise_factor(i, noise_sigma, noise)
            mask = (abs(frame) < threashold)
            frame[mask] = 0
            if self.mode == "soft":
                frame[~mask] = frame[~mask] - threashold

        denoised = self.recompose(res, img)
        print "Done"
        return denoised


class WaveletDenoise(uiutils.Experience):

    def __init__(self, img):
        wavelet_families=wavelets.get_all_wavelet_families()
        self.boundary = "symm"

        gui = uiutils.UI(500, 500, "Wavelet Transform 2D")
        bv = gui.add_box(uiutils.VBox())
        self.ctl = bv.add(uiutils.HBox())
        self.view = bv.add(plotutils.BaseCustomCanvas(), True)
        bv.add(plotutils.ExtendedNavigationToolbar(self.view, gui))

        self.img = uiutils.OpenImage(self.ctl, self, img=img)
        self.wavelet = waveletsui.WaveletSelector(self.ctl, self,
                                                  wavelet_families)
        # self.noise_level = uiutils.SpinRangeParameter(self.ctl, self, "Noise:", 0, 100, 5, 20)
        self.noise_level = uiutils.FloatParamater(self.ctl, self, "Noise:", 20, max_lenght=5)
        self.scale = uiutils.SpinRangeParameter(self.ctl, self, "Scale:", 1, 6, 1, 3)
        self.threashold_factor = uiutils.SpinRangeParameter(self.ctl, self, "Threshold:", 0, 6, 1, 4)
        self.mode = uiutils.ListParameter(self.ctl, self, "Mode:", ["hard", "soft"])

        self.ax1, self.ax2, self.ax3 = self.view.figure.subplots(1, 3)

        self.noisy = None
        gui.start()

    def before_update(self, changed):
        if not isinstance(self.wavelet.get(), str) and isinstance(self.img.get(), imgutils.Image):
            maxs = min(8, self.wavelet.get().get_max_level(self.img.get().data) + 2)
            self.scale.set_max(maxs)

    def update(self, changed):
        wavelet = self.wavelet.get()
        if wavelets.TriangeWaveletFamily().is_from(wavelet) or wavelets.BSplineWaveletFamily().is_from(wavelet):
            dec = wtutils.uiwt
            rec = wtutils.uiwt_inv
        else:
            dec = wtutils.uwt
            rec = wtutils.uwt_inv

        denoise = Denoise(wavelet, self.scale.get(), self.boundary, dec, rec, mode=self.mode.get())
        img = self.img.get()

        if changed in [self.img, self.noise_level] or self.noisy is None:
            self.noisy = img.data + nputils.gaussian_noise(img.data.shape, 0, self.noise_level.get())

        estimated_noise_sigma = nputils.k_sigma_noise_estimation(self.noisy)
        print "Estimated noise:", estimated_noise_sigma

        denoised = denoise.do(self.noisy, estimated_noise_sigma, threashold_factor=self.threashold_factor.get())
        # denoised = nputils.smooth(self.noisy, 9, mode="same", boundary="symm")

        return (img, imgutils.Image.from_image(img, self.noisy), imgutils.Image.from_image(img, denoised))

    def after_update(self, result):
        img, noisy, denoised = result

        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.clear()

        plotutils.imshow_image(self.ax1, img, title=False, norm=plotutils.Normalize())
        self.ax1.set_title('Original')
        plotutils.imshow_image(self.ax2, noisy, title=False, norm=plotutils.Normalize())
        self.ax2.set_title('Original + noise')
        plotutils.imshow_image(self.ax3, denoised, title=False, norm=plotutils.Normalize())
        self.ax3.set_title('Denoised')

        self.view.figure.tight_layout()
        self.view.draw()

if __name__ == '__main__':
    plt.gray()
    DenoiseApp(imgutils.Image(imgutils.lena()[::-1]))
