from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.backends.qt_editor.figureoptions as figureoptions

import uiutils

from plotutils_base import *


def subplots(**kargs):
    figure = BaseCustomFigure()
    axes = figure.subplots(**kargs)
    window = BaseFigureWindow(figure=figure)
    window.show()

    return axes


def subplots_replayable(plt_fct, *args):
    figure = ReplayableFigure(plt_fct, *args, dpi=75)
    window = BaseFigureWindow(figure=figure)
    window.show()

    return figure    


class Cursor(QtCore.QObject):

    cursorMoved = QtCore.pyqtSignal(list) 

    def __init__(self, ax, figure, other_axs=[]):
        QtCore.QObject.__init__(self)
        self.ax = ax
        self.all_axs = [ax] + other_axs
        self.canvas = figure.canvas
        self.back = None

        self.lx = ax.axhline(color='k', ls='-.', visible=False)
        self.ly = ax.axvline(color='k', ls='-.', visible=False)

        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('draw_event', self.on_draw)

        self.visible = False

    def set_visibility(self, visible):
        self.lx.set_visible(visible)
        self.ly.set_visible(visible)
        self.visible = visible

    def on_draw(self, event):
        self.back = self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        self.set_visibility(False)

    def on_mouse_move(self, event):
        if not event.inaxes or not self.canvas.widgetlock.available(self):
            if self.visible:
                self.set_visibility(False)
                self.draw()
        else:
            self.set_visibility(True)
            x, y = event.xdata, event.ydata

            cursor_positions = []
            for ax in self.all_axs:
                pos = ax.transData.inverted().transform((event.x, event.y))
                cursor_positions.append(pos)

            self.cursorMoved.emit(cursor_positions)
            # update the line positions
            self.lx.set_ydata(y)
            self.ly.set_xdata(x)

            self.draw()

    def draw(self):
        self.canvas.restore_region(self.back)
        self.ax.draw_artist(self.lx)
        self.ax.draw_artist(self.ly)
        self.canvas.update()


class AbstractTwoPointsRequest(object):

    def __init__(self, canvas):
        self.canvas = canvas

        self.axes = None
        self.p1 = None
        self.p2 = None

        self.state_pressed = False

        self.background = None

        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.cid_draw = None

    def release(self):
        self.canvas.mpl_disconnect(self.cid_press)
        if self.cid_draw is not None:
            self.canvas.mpl_disconnect(self.cid_draw)
        self.clear()
        self.release_line()

    def on_mouse_press(self, event):
        if self.state_pressed:
            # catched double press events
            return

        if event.inaxes is None or not self.check_axes(event.inaxes):
            return

        self.state_pressed = True

        if self.axes is not None:
            self.clear()

        self.background = None

        self.axes = event.inaxes
        self.p1 = np.array([event.xdata, event.ydata])
        self.p2 = None

        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion_notify)
        self.cid_draw = self.canvas.mpl_connect('draw_event', self.on_draw)

        self.axes.set_autoscale_on(False)
        self.init_line()

    def on_mouse_release(self, event):
        self.canvas.mpl_disconnect(self.cid_motion)
        self.canvas.mpl_disconnect(self.cid_release)

        if self.p1 is not None and self.p2 is not None:
            if not self.action():
                self.clear()

        self.state_pressed = False

    def on_draw(self, event):
        self.background = None
        self.__draw_line()

    def on_motion_notify(self, event):
        if event.inaxes is not self.axes:
            self.on_mouse_release(event)
            return

        self.p2 = np.array([event.xdata, event.ydata])
        self.set_line_data(self.p1, self.p2)
        self.__draw_line()

    def check_axes(self, axes):
        pass

    def init_line(self):
        pass

    def set_line_data(self, p1, p2):
        pass

    def draw_line(self):
        pass

    def release_line(self):
        pass

    def clear(self):
        if self.axes is not None:
            try:
                self.release_line()
                self.init_line()
                self.canvas.restore_region(self.background)
                self.canvas.update()
            except:
                pass

    def __draw_line(self):
        if self.background is None:
            self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.canvas.restore_region(self.background)
        self.draw_line()
        self.canvas.update()


