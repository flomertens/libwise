'''
Created on Mar 12, 2012

@author: fmertens
'''

import astropy.io.fits as pyfits
from libwise import uiutils, imgutils, plotutils, wtutils, wavelets

import waveletsui


class WaveletTransform2D(uiutils.Experience):

    def __init__(self, img, wavelet_families=wavelets.get_all_wavelet_families()):
        uiutils.Experience.__init__(self)
        self.gui = uiutils.UI(1000, 600, "Wavelet Transform 2D")
        bv = self.gui.add_box(uiutils.VBox())
        self.ctl = bv.add(uiutils.HBox())
        self.view = bv.add(plotutils.BaseCustomCanvas(), True)
        bv.add(plotutils.ExtendedNavigationToolbar(self.view, self.gui))

        self.img = uiutils.OpenImage(self.ctl, self, img=img)
        self.wavelet = waveletsui.WaveletSelector(self.ctl, self,
                                                  wavelet_families, initial=wavelets.get_wavelet("b3"))
        self.scale = uiutils.ScaleRangeParameter(self.ctl, self, "Scale:", 1, 6, 1, 2)
        decs = {"DWT": wtutils.dwt, "UWT": wtutils.uwt, "UIWT": wtutils.uiwt, "UIMWT": wtutils.uimwt}
        exts = {"Symmetry": "symm", "Zero": "zero", "Periodic": "wrap"}

        self.dec = uiutils.ListParameter(self.ctl, self, "Transform:", decs)
        self.ext = uiutils.ListParameter(self.ctl, self, "Boundary:", exts, "symm")

        uiutils.Button(self.ctl, self, "Save result", self.on_save)

        self.add_spinner(self.ctl)

        self.ax1, self.ax2 = self.view.figure.subplots(1, 2)

        self.current_wavedec = None

        self.gui.show()
        self.do_update()

    def on_save(self):
        if self.current_wavedec is None:
            return
        file = uiutils.select_file()
        if file is not None:
            new_hdul = pyfits.HDUList()
            for scale, img in zip(range(self.scale.get_min(), self.scale.get_max() + 1), self.current_wavedec):
                hdu = img.build_hdu()
                hdu.header.set('EXTNAME', "Scale %s" % scale)
                new_hdul.append(hdu)
            new_hdul.writeto(file)

    def before_update(self, changed):
        if not isinstance(self.wavelet.get(), str) and isinstance(self.img.get(), imgutils.Image):
            maxs = min(8, self.wavelet.get().get_max_level(self.img.get().data) + 2)
            self.scale.set_max(maxs)

    def update(self, changed, thread):
        if changed is not self.scale:
            if self.img.get() is None:
                return False
            scale_max = self.scale.get_max()
            data = self.img.get().data
            res = wtutils.wavedec(data, self.wavelet.get(), scale_max,
                                  dec=self.dec.get(), boundary=self.ext.get(), thread=thread)
            if res == None:
                return False
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


def main():
    # img = imgutils.galaxy()[::-1]

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

    # file = "/home/flo/data/lmc/lmc_bothun_R_ast.fits"
    # img = imgutils.FitsImage(file)

    # img = img[480:600, 480:600]

    img = imgutils.galaxy()[::-1]

    # from WaveletDenoise import Denoise
    # denoiser = Denoise('db1', 3, dec=wtutils.uwt, rec=wtutils.uwt_inv)
    # estimated_noise_sigma = nputils.k_sigma_noise_estimation(img)
    # denoised = denoiser.do(img, noise_sigma=estimated_noise_sigma, threashold_factor=3)

    w = WaveletTransform2D(img)
    w.gui.start()

if __name__ == '__main__':
    main()
