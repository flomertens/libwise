'''
Created on Mar 9, 2012

@author: fmertens
'''
import os
import gtk
import gobject
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg

import imgutils


def select_file(parent=None, current_folder=None, action=gtk.FILE_CHOOSER_ACTION_SAVE):
    if action == gtk.FILE_CHOOSER_ACTION_SAVE:
        button_ok = gtk.STOCK_SAVE
    elif action == gtk.FILE_CHOOSER_ACTION_OPEN:
        button_ok = gtk.STOCK_OPEN

    dialog = gtk.FileChooserDialog(action=action,
                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                            button_ok, gtk.RESPONSE_OK), parent=parent)
    dialog.set_default_response(gtk.RESPONSE_OK)
    if current_folder is not None:
        dialog.set_current_folder(current_folder)
    response = dialog.run()
    dest = None
    if response == gtk.RESPONSE_OK:
        dest = dialog.get_filename()
    dialog.destroy()
    return dest


def select_folder():
    dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_APPLY, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    response = dialog.run()
    dest = None
    if response == gtk.RESPONSE_OK:
        dest = dialog.get_filename()
    dialog.destroy()
    return dest


def error_msg(msg, parent=None):
    dial = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
                             flags=gtk.DIALOG_MODAL, message_format=msg)
    dial.run()
    dial.destroy()


def check_python_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')


class PlotView(FigureCanvas):

    def __init__(self, figure=None):
        if figure is None:
            figure = Figure(dpi=90, frameon=True)
        self.figure = figure
        FigureCanvas.__init__(self, figure)


class NavigationToolbar(NavigationToolbar2GTKAgg):

    def __init__(self, plot_view):
        super(NavigationToolbar, self).__init__(plot_view, None)


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


class WidgetParameter(Parameter, gtk.HBox):

    def __init__(self, box, experience, initial_value=None):
        Parameter.__init__(self, experience, initial_value)
        gtk.HBox.__init__(self, False, 10)
        box.pack_start(self, False, True)


class NamedWidgetParameter(WidgetParameter):

    def __init__(self, box, experience, name, initial_value=None):
        WidgetParameter.__init__(self, box, experience, initial_value)
        if name is not None:
            label = gtk.Label(name)
            self.pack_start(label, False, True)


class TextParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, value, max_lenght=-1):
        NamedWidgetParameter.__init__(self, box, experience, name, value)

        self.entry = gtk.Entry()
        self.entry.set_width_chars(max_lenght)
        self.entry.set_text(str(value))
        self.pack_start(self.entry, False, False)

        self.entry.connect('activate', self.on_activated)

        self._initialized()

    def on_activated(self, entry):
        self.set(self.entry.get_text())

    def get(self):
        return self.entry.get_text()

    def set(self, value, update=True):
        self.entry.set_text(str(value))
        NamedWidgetParameter.set(self, value, update=update)


class FloatParamater(TextParameter):

    def get(self):
        return float(self.entry.get_text())


class ListParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, values,
                 initial_value=None):
        NamedWidgetParameter.__init__(self, box, experience, name,
                                      initial_value)
        self.values = dict()
        self.orders = []

        self.combo = gtk.combo_box_new_text()
        self.pack_start(self.combo, True, True)

        self.combo.connect("changed", self.on_changed)
        self.set_values(values, initial_value)
        self._initialized()

    def on_changed(self, combobox):
        text = self.combo.get_active_text()
        if text is not None:
            self.set(self.values[text])

    def set_index(self, index):
        self.combo.set_active(index)

    def set_values(self, values, initial_value=None):
        self.combo.get_model().clear()
        for value in values:
            if isinstance(values, dict):
                v = values[value]
            else:
                v = value
            self.values[str(value)] = v
            self.orders.append(str(value))
            self.combo.append_text(str(value))
        if initial_value and initial_value in values:
            self.combo.set_active(self.orders.index(str(initial_value)))
        else:
            self.combo.set_active(0)


