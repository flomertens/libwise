import waveletsui
import numpy as np

from libwise import signalutils, uiutils, plotutils, nputils, wtutils, wavelets


class WaveletFilterResponse(uiutils.Experience):

    def __init__(self, wavelet_families=wavelets.get_all_wavelet_families()):
        gui = uiutils.UI(900, 500, "Wavelet Filter Bank Response")

        box = gui.add_box(uiutils.VBox())

        self.figure = plotutils.ReplayableFigure(self.do_plot, None)
        self.view = box.add(plotutils.FigureCanvas(self.figure), True)

        ctl = box.add(uiutils.HBox())
        ctl.add(plotutils.ExtendedNavigationToolbar(self.view, gui), True)

        self.wavelet = waveletsui.WaveletSelector(ctl, self,
                                                  wavelet_families)

        self.dx = uiutils.SpinRangeParameter(ctl, self, "dx", -10, 10, 1, 0)

        self.add_spinner(ctl)

        gui.start()

    def do_plot(self, figure, result):
        if result is None:
            return

        # ax = figure.subplots(n=1)
        ax, ax2 = figure.subplots(n=2)

        w, intensities, widths = result

        ax.set_xscale('log', basex=2)

        ax.set_xlabel("FWHM (log2 scale)")
        ax.set_ylabel("Intensity")

        colors = plotutils.ColorSelector()
        colors.colors[3] = plotutils.lblue
        colors.colors[5] = plotutils.orange

        widthmax = []
        fwhm = []
        scale = []
        nscale = intensities.shape[0]
        for i in range(nscale):
            line, = ax.plot(w, intensities[i], linewidth=1, label="Scale %i" % (i + 1), c=colors.get())
            intensity = intensities[i].copy()
            intensity[:10] = 0
            wmax = w[intensity.argmax()]
            widthabove = w[intensity > intensity.max() / 2]
            if len(widthabove) > 0:
                fwhm.append(widthabove[-1] - widthabove[0])
            else:
                fwhm.append(0)
            widthmax.append(wmax)
            # widthmax.append(2 ** i)
            scale.append(intensities[i].max())

        ticks = [2 ** k for k in range(nscale)]
        print ticks
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(k) for k in ticks])
        # ax.set_xticks(widthmax)
        # ax.set_xticklabels(["%.1f" % k for k in widthmax])

        ax.legend()
        ax.set_xlim(1, 2 ** (nscale + 1))

        x = [2 ** i for i in range(nscale)]
        y = widthmax

        ax2.plot(x, y, marker='+', label="Width max")

        fct = nputils.LinearFct.fit(x, y)
        ax2.plot(x, fct(x), label=fct.get_text_equ())

        ax2.plot(x, fwhm, marker="o", label="FWHM")

        fct = nputils.LinearFct.fit(x, fwhm)
        ax2.plot(x, fct(x), label=fct.get_text_equ())

        ax2.legend()

    def update(self, changed):
        print "Done update"
        wavelet = self.wavelet.get()

        if wavelet.get_name() in ["triangle", "triangle2", 'b1', "b3"]:
            dec = wtutils.uiwt
        else:
            dec = wtutils.uwt

        n = 1000
        nscales = min(wavelet.get_max_level(np.zeros(n)), 6)
        w = np.logspace(0, 8, 100, base=2)

        intensities = np.zeros([nscales, len(w)])
        widths = np.zeros([nscales, len(w)])
        for i, width in enumerate(w):
            s = signalutils.gaussian(n, width=width)
            # s = s / s.sum()
            # s = signalutils.square(n, width)
            # s = signalutils.lorentzian(n, width)
            # s = np.sin((2 * np.pi) * np.arange(n) / (width))
            scales = wtutils.wavedec(s, wavelet, nscales, dec=dec, boundary="zero")
            for j, scale in enumerate(scales[:-1]):
                # intensities[j, i] = (scale ** 2).sum() / s.sum()
                intensities[j, i] = scale.max()
                # intensities[j, i] = np.abs(scale).sum()

        return w, intensities, widths

    def after_update(self, result):
        self.figure.replay(result)
        self.view.draw()


if __name__ == '__main__':
    win = WaveletFilterResponse()