class ProfileLine(AbstractTwoPointsRequest):

    def __init__(self, parent, canvas):
        AbstractTwoPointsRequest.__init__(self, canvas)

        self.pos_background = None
        self.path_position = None
        self.line = None

        self.profile_window = ProfileWindow(parent)
        self.profile_window.closeRequested.connect(self.clear)

    def check_axes(self, axes):
        return axes_has_artist(axes, AxesImage)

    def release(self):
        AbstractTwoPointsRequest.release(self)
        self.profile_window.close()

    def action(self):
        ax1 = self.profile_window.get_axes()
        ax2 = ax1.twiny()

        ax1.set_ylabel("Intensity")
        ax1.set_xlabel("X")
        ax2.set_xlabel("Y")
        got_data = False
        datas = []

        for artist in self.axes.get_children():
            if isinstance(artist, AxesImage):
                data = artist.get_array()
                xe0, xe1, ye0, ye1 = artist.get_extent()
                tr_x, itr_x = nputils.affine_transform(xe0, xe1, 0, data.shape[1])
                tr_y, itr_y = nputils.affine_transform(ye0, ye1, 0, data.shape[0])
                x0, y0 = int(tr_x(self.p1[0])), int(tr_y(self.p1[1]))
                x1, y1 = int(tr_x(self.p2[0])), int(tr_y(self.p2[1]))
                length = int(np.hypot(x1 - x0, y1 - y0))
                if length == 0:
                    continue
                x, y = np.linspace(x0, x1, length), np.linspace(y0, y1, length)
                zi = data[y.astype(np.int), x.astype(np.int)]
                xdata = itr_x(x)  # get the middle of the pixel
                ydata = itr_y(y)

                datas.append(zi)

                if np.abs(x[-1] - x[0]) > np.abs(y[-1] - y[0]):
                    ax1.plot(xdata, zi, marker='+')
                    ax1.set_xlim(xdata[0], xdata[-1])
                    ax2.plot(ydata, zi, visible=False)
                    ax2.set_xlim(ydata[0], ydata[-1])
                else:
                    ax2.plot(ydata, zi, marker='+')
                    ax2.set_xlim(ydata[0], ydata[-1])
                    ax1.plot(ydata, zi, visible=False)
                    ax1.set_xlim(xdata[0], xdata[-1])
                got_data = True

        if not got_data:
            return False

        # if len(datas) > 5:
        #     ax1.clear()
        #     print np.array(datas).shape
        #     ax1.imshow(np.array(datas), norm=LogNorm())
        #     ax1.set_xlim(None, None)

        self.cusor = Cursor(ax2, self.profile_window.get_figure(), [ax1])
        self.path_position = self.axes.scatter([], [], animated=True)
        self.pos_background = None
        self.cusor.cursorMoved.connect(self.on_cursor_moved)
        self.profile_window.draw()

        return True

    def on_draw(self, event):
        AbstractTwoPointsRequest.on_draw(self, event)
        self.pos_background = None

    def on_cursor_moved(self, positions):
        x = positions[0][0]
        y = positions[1][0]
        self.path_position.set_offsets([y, x])
        self.draw_position()

    def draw_position(self):
        if self.pos_background is None:
            self.pos_background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.canvas.restore_region(self.pos_background)
        self.canvas.figure.draw_artist(self.path_position)
        self.canvas.update()

    def init_line(self):
        self.line, = self.axes.plot([], [], marker='o', markerfacecolor='r', animated=True)

    def release_line(self):
        if self.line is not None:
            self.line.remove()

    def set_line_data(self, p1, p2):
        self.line.set_data(zip(self.p1, self.p2))

    def draw_line(self):
        self.canvas.figure.draw_artist(self.line)

    def clear(self):
        if self.path_position is not None:
            self.path_position.set_offsets([])
        AbstractTwoPointsRequest.clear(self)


class PlotImageStats(AbstractTwoPointsRequest):

    def __init__(self, parent, canvas):
        AbstractTwoPointsRequest.__init__(self, canvas)
        self.stats_window = StatsWindow(parent, canvas)

        self.rect1 = None
        self.rect2 = None

    def check_axes(self, axes):
        return axes_has_artist(axes, Line2D) or axes_has_artist(axes, AxesImage)

    def init_line(self):
        self.rect1 = Rectangle([0, 0], 0, 0, ec=black, fc='none', lw=2, animated=True, zorder=10)
        self.rect2 = Rectangle([0, 0], 0, 0, ec='none', fc=blue, alpha=0.2, animated=True, zorder=10)
        self.axes.add_patch(self.rect1)
        self.axes.add_patch(self.rect2)

    def release_line(self):
        if self.rect1 is not None:
            self.rect1.remove()
        if self.rect2 is not None:
            self.rect2.remove()

    def release(self):
        AbstractTwoPointsRequest.release(self)
        self.stats_window.close()

    def action(self):
        self.stats_window.init()

        for artist in self.axes.get_children():
            if isinstance(artist, AxesImage):
                fulldata = artist.get_array()
                xe0, xe1, ye0, ye1 = artist.get_extent()
                tr_x, itr_x = nputils.affine_transform(xe0, xe1, 0, fulldata.shape[1])
                tr_y, itr_y = nputils.affine_transform(ye0, ye1, 0, fulldata.shape[0])
                x0, y0 = int(tr_x(self.p1[0])), int(tr_y(self.p1[1]))
                x1, y1 = int(tr_x(self.p2[0])), int(tr_y(self.p2[1]))
                x0, x1 = sorted([x0, x1])
                y0, y1 = sorted([y0, y1])
                data = fulldata[y0:y1, x0:x1]
                if min(data.shape) < 2:
                    continue
                fct_index2coord = lambda index: (itr_x(x0 + index[1] + 0.5),
                                                 itr_y(y0 + index[0] + 0.5))
                self.stats_window.add_data(self.axes, data, str(artist), fct_index2coord)
            elif isinstance(artist, Line2D):
                y = np.array(artist.get_ydata())
                x = np.array(artist.get_xdata())
                x0, x1 = sorted([self.p1[0], self.p2[0]])
                data = y[(x >= x0) & (x <= x1)]
                if len(data) <= 3:
                    continue
                try:
                    i0 = np.where(x >= x0)[0][0]
                    fct_index2coord = lambda index: x[i0 + index[0]]
                    self.stats_window.add_data(self.axes, data, str(artist), fct_index2coord)
                except:
                    pass

        if not self.stats_window.has_data():
            return False

        self.stats_window.show()
        self.stats_window.activateWindow()

        return True

    def set_line_data(self, p1, p2):
        l, b = np.min([p1, p2], axis=0)
        w, h = np.abs(p2 - p1)
        if axes_has_artist(self.axes, Line2D)\
                and not axes_has_artist(self.axes, AxesImage):
            ymin, ymax = self.axes.get_ylim()
            b = ymin - 10
            h = ymax - ymin + 10
        self.rect1.set_bounds(l, b, w, h)
        self.rect2.set_bounds(l, b, w, h)

    def draw_line(self):
        self.canvas.figure.draw_artist(self.rect1)
        self.canvas.figure.draw_artist(self.rect2)


