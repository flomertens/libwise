'''
Created on Feb 21, 2012

@author: fmertens
'''

from libwise import uiutils, wavelets, plotutils
import waveletsui


class Wavelet2DBrowser(uiutils.Experience):

    def __init__(self, wavelet_families=wavelets.get_all_wavelet_families()):
        gui = uiutils.UI(900, 500, "Wavelet Browser")

        box = gui.add_box(uiutils.VBox())
        self.view = box.add(plotutils.BaseCustomCanvas(), True)
        ctl = box.add(uiutils.HBox())

        [[self.ax1, self.ax2], [self.ax3, self.ax4]] = self.view.figure.subplots(2, 2)

        self.wavelet = waveletsui.WaveletSelector(ctl, self,
                                                   wavelet_families)
        gui.start()

    def update(self, changed):
        return self.wavelet.get().get_2d_tf_wavelet_fct(8, -4, 4, 10000)

    def after_update(self, result):
        (f, tf_phi, tf_psi1, tf_psi2, tf_psi3) = result

        self.view.figure.suptitle("PSD")

        ranges = [min(f), max(f), min(f), max(f)]

        self.ax1.clear()
        self.ax1.set_title("Scaling function")
        self.ax1.imshow((tf_phi * tf_phi.conj()).real, extent=ranges)

        self.ax2.clear()
        self.ax2.set_title("Wavelet function 1")
        self.ax2.imshow((tf_psi1 * tf_psi1.conj()).real, extent=ranges)

        self.ax3.clear()
        self.ax3.set_title("Wavelet function 2")
        self.ax3.imshow((tf_psi2 * tf_psi2.conj()).real, extent=ranges)

        self.ax4.clear()
        self.ax4.set_title("Wavelet function 3")
        self.ax4.imshow((tf_psi3 * tf_psi3.conj()).real, extent=ranges)

        self.view.draw()

if __name__ == '__main__':
    win = Wavelet2DBrowser()
