'''
Created on Mar 9, 2012

@author: fmertens
'''
import os
import sys
import collections

import numpy as np


try:
    __import__('PyQt5')
    use_pyqt5 = True
except ImportError:
    use_pyqt5 = False

if use_pyqt5:
    from PyQt5 import QtGui, QtCore, QtWidgets
    for obj_str in dir(QtWidgets):
        if not obj_str.startswith('_'):
            setattr(QtGui, obj_str, getattr(QtWidgets, obj_str))
else:
    from PyQt4 import QtGui, QtCore

import waitingspinnerwidget

import imgutils

_QT_APP = None


def select_file(parent=None, current_folder=""):
    global _QT_APP
    if QtGui.QApplication.startingUp():
        _QT_APP = QtGui.QApplication(sys.argv)

    res = QtGui.QFileDialog.getSaveFileName(parent=parent, directory=current_folder)

    if use_pyqt5:
        res = res[0]

    if res == "":
        return None
    return str(res)


def open_file(parent=None, current_folder=""):
    global _QT_APP
    if QtGui.QApplication.startingUp():
        _QT_APP = QtGui.QApplication(sys.argv)

    res = QtGui.QFileDialog.getOpenFileName(parent=parent, directory=current_folder)

    if use_pyqt5:
        res = res[0]

    if res == "":
        return None
    return str(res)


def select_folder():
    res = QtGui.QFileDialog.getExistingDirectory()
    if res == "":
        return None
    return str(res)
    

def erro_msg(msg, parent=None):
    dial = QtGui.QMessageBox.warning(parent, "", msg, QtGui.QMessageBox.Close)


class Box(QtGui.QBoxLayout):

    def add(self, element, expand=False):
        if isinstance(element, QtGui.QBoxLayout):
            self.addLayout(element)
        else:
            self.addWidget(element)
        return element


class VBox(QtGui.QVBoxLayout, Box):

    def __init__(self, homogeneous=False, spacing=10):
        QtGui.QVBoxLayout.__init__(self)
        self.setSpacing(spacing)


class HBox(QtGui.QHBoxLayout, Box):

    def __init__(self, homogeneous=False, spacing=10):
        QtGui.QHBoxLayout.__init__(self)
        self.setSpacing(spacing)


class Parameter:

    def __init__(self, experience, initial_value):
        self.key = initial_value
        self.experience = experience
        self.initialised = False

    def _initialized(self):
        self.initialised = True

    def get(self):
        return self.key

    def set(self, value, update=True):
        self.key = value
        if self.initialised and self.experience and update:
            self.experience.do_update(self)


class WidgetParameter(Parameter, HBox):

    def __init__(self, box, experience, initial_value=None):
        Parameter.__init__(self, experience, initial_value)
        HBox.__init__(self, False, 10)
        box.add(self)


class NamedWidgetParameter(WidgetParameter):

    def __init__(self, box, experience, name, initial_value=None):
        WidgetParameter.__init__(self, box, experience, initial_value)
        if name is not None:
            label = QtGui.QLabel(name)
            self.add(label)


class TextParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, value, max_lenght=-1):
        NamedWidgetParameter.__init__(self, box, experience, name, value)

        self.entry = QtGui.QLineEdit(str(value))
        if max_lenght > 0:
            metric = QtGui.QFontMetrics(self.entry.font())
            self.entry.setFixedWidth(metric.width("8" * max_lenght))
        # self.entry.set_width_chars(max_lenght)
        self.entry.returnPressed.connect(lambda : self.set(self.get()))
        self.add(self.entry)

        # self.entry.connect('activate', self.on_activated)

        self._initialized()

    # def textChanged(self, text):
    #     self.set(text)

    def get(self):
        return self.entry.text()

    def set(self, value, update=True):
        self.entry.setText(str(value))
        NamedWidgetParameter.set(self, value, update=update)


class FloatParamater(TextParameter):

    def get(self):
        return float(self.entry.text())


class ListParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, values,
                 initial_value=None):
        NamedWidgetParameter.__init__(self, box, experience, name,
                                      initial_value)

        self.combo = QtGui.QComboBox()
        self.add(self.combo)

        self.combo.activated.connect(self.on_changed)
        self.set_values(values, initial_value)
        self._initialized()

    def on_changed(self, index):
        self.set(self.dict.values()[index])

    def set_values(self, values, initial_value=None):
        self.combo.clear()
        if isinstance(values, dict):
            self.dict = values
            self.values = self.dict.values()
        else:
            self.dict = collections.OrderedDict(zip([str(k) for k in values], values))
            self.values = values

        self.combo.addItems(self.dict.keys())

        if not initial_value and len(self.values) > 0:
            initial_value = self.values[0]

        if initial_value and initial_value in self.values:
            index = self.values.index(initial_value)
            self.combo.setCurrentIndex(index)
            self.set(self.dict.values()[index])


class RangeParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 range_widget, initial_value=None, range_box=None):
        if initial_value is None:
            initial_value = lower
        NamedWidgetParameter.__init__(self, box, experience, name,
                                      initial_value)

        # self.adj = gtk.Adjustment(initial_value, lower, upper, step, 1, 0)
        self.range_widget = range_widget
        self.range_widget.setRange(lower, upper)
        self.range_widget.setSingleStep(step)
        # self.range_widget.set_update_policy(gtk.UPDATE_DELAYED)
        self.add(self.range_widget)

        if initial_value is not None:
            self.set(initial_value, update=False)

        self._initialized()

    def value_changed(self, value):
        self.set(value)

    def set_max(self, maxi):
        self.range_widget.setMaximum(maxi)
        if self.range_widget.value() > maxi:
            self.range_widget.setValue(maxi)
            self.set(maxi, update=False)

    def get_max(self):
        return self.range_widget.maximum()

    def get_min(self):
        return self.range_widget.minimum()
        
    def set_min(self, mini):
        self.range_widget.setMinimum(mini)
        if self.range_widget.value() < mini:
            self.range_widget.setValue(mini)
            self.set(mini, update=False)

    def set(self, value, update=True):
        if value >= self.range_widget.minimum() and value <= self.range_widget.maximum():
            super(RangeParameter, self).set(value, update)
            self.range_widget.setValue(value)


class SpinRangeParameter(RangeParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 initial_value=None):
        spin = QtGui.QSpinBox()
        spin.valueChanged.connect(self.value_changed)

        RangeParameter.__init__(self, box, experience, name, lower,
                                upper, step, spin, initial_value)


class ScaleRangeParameter(RangeParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 initial_value=None, digits=0):
        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setTickPosition(QtGui.QSlider.TicksBelow)
        slider.setMinimumSize(150, 30)

        RangeParameter.__init__(self, box, experience, name, lower,
                                upper, step, slider, initial_value)

        self.label = QtGui.QLabel(str(self.get()))
        self.insertWidget(1, self.label)
        slider.valueChanged.connect(self.value_changed)

    def value_changed(self, value):
        self.label.setText(str(value))
        RangeParameter.value_changed(self, value)


class Button(WidgetParameter):

    def __init__(self, box, experience, name, on_clicked=None):
        WidgetParameter.__init__(self, box, experience, None)
        self.bn = QtGui.QPushButton(name)
        if on_clicked is None:
            on_clicked = self.on_clicked
        self.bn.clicked.connect(on_clicked)
        self.add(self.bn)

        self._initialized()


class UpdateButton(Button):

    def __init__(self, box, experience):
        Button.__init__(self, box, experience, "", on_clicked=self.on_clicked)
        self.bn.setIcon(QtGui.QIcon.fromTheme("view-refresh"))

    def on_clicked(self, bn):
        self.set(1)


class OpenImage(Button):
    
    def __init__(self, box, experience, img=None):
        Button.__init__(self, box, experience, "Open image...", on_clicked=self.on_clicked)
        if img is not None:
            if not isinstance(img, imgutils.Image):
                img = imgutils.Image(img)
            self.set(img, update=False)
        self.current_path = None

    def set(self, value, update=True):
        Button.set(self, value, update=update)
        if not hasattr(value, "file"):
            label = "DATA"
        else:
            label = os.path.basename(value.file)
        self.bn.setText(label)

    def on_clicked(self, bn):
        current_folder = ''
        if self.current_path is not None:
            current_folder = os.path.dirname(self.current_path)

        self.current_path = open_file(current_folder=current_folder)

        if self.current_path is not None:
            img = imgutils.guess_and_open(self.current_path)
            self.set(img)