class StatsWindow(uiutils.UI):

    def __init__(self, parent, canvas):
        uiutils.UI.__init__(self, 600, 500, "Statistics")

        self.setLayout(QtGui.QVBoxLayout())
        self.canvas = canvas

        self.notebook = QtGui.QTabWidget()
        # self.notebook.set_scrollable(True)
        self.layout().addWidget(self.notebook)
        # self.connect("delete-event", self.on_delete)

    # def on_delete(self, widget, event):
    #     self.hide()
    #     return True

    def init(self):
        self.notebook.clear()

    def has_data(self):
        return self.notebook.count() > 0

    def add_stat_entry(self, vbox, text, value):
        hbox = QtGui.QHBoxLayout()
        # hbox.set_border_width(2)
        vbox.addLayout(hbox)

        label = QtGui.QLabel("<b>%s:</b>" % (text))
        # label.set_width_chars(20)
        # label.set_alignment(0, 0)
        hbox.addWidget(label)
        hbox.addWidget(QtGui.QLabel(value))

    def add_data(self, axes, data, title, fct_index2coord):
        tab = QtGui.QWidget()
        vbox = QtGui.QFormLayout()
        tab.setLayout(vbox)
        vbox.addRow(QtGui.QLabel("<b>Dimensions:</b>"), QtGui.QLabel("%s n=%s" % (str(data.shape), data.size)))
        vbox.addRow(QtGui.QLabel("<b>Mean:</b>"), QtGui.QLabel("%g" % data.mean()))
        vbox.addRow(QtGui.QLabel("<b>Median:</b>"), QtGui.QLabel("%g" % np.median(data)))
        vbox.addRow(QtGui.QLabel("<b>Sum:</b>"), QtGui.QLabel("%g" % data.sum()))

        coord_max = fct_index2coord(nputils.coord_max(data))
        vbox.addRow(QtGui.QLabel("<b>Maximum:</b>"), QtGui.QLabel("%g at %s" % (data.max(), coord_max)))

        coord_min = fct_index2coord(nputils.coord_min(data))
        vbox.addRow(QtGui.QLabel("<b>Minimum:</b>"), QtGui.QLabel("%g at %s" % (data.min(), coord_min)))

        vbox.addRow(QtGui.QLabel("<b>Standart deviation:</b>"), QtGui.QLabel("%g" % data.std()))
        vbox.addRow(QtGui.QLabel("<b>P90:</b>"), QtGui.QLabel("%g" % np.percentile(data, 90)))

        coord_com = fct_index2coord(measurements.center_of_mass(data))
        vbox.addRow(QtGui.QLabel("<b>Center of mass:</b>"), QtGui.QLabel(str(np.round(coord_com, decimals=2))))

        self.notebook.addTab(tab, title)

        if data.ndim == 2:
            xmin, ymin = coord_min
            xmax, ymax = coord_max

            xcom, ycom = coord_com
            a = axes.scatter(xcom, ycom, animated=True, edgecolors=black, facecolors=green, zorder=20)
            self.canvas.figure.draw_artist(a)

        elif data.ndim == 1:
            xmin, ymin = coord_min, data.min()
            xmax, ymax = coord_max, data.max()

        a = axes.scatter(xmin, ymin, animated=True, edgecolors=black, facecolors=blue, zorder=20)
        self.canvas.figure.draw_artist(a)

        a = axes.scatter(xmax, ymax, animated=True, edgecolors=black, facecolors=red, zorder=20)
        self.canvas.figure.draw_artist(a)

        self.canvas.update()


class BaseFigureWindow(uiutils.UI):

    def __init__(self, figure=None, name="", parent=None, extended_toolbar=True):
        uiutils.UI.__init__(self, 800, 500, name)
        self.setLayout(QtGui.QVBoxLayout())

        self.tooltip_manager = TooltipManager(self)

        if figure is None:
            figure = BaseCustomFigure()
        self.figure = figure

        if isinstance(self.figure.canvas, NotAutoResizeFigureCanvas):
            NotAutoResizeFigureCanvas(self.figure)
        else:
            FigureCanvas(self.figure)

        if extended_toolbar:
            figure.navigation = ExtendedNavigationToolbar(figure.canvas, self)
        else:
            figure.navigation = NavigationToolbar(figure.canvas, self)