class RangeParameter(NamedWidgetParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 range_widget, initial_value=None):
        if initial_value is None:
            initial_value = lower
        NamedWidgetParameter.__init__(self, box, experience, name,
                                      initial_value)

        self.adj = gtk.Adjustment(initial_value, lower, upper, step, 1, 0)
        self.range_widget = range_widget
        self.range_widget.set_adjustment(self.adj)
        self.range_widget.set_update_policy(gtk.UPDATE_DELAYED)
        self.range_widget.connect("value-changed", self.on_changed)
        self.pack_start(self.range_widget, True, False)

        if initial_value is not None:
            self.set(initial_value, update=False)

        self._initialized()

    def set_max(self, maxi):
        self.adj.set_upper(maxi)
        if self.adj.get_value() > maxi:
            self.range_widget.set_value(maxi)
            self.set(maxi, update=False)

    def get_max(self):
        return self.adj.get_upper()

    def set_min(self, mini):
        self.adj.set_lower(mini)
        if self.adj.get_value() < mini:
            self.range_widget.set_value(mini)
            self.set(mini, update=False)

    def set(self, value, update=True):
        if value >= self.adj.get_lower() and value <= self.adj.get_upper():
            super(RangeParameter, self).set(value, update)
            self.range_widget.set_value(value)

    def on_changed(self, spinbutton):
        self.set(self.range_widget.get_value())


class SpinRangeParameter(RangeParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 initial_value=None):
        RangeParameter.__init__(self, box, experience, name, lower,
                                upper, step, gtk.SpinButton(), initial_value)


class ScaleRangeParameter(RangeParameter):

    def __init__(self, box, experience, name, lower, upper, step,
                 initial_value=None, digits=0):
        scale = gtk.HScale()
        scale.set_value_pos(gtk.POS_LEFT)
        scale.set_size_request(200, 30)
        scale.set_digits(digits)
        RangeParameter.__init__(self, box, experience, name, lower,
                                upper, step, scale, initial_value)


class Button(WidgetParameter):

    def __init__(self, box, experience, name, on_clicked=None):
        WidgetParameter.__init__(self, box, experience, None)
        self.bn = gtk.Button(name)
        self.bn.set_property("use-stock", True)
        if on_clicked is None:
            on_clicked = self.on_clicked
        self.bn.connect("clicked", on_clicked)
        self.pack_start(self.bn, True, True)

        self._initialized()


class UpdateButton(Button):

    def __init__(self, box, experience):
        Button.__init__(self, box, experience, gtk.STOCK_REFRESH, on_clicked=self.on_clicked)

    def on_clicked(self, bn):
        self.set(1)


class OpenImage(Button):
    
    def __init__(self, box, experience, img=None):
        Button.__init__(self, box, experience, "Open image...", on_clicked=self.on_clicked)
        if img is not None:
            if not isinstance(img, imgutils.Image):
                img = imgutils.Image(img)
            self.set(img, update=False)

    def set(self, value, update=True):
        Button.set(self, value, update=update)
        if not hasattr(value, "file"):
            label = "DATA"
        else:
            label = os.path.basename(value.file)
        self.bn.set_label(label)

    def on_clicked(self, bn):
        path = select_file(action=gtk.FILE_CHOOSER_ACTION_OPEN)

        if path is not None:
            try:
                img = imgutils.guess_and_open(path)
                self.set(img)
            except:
                pass


class Box(gtk.Box):

    def add(self, element, expand=False):
        self.pack_start(element, expand, True)
        return element


class VBox(gtk.VBox, Box):

    def __init__(self, homogeneous=False, spacing=10):
        gtk.VBox.__init__(self, homogeneous, spacing)


class HBox(gtk.HBox, Box):

    def __init__(self, homogeneous=False, spacing=10):
        gtk.HBox.__init__(self, homogeneous, spacing)


class UI(gtk.Window):

    def __init__(self, xsize, ysize, title, parent=None, destroy_with_parent=True):
        gobject.threads_init()
        gtk.Window.__init__(self)
        self.connect("destroy", self.__on_destroy)
        self.set_default_size(xsize, ysize)
        self.set_title(title)
        self.set_property("border-width", 5)
        self.set_transient_for(parent)
        if parent is not None:
            self.connect("key-press-event", self.__on_key_press)
            self.set_destroy_with_parent(destroy_with_parent)
        # if parent is None and check_python_interactive():
        #     self.connect('delete-event', self.hide_and_quit_on_delete)

    def __on_destroy(self, window):
        if self.transient_parent is None:
            gtk.main_quit()

    def __on_key_press(self, window, event):
        if event.keyval == gtk.keysyms.Escape:
            self.emit("delete-event", event)
            # self.hide()

    def hide_and_quit_on_delete(self, window, event):
        print "Hide on delete"
        window.hide()
        gtk.main_quit()
        return True

    def add_box(self, box):
        self.add(box)
        return box

    def start(self):
        self.show_all()
        gtk.main()


