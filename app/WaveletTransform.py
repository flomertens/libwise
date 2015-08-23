'''
Created on Mar 14, 2012

@author: fmertens
'''
import numpy as np
import waveletsui

from utils import uiutils, plotutils, signalutils, nputils, wavelets, wtutils


class Wavelet(uiutils.Experience):

    def __init__(self, wavelet_families, t, x):
        gui = uiutils.UI(500, 500, "Wavelet Transform")
        bv = gui.add_box(uiutils.VBox())
        self.ctl = bv.add(uiutils.HBox())
        self.view = bv.add(plotutils.BaseCustomCanvas(), True)
        bv.add(plotutils.ExtendedNavigationToolbar(self.view, gui))

        self.wavelet = waveletsui.WaveletSelector(self.ctl, self,
                                                  wavelet_families)
        self.scale = uiutils.ScaleRangeParameter(self.ctl, self, "Scale:", 1, 8, 1, 5)
        decs = {"DWT": wtutils.dwt, "UWT": wtutils.uwt, "UIWT": wtutils.uiwt}
        exts = {"Symmetry": "symm", "Zero": "zero", "Periodic": "wrap"}

        self.dec = uiutils.ListParameter(self.ctl, self, "Transform:", decs)
        self.ext = uiutils.ListParameter(self.ctl, self, "Boundary:", exts)

        self.x = x
        self.t = t

        gui.start()

    def before_update(self, changed):
        self.scale.set_max(self.wavelet.get().get_max_level(self.x))

    def update(self, changed):
        return wtutils.wavedec(self.x, self.wavelet.get(), self.scale.get(),
                               dec=self.dec.get(), boundary=self.ext.get())
        # res = pywt.swt(self.x, self.wavelet.get().get_name(), level=self.scale.get())
        # return [d for (d, a) in res][::-1]
        res = pywt.wavedec(self.x, self.wavelet.get().get_name(), level=self.scale.get())
        return res[1:][::-1]

    def after_update(self, result):
        titles = ["Original"] + \
                 ["Scale %i" % k for k in range(1, int(self.scale.get()) + 1)] + ["Residu"]

        plots = [self.x] + list(result)

        self.view.figure.clear()
        # axs = self.view.figure.subplots(nrows=len(plots))

        # for plot, title, ax in zip(plots, titles, axs):
        #     ax.plot(plot)
        #     ax.set_title(title)

        ax = self.view.figure.subplots()

        for plot, title in zip(plots, titles):
            plot = nputils.resize_like(plot, self.x)
            ax.plot(plot, label=title)

        ax.legend()
        self.view.draw()

if __name__ == '__main__':
    # t = np.arange(0, 10, 0.01)
    # x = np.sin(2 * t) + np.cos(20 * t) + np.sqrt(t)
    # x = signalutils.linear_chirp(t, 1, 20, 0, 0) - \
    #    signalutils.linear_chirp(t, 1, 7, 0, 0)

    x = np.zeros(500)
    center = 20
    for width in [2, 4, 8, 16, 32, 64]:
        x += signalutils.gaussian(500, width=width, center=center)
        center += 8 * width

    # g1 = signalutils.gaussian(500, width=20, center_offset=-150)
    # # x += g1
    # g2 = signalutils.gaussian(500, width=5, center_offset=150)
    # x = g1 + g2

    # x = np.cos(np.arange(100) / 2)

    w = Wavelet(wavelets.get_all_wavelet_families(), np.arange(500), x)
