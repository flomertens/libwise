#!/usr/bin/env python

from libwise import uiutils, wavelets, plotutils
import waveletsui
import numpy as np


class WaveletBrowser(uiutils.Experience):

    def __init__(self, wavelet_families=wavelets.get_all_wavelet_families()):
        uiutils.Experience.__init__(self)
        self.gui = uiutils.UI(900, 500, "Wavelet Browser")

        box = self.gui.add_box(uiutils.VBox())
        self.view = box.add(plotutils.BaseCustomCanvas(), True)
        ctl = box.add(uiutils.HBox())

        self.wavelet = waveletsui.WaveletSelector(ctl, self,
                                                  wavelet_families)
        self.level = uiutils.ScaleRangeParameter(ctl, self, "Level:", 1, 10, 1, 8)

        self.ax1, self.ax2 = self.view.figure.subplots(1, 2)

        self.gui.show()
        self.do_update()

    def update(self, changed, thread):
        result = self.wavelet.get().get_wavelet_fct(self.level.get())
        result_tf = self.wavelet.get().get_tf_wavelet_fct(self.level.get(), - 4, 4)

        return (result, result_tf)

    def after_update(self, result):
        t, phi, psi = result[0]
        f, tf_phi, tf_psi = result[1]

        self.ax1.clear()

        self.ax1.set_title("Scaling and wavelet function")
        self.ax1.set_xlabel("time")

        if phi is not None:
            self.ax1.plot(t, phi, label="Scaling")
        self.ax1.plot(t, psi, label="Wavelet")

        self.ax1.legend()

        self.ax2.clear()

        self.ax2.set_title("PSD")
        self.ax2.set_xlabel("frequency")

        m = (tf_psi * tf_psi.conj()).argmax()
        fmax = f[m]

        # self.ax1.plot(t, np.sin(fmax * t * 2 * np.pi))

        tf_f = np.fft.fft(np.sin(fmax * t * 2 * np.pi), 10 * len(t))

        ds = len(t) / (t.max() - t.min())
        f2 = np.fft.fftfreq(10 * len(t), 1 / ds)

        tf_f = tf_f / tf_f.max()

        if tf_phi is not None:
            self.ax2.plot(f, tf_phi * tf_phi.conj())
        self.ax2.plot(f, tf_psi * tf_psi.conj())
        # self.ax2.plot(f2, tf_f * tf_f.conj())
        self.ax2.set_xlim([-4, 4])

        self.view.draw()


def main():
    win = WaveletBrowser()
    win.gui.start()


if __name__ == '__main__':
    main()
