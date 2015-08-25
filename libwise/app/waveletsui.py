'''
Created on Feb 21, 2012

@author: fmertens
'''

import gtk
from utils import uiutils


class WaveletSelector(uiutils.WidgetParameter):

    def __init__(self, box, experience, wavelet_families):
        uiutils.WidgetParameter.__init__(self, box, experience, "Wavelet family")
        self.wavelet_families = wavelet_families
        self.family = None
        self.order = None

        label_wavelet = gtk.Label("Wavelet family:")
        self.pack_start(label_wavelet, False, True)

        self.combo_wlet_fam = gtk.combo_box_new_text()
        for wavelet in self.wavelet_families:
            self.combo_wlet_fam.append_text(wavelet.get_name())

        self.combo_wlet_fam.connect("changed", self.on_wavelet_family_changed)
        self.pack_start(self.combo_wlet_fam, False, False)

        label_wavelet = gtk.Label("Order:")
        self.pack_start(label_wavelet, False, True)

        self.combo_wlet_order = gtk.combo_box_new_text()
        self.combo_wlet_order.connect("changed", self.on_wavelet_order_changed)
        self.pack_start(self.combo_wlet_order, False, False)

        self._initialized()

    def update_combo_wlet_order(self):
        self.combo_wlet_order.get_model().clear()
        for order in self.family.get_orders():
            self.combo_wlet_order.append_text(order)
        self.combo_wlet_order.set_active(0)

    def on_wavelet_changed(self):
        if self.family and self.order:
            self.set(self.family.get_wavelet(self.order))

    def on_wavelet_family_changed(self, combobox):
        self.family = None
        text = self.combo_wlet_fam.get_active_text()
        for family in self.wavelet_families:
            if family.get_name() == text:
                self.family = family
        self.update_combo_wlet_order()

    def on_wavelet_order_changed(self, combobox):
        self.order = self.combo_wlet_order.get_active_text()
        self.on_wavelet_changed()