# 
        self.layout().addWidget(figure.canvas)
        self.layout().addWidget(figure.navigation)
        self.figure.canvas.draw()

    def closeEvent(self, event):
        self.tooltip_manager.release()
        self.deleteLater()
        uiutils.UI.closeEvent(self, event)

    # def show(self):
    #     self.start()


class ExtFigureWindow(BaseFigureWindow):

    def __init__(self, figure, name, figure_stack, pos):
        BaseFigureWindow.__init__(self, figure, name, None)

        self.figure_stack = figure_stack
        self.pos = pos
        self.name = name

    def closeEvent(self, event):
        self.figure.navigation.home()
        self.figure_stack.add_figure(self.name, self.figure, position=self.pos)
        BaseFigureWindow.closeEvent(self, event)


class ProfileWindow(BaseFigureWindow):

    closeRequested = QtCore.pyqtSignal() 

    def __init__(self, parent=None):
        BaseFigureWindow.__init__(self, None, "Profile", parent, extended_toolbar=False)

    def closeEvent(self, event):
        self.closeRequested.emit()
        BaseFigureWindow.closeEvent(self, event)

    def get_figure(self):
        return self.figure

    def get_axes(self):
        figure = self.get_figure()
        figure.clear()
        ax = figure.subplots()
        return ax

    def draw(self):
        self.figure.canvas.draw()
        self.show()
        self.activateWindow()


class BaseFigureTooltip:

    def get_tooltip(self, axes, coord):
        pass


class FigureTooltips(BaseFigureTooltip):

    def __init__(self):
        self.axes = dict()

    def add_tooltip(self, axes, coord, text, tol=4):
        if axes not in self.axes:
            self.axes[axes] = []
        self.axes[axes].append((coord, text, tol))

    def get_tooltip(self, axes, coord):
        if axes not in self.axes:
            return None
        texts = []
        for tcoord, text, tol in self.axes[axes]:
            if np.linalg.norm(tcoord - coord) < tol:
                texts.append(text)
        if len(texts) == 0:
            return None
        return "\n".join(texts)


class IntensityFigureTooltip(BaseFigureTooltip):

    def get_tooltip(self, axes, coord):
        text = ""
        i = 0

        for artist in axes.get_children():
            if isinstance(artist, AxesImage):
                data = artist.get_array()
                if hasattr(axes, "_grid_helper") and isinstance(axes._grid_helper, GridHelperCurveLinear):
                    (xdata,), (ydata,) = axes._grid_helper.grid_finder.inv_transform_xy((coord[1],), (coord[0],))
                    y0, x0 = np.round(coord)
                else:
                    xe0, xe1, ye0, ye1 = artist.get_extent()
                    tr_x, itr_x = nputils.affine_transform(xe0, xe1, 0, data.shape[1])
                    tr_y, itr_y = nputils.affine_transform(ye0, ye1, 0, data.shape[0])
                    x0 = int(tr_x(coord[1]))
                    y0 = int(tr_y(coord[0]))

                    xdata = itr_x(x0 + 0.5)
                    ydata = itr_y(y0 + 0.5)

                if nputils.check_index(data, y0, x0):
                    intensity = data[y0, x0]
                    text += "\n<b>Image %s:</b> (%s, %s): %s" % (i, xdata, ydata, intensity)
                    text += "\n Data coordinate: (%s, %s)" % (y0, x0)
                i += 1

        return text.strip()


class TooltipManager:

    def __init__(self, window):
        self.tooltips = dict()
        self.current_figure = None
        self.cid_motion = None

    def set_current_figure(self, figure):
        self.current_figure = figure
        if figure in self.tooltips:
            self.cid_motion = figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def get_figure_tooltip(self, figure):
        return self.tooltips.get(figure)

    def add_figure_tooltip(self, figure, figure_tooltip):
        self.tooltips[figure] = figure_tooltip

    def on_motion(self, event):
        if event.inaxes:
            tooltips = self.tooltips[self.current_figure]
            text = tooltips.get_tooltip(event.inaxes, np.array([event.ydata, event.xdata]))
            if len(text) > 0:
                text = "<p style='white-space:pre'>" + text
            self.current_figure.canvas.setToolTip(text)
        else:
            self.current_figure.canvas.setToolTip("")

    def release(self):
        if self.cid_motion is not None and self.current_figure is not None:
            self.current_figure.canvas.mpl_disconnect(self.cid_motion)