class EntryDescription(QtGui.QLineEdit):

    def __init__(self, description, text=None, n_chars=None):
        super(EntryDescription, self).__init__()
        if n_chars is not None:
            metric = QtGui.QFontMetrics(self.font())
            self.setFixedWidth(metric.width("8" * n_chars))
        self.description = description
        self.description_mode = False
        self.clear_on_escape = False

        self.setToolTip(description)

        if text is None or text == "":
            self.set_description_mode(True)
        else:
            self.setText(text)

    def keyPressEvent(self, event):
        QtGui.QLineEdit.keyPressEvent(self, event)
        if self.clear_on_escape:
            if event.key() == QtCore.Qt.Key_Escape:
                self.clear()

    def set_clear_on_escape(self, value):
        self.clear_on_escape = value

    def set_description_mode(self, value):
        # if value == self.description_mode:
        #     return
        self.description_mode = value
        if self.description_mode is True:
            self.setStyleSheet("color: #808080")
            # self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('gray'))
            super(EntryDescription, self).setText(self.description)
        else:
            self.setStyleSheet("color: #000000")
            # self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
            super(EntryDescription, self).setText("")

    def focusInEvent(self, event):
        if self.description_mode:
            self.set_description_mode(False)
        QtGui.QLineEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        if len(self.text()) == 0:
            self.set_description_mode(True)
        QtGui.QLineEdit.focusOutEvent(self, event)

    def get_text(self):
        if self.description_mode is True:
            return ""
        return super(EntryDescription, self).text()

    def set_text(self, text):
        if text == "" or text is None:
            self.set_description_mode(True)
        else:
            self.set_description_mode(False)
            super(EntryDescription, self).setText(text)

    def clear(self):
        self.set_text("")
        self.set_description_mode(False)
        self.editingFinished.emit()


class CustomNode(object):

    def __init__(self, in_data):
        self._data = in_data  
  
        self._columncount = len(self._data)
        self._children = []  
        self._parent = None  
        self._row = 0  
  
    def data(self, in_column):  
        if in_column >= 0 and in_column < len(self._data):  
            return self._data[in_column]

    def setData(self, in_column, data):
        self._data[in_column] = data
  
    def columnCount(self):  
        return self._columncount  
  
    def childCount(self):  
        return len(self._children)  
  
    def child(self, in_row):  
        if in_row >= 0 and in_row < self.childCount():  
            return self._children[in_row]  

    def parent(self):  
        return self._parent  
  
    def row(self):  
        return self._row  
  
    def addChild(self, in_child):  
        in_child._parent = self  
        in_child._row = len(self._children)  
        self._children.append(in_child)  
        self._columncount = max(in_child.columnCount(), self._columncount)  
  
  
