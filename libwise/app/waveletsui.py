'''
Created on Feb 21, 2012

@author: fmertens
'''

try:
    __import__('PyQt5')
    use_pyqt5 = True
except ImportError:
    use_pyqt5 = False

if use_pyqt5:
    from PyQt5 import QtGui, QtWidgets
    for obj_str in dir(QtWidgets):
        if not obj_str.startswith('_'):
            setattr(QtGui, obj_str, getattr(QtWidgets, obj_str))
else:
    from PyQt4 import QtGui

from libwise import uiutils


class WaveletSelector(uiutils.WidgetParameter):

    def __init__(self, box, experience, wavelet_families, initial=None):
        uiutils.WidgetParameter.__init__(self, box, experience, "Wavelet family")
        self.wavelet_families = wavelet_families
        self.family = None
        self.orders = []
        self.order = None

        label_wavelet = QtGui.QLabel("Wavelet:")
        self.addWidget(label_wavelet, 0)

        self.combo_wlet_fam = QtGui.QComboBox()
        self.addWidget(self.combo_wlet_fam, 0)

        # label_wavelet = QtGui.QLabel("")
        # self.addWidget(label_wavelet, 0)

        self.combo_wlet_order = QtGui.QComboBox()
        self.addWidget(self.combo_wlet_order, 0)

        self.addStretch()

        self.combo_wlet_order.currentIndexChanged.connect(self.on_wavelet_order_changed)
        self.combo_wlet_fam.currentIndexChanged.connect(self.on_wavelet_family_changed)
        self.combo_wlet_fam.addItems([wavelet.get_name() for wavelet in self.wavelet_families])

        if initial is not None:
            family = initial.get_family()
            self.combo_wlet_fam.setCurrentIndex(self.wavelet_families.index(family))
            self.combo_wlet_order.setCurrentIndex(self.orders.index(initial.name))

        self._initialized()

    def update_combo_wlet_order(self):
        self.combo_wlet_order.clear()
        if self.family is not None:
            self.orders = self.family.get_orders()
            self.combo_wlet_order.addItems(self.orders)
            self.combo_wlet_order.setCurrentIndex(0)

    def on_wavelet_changed(self):
        if self.family and self.order:
            self.set(self.family.get_wavelet(self.order))

    def on_wavelet_family_changed(self, index):
        self.family = None
        text = str(self.combo_wlet_fam.currentText())
        for family in self.wavelet_families:
            if family.get_name() == text:
                self.family = family
        self.update_combo_wlet_order()

    def on_wavelet_order_changed(self, index):
        self.order = str(self.combo_wlet_order.currentText())
        self.on_wavelet_changed()