class ExtendedNavigationToolbar(NavigationToolbar):

    def __init__(self, canvas, window, profile=True):
        self.toolitems = list(self.toolitems)
        self.toolitems.insert(6, ('Profile', 'Get the profile of a line in an image', 
            os.path.join(imgutils.RESSOURCE_PATH, "profile"), 'profile'))
        self.toolitems.insert(7, ('Stats', 'Get statistics on a portion of an image/line', 
            os.path.join(imgutils.RESSOURCE_PATH, "stats"), 'stats'))
        NavigationToolbar.__init__(self, canvas, window)
        self._actions['profile'].setCheckable(True)
        self._actions['stats'].setCheckable(True)

    def hideEvent(self, event):
        self.toogle_off_all_active()

    def _icon(self, name):
        if name.startswith("/"):
            return QtGui.QIcon(name)
        return NavigationToolbar._icon(self, name)

    def _update_buttons_checked(self):
        NavigationToolbar._update_buttons_checked(self)
        self._actions['profile'].setChecked(self._active == 'PROFILE')
        self._actions['stats'].setChecked(self._active == 'STATS')

    def zoom(self):
        if self._active != 'ZOOM':
            self.toogle_off_all_active()
        NavigationToolbar.zoom(self)

    def pan(self):
        if self._active != 'PAN':
            self.toogle_off_all_active()
        NavigationToolbar.pan(self)

    def profile(self):
        if self._active == 'PROFILE':
            self._active = None
            self.profile_line.release()
        else:
            self.toogle_off_all_active()
            self._active = 'PROFILE'
            self.profile_line = ProfileLine(None, self.canvas)
        self._update_buttons_checked()

    def stats(self):
        if self._active == 'STATS':
            self._active = None
            self.image_stats.release()
        else:
            self.toogle_off_all_active()
            self._active = 'STATS'
            self.image_stats = PlotImageStats(None, self.canvas)
        self._update_buttons_checked()

    def toogle_off_all_active(self):
        if self._active in ['ZOOM', 'PAN', 'STATS', 'PROFILE']:
            getattr(self, self._active.lower())()

    def save_figure(self, *args):
        self.canvas.figure.navigation = self
        self.sf = SaveFigure(self.canvas.figure, parent=None)


class BaseCustomCanvas(FigureCanvas):

    def __init__(self, figure=None):
        if figure is None:
            figure = BaseCustomFigure(dpi=90, frameon=True)
        self.figure = figure
        FigureCanvas.__init__(self, figure)


class NotAutoResizeFigureCanvas(BaseCustomCanvas):

    def __init__(self, figure=None):
        BaseCustomCanvas.__init__(self, figure=figure)

    def resizeEvent(self, event):
        BaseCustomCanvas.resize_event(self)
        self.draw_idle()
        QtGui.QWidget.resizeEvent(self, event)


class FixedAspectRatioFigureView(QtGui.QScrollArea):

    def __init__(self, figure, auto_dpi=True, auto_dpi_height=True):
        QtGui.QScrollArea.__init__(self)
        self.figure = figure
        self.auto_dpi = auto_dpi
        self.auto_dpi_height = auto_dpi_height

        self.setBackgroundRole(QtGui.QPalette.Dark)

        self.figure = figure
        NotAutoResizeFigureCanvas(self.figure)
        self.setWidget(self.figure.canvas)

    def resizeEvent(self, event):
        winch, hinch = self.figure.get_size_inches()

        if self.auto_dpi:
            w, h = self.width(), self.height()
            if self.auto_dpi_height:
                dpi = h / hinch
            else:
                dpi = w / winch
            self.figure.set_dpi(dpi)
        else:
            dpi = self.figure.get_dpi()

        w = int(winch * dpi)
        h = int(hinch * dpi) - 2

        self.figure.canvas.setFixedSize(w, h)
        QtGui.QScrollArea.resizeEvent(self, event)


class PresetSetting(uiutils.CustomNode):

    def __init__(self, preset, group, setting, value):
        self.group = group
        self.setting = setting
        self.preset = preset
        uiutils.CustomNode.__init__(self, [group, setting, value])

    def value(self):
        return str(self.preset.get(self.group, self.setting))

    def set_default(self):
        self.preset.set_default(self.group, self.setting)
        uiutils.CustomNode.setData(self, 2, self.value())

    def setData(self, column, value):
        if isinstance(value, QtCore.QVariant):
            value = unicode(value.toPyObject())
        try:
            self.preset.set(self.group, self.setting, value)
            uiutils.CustomNode.setData(self, column, value)
            return True
        except Exception, e:
            print "Exception while setting %s.%s to %s" % (self.group, self.setting, value)
            print e
        return False


class PresetGroup(uiutils.CustomNode):

    def __init__(self, group):
        self.group = group
        uiutils.CustomNode.__init__(self, [group, '', ''])

    def getChilds(self):
        return self._children