class CustomModel(QtCore.QAbstractItemModel):  
    def __init__(self, in_nodes, header):
        QtCore.QAbstractItemModel.__init__(self)  
        self._root = CustomNode(header)  
        for node in in_nodes:  
            self._root.addChild(node)
        self.header = header

    def getNode(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._root.data(section)

        return None
  
    def rowCount(self, in_index):  
        if in_index.isValid():  
            return in_index.internalPointer().childCount()  
        return self._root.childCount()  
  
    def addChild(self, in_node, in_parent):  
        if not in_parent or not in_parent.isValid():  
            parent = self._root  
        else:  
            parent = in_parent.internalPointer()  
        parent.addChild(in_node)  
  
    def index(self, in_row, in_column, in_parent=None):  
        if not in_parent or not in_parent.isValid():  
            parent = self._root  
        else:  
            parent = in_parent.internalPointer()  
      
        if not QtCore.QAbstractItemModel.hasIndex(self, in_row, in_column, in_parent):  
            return QtCore.QModelIndex()  
      
        child = parent.child(in_row)  
        if child:  
            return QtCore.QAbstractItemModel.createIndex(self, in_row, in_column, child)  
        else:  
            return QtCore.QModelIndex()  
  
    def parent(self, in_index):  
        if in_index.isValid():  
            p = in_index.internalPointer().parent()  
            if p:  
                return QtCore.QAbstractItemModel.createIndex(self, p.row(),0,p)  
        return QtCore.QModelIndex()
  
    def columnCount(self, in_index):  
        return self._root.columnCount()
  
    def data(self, in_index, role):  
        if not in_index.isValid():
            return None  
        node = in_index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # print in_index.column(), in_index.row(), role
            return node.data(in_index.column())
        elif role == QtCore.Qt.BackgroundRole:
            # print "Font role"
            return None
        return None

    def setData(self, in_index, value, role):
        node = in_index.internalPointer()
        if role == QtCore.Qt.EditRole:
            current_value = node.data(in_index.column())
            if current_value != value:
                ret = node.setData(in_index.column(), value)
                if ret:
                    self.dataChanged.emit(in_index, in_index)
                    print "Change done"
                    return True
        return False


class UI(QtGui.QWidget):

    closeRequested = QtCore.pyqtSignal() 

    def __init__(self, xsize, ysize, title, parent=None, window_flags=QtCore.Qt.Window):
        if QtGui.QApplication.startingUp():
            self._app = QtGui.QApplication(sys.argv)

        QtGui.QWidget.__init__(self, parent=parent)
        self.setWindowFlags(window_flags)

        # self.connect("destroy", self.__on_destroy)
        self.size_hint = QtCore.QSize(xsize, ysize)
        self.setMinimumSize(300, 200)
        self.setWindowTitle(title)
        # self.set_property("border-width", 5)
        # self.set_transient_for(parent)
        # if parent is not None:
        #     self.connect("key-press-event", self.__on_key_press)
        #     self.set_destroy_with_parent(destroy_with_parent)
        # if parent is None and check_python_interactive():
        #     self.connect('delete-event', self.hide_and_quit_on_delete)

    # def __on_destroy(self, window):
    #     if self.transient_parent is None:
    #         gtk.main_quit()

    # def __on_key_press(self, window, event):
    #     if event.keyval == gtk.keysyms.Escape:
    #         self.emit("delete-event", event)
    #         # self.hide()

    # def hide_and_quit_on_delete(self, window, event):
    #     print "Hide on delete"
    #     window.hide()
    #     gtk.main_quit()
    #     return True

    def closeEvent(self, event):
        self.closeRequested.emit()
        QtGui.QWidget.closeEvent(self, event)

    def sizeHint(self):
        return self.size_hint

    def add_box(self, box):
        self.setLayout(box)
        return box

    def start(self):
        QtGui.QWidget.show(self)
        QtGui.QApplication.instance().exec_()


class Experience(object):

    def __init__(self):
        self.thread = None
        self.spinner = None
        self.mutex = QtCore.QMutex()

    def add_spinner(self, box):
        self.label = QtGui.QLabel("    ")
        self.spinner = waitingspinnerwidget.QtWaitingSpinner(self.label)
        self.spinner.setLineLength(4)
        self.spinner.setInnerRadius(3)
        self.spinner.setNumberOfLines(10)
        self.spinner.hide()
        box.add(self.label)

    def do_update(self, parameter_changed=None):
        if not self.mutex.tryLock():
            # call to do_update() caused by parameter set in before_update() -> ignore it
            return

        print "Start do update"
        self.stopping()
        res = self.before_update(parameter_changed)

        if res is not False:
            if self.spinner is not None:
                self.spinner.start()
                self.spinner.show()
            self.thread = LongRunning(self.update, (parameter_changed), dict(),
                                 self.__after_update)
            self.thread.start()
        print "Done do update"
        self.mutex.unlock()

    def before_update(self, changed):
        pass

    def update(self, changed):
        pass

    def __after_update(self, result):
        if self.spinner is not None:
            self.spinner.stop()
            self.spinner.hide()
        if not (isinstance(result, bool) and result is False):
            self.after_update(result)

    def after_update(self, result):
        pass

    def stopping(self):
        if self.thread is not None:
            self.thread.cancel()
            self.thread.wait()


class LongRunning(QtCore.QThread):

    def __init__(self, fct, args, kwargs, cbk=None):
        self.fct = fct
        self.args = args
        self.kwargs = kwargs
        self.cbk = cbk
        self._is_alive = True
        QtCore.QThread.__init__(self)

    def is_alive(self):
        return self._is_alive

    def cancel(self):
        self._is_alive = False        

    def run(self):
        result = self.fct(self.args, self)
        if self.is_alive() and self.cbk:
            self.cbk(result)


class TestExperience(Experience):

    def __init__(self):
        self.gui = UI(100, 100, "Wavelet Transform 2D")
        bv = self.gui.add_box(VBox())

        self.pv = bv.add(PlotView())
        bv.add(NavigationToolbar(self.pv))

        ctl = bv.add(HBox())
        t1 = TextParameter(ctl, self, "A:", "Test", max_lenght=8)
        TextParameter(ctl, self, "B:", "Test")
        ListParameter(ctl, self, "B:", ["A", "B", "C", "D", 5, 9, 10])
        ScaleRangeParameter(ctl, self, "B:", -2, 10, 1, 5)
        OpenImage(ctl, self)
        UpdateButton(ctl, self)
        ctl.add(EntryDescription("Put your text", n_chars=15))

        self.update(t1)
        self.gui.start()

    def update(self, changed):
        print 'Update:', changed, changed.get()
        self.pv.figure.clear()
        ax = self.pv.figure.add_subplot(111)
        ax.plot(np.linspace(0, 10) ** 2)

        print "Done"


def test_qt():
    app = QtGui.QApplication(sys.argv)
    # print erro_msg("This is a test")

    gui = UI(400, 300, "This is a test")

    vbox = VBox()
    vbox.add(QtGui.QLabel('This is a test', gui))

    vbox.add(QtGui.QPushButton('Press Me', gui))

    gui.add_box(vbox)
    gui.start()
    print "Lets start"
    app.exec_()


def test_gui():
    app = QtGui.QApplication(sys.argv)
    test = TestExperience()
    test.gui.start()
    print "Lets start"
    app.exec_()


if __name__ == '__main__':
    # test_qt()
    test_gui()