class EntryDescription(gtk.Entry):

    def __init__(self, description, text=None, n_chars=None):
        super(EntryDescription, self).__init__()
        if n_chars is not None:
            self.set_width_chars(n_chars)
        self.description = description
        self.description_mode = False

        self.set_tooltip_text(description)

        if text is None or text == "":
            self.set_description_mode(True)
        else:
            self.set_text(text)

        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)

    def set_description_mode(self, value):
        if value == self.description_mode:
            return
        self.description_mode = value
        if self.description_mode is True:
            self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('gray'))
            super(EntryDescription, self).set_text(self.description)
        else:
            self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
            super(EntryDescription, self).set_text("")

    def on_focus_in(self, entry, event):
        self.set_description_mode(False)

    def on_focus_out(self, entry, event):
        if self.get_text_length() == 0:
            self.set_description_mode(True)

    def get_text(self):
        if self.description_mode is True:
            return ""
        return super(EntryDescription, self).get_text()

    def set_text(self, text):
        if text == "" or text is None:
            self.set_description_mode(True)
        else:
            self.set_description_mode(False)
            super(EntryDescription, self).set_text(text)

    def clear(self):
        self.set_description_mode()
        self.emit("changed")


class ObjectComboBox(gtk.ComboBox):

    def __init__(self, objects=[], initial=object):
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str)
        super(ObjectComboBox, self).__init__(self.model)

        cell = gtk.CellRendererPixbuf()
        self.pack_start(cell, False)
        self.add_attribute(cell, 'stock-id', 2)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        self.fill(objects, initial)

    def append(self, object):
        if hasattr(object, 'get_image_id'):
            stock_id = object.get_image_id()
        else:
            stock_id = ''
        self.model.append((object, str(object), stock_id))

    def fill(self, objects, initial=None):
        self.model.clear()
        if objects is not None:
            for object in objects:
                self.append(object)
        if objects is not None:
            if initial in objects:
                self.set_active(objects.index(initial))
            else:
                self.set_active(0)

    def size(self):
        return len(self.model)

    def get_all(self):
        return [k[0] for k in self.model]

    def get_current(self):
        i = self.get_active()
        if i >= 0 and i < len(self.model):
            return self.model[i][0]
        return None


class EntryDialog(gtk.Dialog):

    def __init__(self, description, value, title="", parent=None):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        gtk.Dialog.__init__(self, title, parent, flags, buttons)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, padding=5)

        hbox.pack_start(gtk.Label(description), False, False, padding=5)

        self.entry = gtk.Entry()
        self.entry.set_text(value)
        hbox.pack_start(self.entry, False, False, padding=5)

        self.show_all()

    def run(self):
        ret = gtk.Dialog.run(self)
        value = self.entry.get_text()
        self.destroy()
        if ret == gtk.RESPONSE_ACCEPT:
            return value
        return None


class Experience():

    def add_spinner(self, box):
        self.spinner = gtk.Spinner()
        box.add(self.spinner)
        gobject.idle_add(self.spinner.hide)

    def do_update(self, parameter_changed=None):
        res = self.before_update(parameter_changed)

        if hasattr(self, 'spinner'):
            self.spinner.start()
            self.spinner.show()

        if res is not False:
            thread = LongRunning(self.update, (parameter_changed), dict(),
                                 self.__after_update)
            thread.start()

    def before_update(self, changed):
        pass

    def update(self, changed):
        pass

    def __after_update(self, result):
        if hasattr(self, 'spinner'):
            self.spinner.stop()
            self.spinner.hide()
        self.after_update(result)

    def after_update(self, result):
        pass


class LongRunning(threading.Thread):

    def __init__(self, fct, args, kwargs, cbk=None):
        self.fct = fct
        self.args = args
        self.kwargs = kwargs
        self.cbk = cbk
        threading.Thread.__init__(self, target=fct, args=args, kwargs=kwargs)

    def run(self):
        result = self.fct(self.args)
        if self.cbk and (not isinstance(result, bool) or result is not False):
            gobject.idle_add(self.cbk, result)


class TestExperience(Experience):

    def __init__(self):
        gui = UI(100, 100, "Wavelet Transform 2D")
        bv = gui.add_box(VBox())
        self.ctl = bv.add(HBox())

        OpenImage(self.ctl, self)

        gui.start()

    def update(self, changed):
        print 'Update:', changed

if __name__ == '__main__':
    # dial = EntryDialog("Test", "value")
    # print dial.run()
    TestExperience()