class PresetTreeModel(uiutils.CustomModel):

    def __init__(self, preset):
        self.preset = preset
        self.header = ['Group', 'Setting', 'Value']
        nodes = self.setup_data()

        uiutils.CustomModel.__init__(self, nodes, self.header)

    def setup_data(self):
        nodes = []
        for group in self.preset.get_groups():
            node = PresetGroup(group)
            for setting, value in self.preset.get_settings(group):
                node.addChild(PresetSetting(self.preset, group, setting, str(value)))
            nodes.append(node)
        return nodes

    def flags(self, index):
        if not index.isValid():
            return 0
        if index.column() == 2: 
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, in_index, role):
        if role == QtCore.Qt.FontRole:
            node = self.getNode(in_index)
            is_preset = False
            if isinstance(node, PresetSetting):
                is_preset = self.preset.is_preset(node.group, node.setting)
                # if node.group == 'axes':
                #     print "FontRole", node.group, node.setting, is_preset
            elif isinstance(node, PresetGroup):
                for child in node.getChilds():
                    if self.preset.is_preset(child.group, child.setting):
                        is_preset = True
                        break
                # if node.group == 'axes':
                #     print "FontRole", node.group, is_preset
            font = QtGui.QFont()
            if is_preset:
                font.setBold(True)
            return font
        return uiutils.CustomModel.data(self, in_index, role)


class TreeQSortFilterProxyModel(QtGui.QSortFilterProxyModel):

    def __init__(self):
        QtGui.QSortFilterProxyModel.__init__(self)

    def filterAcceptsRow(self, row, sourceParent):
        pattern = self.filterRegExp().pattern()
        if pattern == '':
            return True
        node = self.sourceModel().getNode(self.sourceModel().index(row, 1, sourceParent))
        if isinstance(node, PresetSetting):
            return pattern in node.setting
        if isinstance(node, PresetGroup):
            for child in node.getChilds():
                if pattern in child.setting:
                    return True
            return False
        return True


class PresetEditor(uiutils.UI):

    changed = QtCore.pyqtSignal() 

    def __init__(self, preset):
        uiutils.UI.__init__(self, 400, 350, "Preset Editor: %s" % preset.get_name())

        self.preset = preset
        self.source_model = PresetTreeModel(preset)
        self.model = TreeQSortFilterProxyModel()
        self.model.setSourceModel(self.source_model)
        self.model.dataChanged.connect(self.on_value_edit)

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        self.tree = QtGui.QTreeView()  
        self.tree.setModel(self.model)  
        vbox.addWidget(self.tree)

        ctl = QtGui.QHBoxLayout()
        vbox.addLayout(ctl)

        self.set_default_bn = QtGui.QPushButton("Set to default")
        self.set_default_bn.clicked.connect(self.on_set_default_clicked)
        ctl.addWidget(self.set_default_bn)

        ctl.addStretch()

        self.filter_entry = uiutils.EntryDescription("Filter")
        self.filter_entry.editingFinished.connect(self.on_filter_changed)
        self.filter_entry.set_clear_on_escape(True)

        ctl.addWidget(self.filter_entry)

        self.save_bn = QtGui.QPushButton("Save")
        self.save_bn.clicked.connect(self.on_save_clicked)
        self.save_bn.setMaximumSize(50, 30)
        self.save_bn.setEnabled(False)
        ctl.addWidget(self.save_bn)

        # self.model_filter.set_visible_func(self.match_func)

    def match_func(self, model, iter):
        query = self.filter_entry.get_text()
        if query == "":
            return True

        group, setting = self.model.get_key(iter)

        if setting != "":
            if query in setting:
                return True

        childiter = model.iter_children(iter)

        while childiter is not None:
            group, setting = self.model.get_key(childiter)
            if query in setting:
                return True
            childiter = model.iter_next(childiter)

        return False

    def on_save_clicked(self, bn):
        dial = uiutils.EntryDialog("Preset name", self.preset.get_name(), parent=self)
        name = dial.run()
        if name is not None and len(name) > 0:
            self.preset.set_name(name)
            self.preset.save()
            self.save_bn.setEnabled(False)

    def on_filter_changed(self):
        self.model.setFilterRegExp(self.filter_entry.get_text())
        self.model.layoutChanged.emit()
        if self.filter_entry.get_text() == "":
            self.tree.collapseAll()
        else:
            self.tree.expandAll()

    def on_set_default_clicked(self, bn):
        index = self.model.mapToSource(self.tree.currentIndex())
        node = self.source_model.getNode(index)
        if isinstance(node, PresetSetting):
            node.set_default()
            self.model.layoutChanged.emit()
            self.save_bn.setEnabled(True)
            self.changed.emit()

    def on_value_edit(self, index, index2):
        self.save_bn.setEnabled(True)
        self.changed.emit()


class SaveFigure(uiutils.UI):

    def __init__(self, figure, auto_dpi=True, parent=None):
        uiutils.UI.__init__(self, 800, 500, "Save plot")
        self.figure = figure

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        self.current_canvas = self.figure.canvas
        sp_keys = ["left", "right", "top", "bottom", "wspace", "hspace"]
        self.current_subplotpars = dict([(key, getattr(self.figure.subplotpars, "%s" % key)) for key in sp_keys])
        self.curent_dpi = self.figure.get_dpi()

        self.figure_view = FixedAspectRatioFigureView(self.figure, auto_dpi=auto_dpi)
        vbox.addWidget(self.figure_view)

        ctl = QtGui.QHBoxLayout()
        vbox.addLayout(ctl)

        self.presets = presetutils.get_all_presets()
        self.combo_presets = QtGui.QComboBox()
        self.combo_presets.addItems([str(preset) for preset in self.presets])
        self.combo_presets.activated.connect(self.on_preset_changed)
        ctl.addWidget(self.combo_presets)

        bn_edit = QtGui.QPushButton('Edit preset')
        bn_edit.clicked.connect(self.on_edit_clicked)
        ctl.addWidget(bn_edit)

        bn_explore = QtGui.QPushButton("Edit figure")
        bn_explore.clicked.connect(self.on_explore_clicked)
        ctl.addWidget(bn_explore)

        bn_subplot = QtGui.QPushButton("Subplot param")
        bn_subplot.clicked.connect(self.on_subplot_clicked)
        ctl.addWidget(bn_subplot)

        self.entry_x = uiutils.EntryDescription('Width in "', n_chars=12)
        self.entry_x.editingFinished.connect(self.on_xy_changed)
        ctl.addWidget(self.entry_x)

        ctl.addWidget(QtGui.QLabel("x"))

        self.entry_y = uiutils.EntryDescription('Height in "', n_chars=12)
        self.entry_y.editingFinished.connect(self.on_xy_changed)
        ctl.addWidget(self.entry_y)

        bn_save = QtGui.QPushButton('Save figure')
        bn_save.clicked.connect(self.on_save_clicked)
        ctl.addWidget(bn_save)

        # if not isinstance(figure, ReplayableFigure):
        #     bn_edit.setEnabled(False)

        # self.connect("delete-event", self.on_leave)

        self.show()
        self.update(True)

    def on_leave(self, w, event):
        self.figure.canvas = self.current_canvas
        display_preset = presetutils.RcPreset.load("display")
        display_preset.apply(self.figure)

        if isinstance(self.figure, ReplayableFigure):
            self.figure.replay()

        self.figure.subplots_adjust(**self.current_subplotpars)
        self.figure.set_dpi(self.curent_dpi)

        if self.current_canvas is not None:
            self.figure.canvas.queue_resize()
        self.hide()
        return True

    def on_preset_changed(self, combo):
        self.update(True)

    def on_save_clicked(self, changed):
        dest = uiutils.select_file()
        if dest is not None:
            self.figure.patch.set_visible(False)
            self.figure.savefig(dest)
            self.figure.patch.set_visible(True)

    def on_edit_clicked(self, bn):
        preset = self.presets[self.combo_presets.currentIndex()]
        self.editor = PresetEditor(preset)
        self.editor.changed.connect(self.on_editor_changed)
        self.editor.show()

    def on_explore_clicked(self, bn):
        # From matplotlib/backends/backend_qt5.py
        allaxes = self.figure.get_axes()
        if not allaxes:
            QtGui.QMessageBox.warning(
                None, "Error", "There are no axes to edit.")
            return
        if len(allaxes) == 1:
            axes = allaxes[0]
        else:
            titles = []
            for axes in allaxes:
                name = (axes.get_title() or
                        " - ".join(filter(None, [axes.get_xlabel(),
                                                 axes.get_ylabel()])) or
                        "<anonymous {} (id: {:#x})>".format(
                            type(axes).__name__, id(axes)))
                titles.append(name)
            item, ok = QtGui.QInputDialog.getItem(
                None, 'Customize', 'Select axes:', titles, 0, False)
            if ok:
                axes = allaxes[titles.index(item)]
            else:
                return

        figureoptions.figure_edit(axes, self)
        self.update(False)
    
    def on_subplot_clicked(self, bn):
        self.figure.navigation.configure_subplots()

    def on_editor_changed(self):
        self.update()

    def on_xy_changed(self):
        preset = self.presets[self.combo_presets.currentIndex()]
        x = self.entry_x.get_text()
        y = self.entry_y.get_text()
        if nputils.is_str_number(x) and nputils.is_str_number(y):
            preset.set_key("figure.figsize", "%s, %s" % (x, y))
        self.update(True)

    def update(self, replay=True):
        preset = self.presets[self.combo_presets.currentIndex()]
        if preset is not None:
            x, y = preset.get_key("figure.figsize")
            self.entry_x.set_text(str(x))
            self.entry_y.set_text(str(y))

            preset.apply(self.figure)

            if replay and isinstance(self.figure, ReplayableFigure):
                self.figure.replay()
            try:
                self.figure.tight_layout(pad=0.3)
            except Exception, e:
                print "Failed to run tight_layout: %s" % e
            self.figure.canvas.draw_idle()
            self.figure_view.resizeEvent(None)


class FigureStack(uiutils.UI, BaseFigureStack):

    def __init__(self, title="Figure Stack", fixed_aspect_ratio=False, **kwargs):
        BaseFigureStack.__init__(self, title=title, 
                                 fixed_aspect_ratio=fixed_aspect_ratio, **kwargs)
        uiutils.UI.__init__(self, 800, 500, title)
        self.window_title = title

        # self.connect('delete-event', self.on_destroy)

        self.box = QtGui.QVBoxLayout()
        self.setLayout(self.box)

        self.canva_box = QtGui.QStackedWidget()
        # self.canva_box.connect('size-allocate', self.on_canva_box_size_allocated)
        self.box.addWidget(self.canva_box, 1)

        self.ctl = QtGui.QHBoxLayout()
        self.box.addLayout(self.ctl, 0)

        self.figures = []

        self.combobox = QtGui.QComboBox()
        self.combobox.setMinimumSize(150, 30)
        self.combobox.currentIndexChanged.connect(self.on_list_changed)
        self.ctl.addWidget(self.combobox)

        previous = QtGui.QPushButton(' < ')
        previous.clicked.connect(self.on_previous_pressed)
        previous.setMaximumSize(30, 30)
        self.ctl.addWidget(previous)

        next = QtGui.QPushButton(' > ')
        next.clicked.connect(self.on_next_pressed)
        next.setMaximumSize(30, 30)
        self.ctl.addWidget(next)

        save = QtGui.QPushButton('Save')
        save.setMaximumSize(45, 30)
        save.clicked.connect(self.on_save_pressed)
        self.ctl.addWidget(save)

        ext = QtGui.QPushButton('Ext')
        ext.setMaximumSize(45, 30)
        ext.clicked.connect(self.on_ext_clicked)
        self.ctl.addWidget(ext)

        self.navi_box = QtGui.QStackedWidget()
        self.ctl.addWidget(self.navi_box, 2)

        self.tooltip_manager = TooltipManager(self)

    def closeEvent(self, event):
        self.destroy()
        uiutils.UI.closeEvent(self, event)

    def destroy(self):
        self.tooltip_manager.release()
        self.tooltip_manager = None
        BaseFigureStack.destroy(self)
        uiutils.UI.deleteLater(self)

    # def on_canva_box_size_allocated(self, box, allocation):
    #     size = "%s x %s" % (allocation.width, allocation.height)
    #     self.set_title("%s (%s)" % (self.window_title, size))

    def on_next_pressed(self, widget):
        active = self.combobox.currentIndex()
        if active < len(self.figures) - 1:
            self.combobox.setCurrentIndex(active + 1)
        else:
            self.combobox.setCurrentIndex(0)

    def on_previous_pressed(self, widget):
        active = self.combobox.currentIndex()
        if active > 0:
            self.combobox.setCurrentIndex(active - 1)
        else:
            self.combobox.setCurrentIndex(len(self.figures) - 1)

    def on_list_changed(self, widget):
        self.on_figure_changed()

    def on_ext_clicked(self, widget):
        i = self.combobox.currentIndex()
        figure, name = self.figures[i], self.combobox.itemText(i)

        figure.navigation.home()

        self.remove_figure(i)

        self.ext = ExtFigureWindow(figure, name, self, i)
        self.ext.show()

    def on_save_pressed(self, widget):
        f = uiutils.select_file()
        if f is not None:
            self.save_all(f, preset="printer_us_letter")

    def on_figure_changed(self):
        # import resource
        # print "Usage:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        i = self.combobox.currentIndex()
        self.canva_box.setCurrentIndex(i)
        self.navi_box.setCurrentIndex(i)

        self.tooltip_manager.set_current_figure(self.figures[i])

        self.canva_box.update()
        self.ctl.update()

    def add_figure(self, name="None", figure=None, position=None):
        figure = BaseFigureStack.add_figure(self, name=name, figure=figure, position=position)
        if self.fixed_aspect_ratio:
            self.view = FixedAspectRatioFigureView(figure)
        else:
            FigureCanvas(figure)
            self.view = figure.canvas
        figure.navigation = ExtendedNavigationToolbar(figure.canvas, self)

        if position is None:
            position = len(self.figures)

        self.canva_box.insertWidget(position, self.view)
        self.navi_box.insertWidget(position, figure.navigation)
        self.combobox.insertItem(position, str(name))
        self.combobox.setCurrentIndex(position)

        self.add_intensity_tooltip(figure)

        return figure

    def remove_figure(self, i):
        self.figures.pop(i)
        self.combobox.removeItem(i)
        self.canva_box.removeWidget(self.canva_box.widget(i))
        self.navi_box.removeWidget(self.navi_box.widget(i))

        self.combobox.setCurrentIndex(max(i - 1, 0))
        self.on_figure_changed()

    def add_tooltip(self, axes, coord, text, tol=5):
        figure = axes.get_figure()
        figure_tooltip = self.tooltip_manager.get_figure_tooltip(figure)
        if figure_tooltip is None or not isinstance(figure_tooltip, FigureTooltips):
            figure_tooltip = FigureTooltips()
            self.tooltip_manager.add_figure_tooltip(figure, figure_tooltip)
        figure_tooltip.add_tooltip(axes, coord, text, tol)

    def add_intensity_tooltip(self, figure):
        figure_tooltip = self.tooltip_manager.get_figure_tooltip(figure)
        if figure_tooltip is None or not isinstance(figure_tooltip, IntensityFigureTooltip):
            figure_tooltip = IntensityFigureTooltip()
            self.tooltip_manager.add_figure_tooltip(figure, figure_tooltip)

    def show(self, start_main=True):
        self.combobox.setCurrentIndex(0)
        self.on_figure_changed()

        if start_main:
            self.start()
        else:
            QtGui.QWidget.show(self)
