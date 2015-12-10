import gtk
import pango
import gobject

from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

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


class Cursor(gobject.GObject):

    __gsignals__ = {
        'cursor-moved': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (object,))
    }

    def __init__(self, ax, figure, other_axs=[]):
        gobject.GObject.__init__(self)
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

            self.emit("cursor-moved", cursor_positions)
            # update the line positions
            self.lx.set_ydata(y)
            self.ly.set_xdata(x)

            self.draw()

    def draw(self):
        self.canvas.restore_region(self.back)
        self.ax.draw_artist(self.lx)
        self.ax.draw_artist(self.ly)
        self.canvas.blit(self.canvas.figure.bbox)


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
                self.canvas.blit(self.axes.bbox)
            except:
                pass

    def __draw_line(self):
        if self.background is None:
            self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.canvas.restore_region(self.background)
        self.draw_line()
        self.canvas.blit(self.axes.bbox)


class ProfileLine(AbstractTwoPointsRequest):

    def __init__(self, parent, canvas):
        AbstractTwoPointsRequest.__init__(self, canvas)

        self.pos_background = None
        self.path_position = None
        self.line = None

        self.profile_window = ProfileWindow(parent)
        self.profile_window.connect("hide", self.on_profile_window_hide)

    def check_axes(self, axes):
        return axes_has_artist(axes, AxesImage)

    def on_profile_window_hide(self, window):
        self.clear()

    def release(self):
        AbstractTwoPointsRequest.release(self)
        self.profile_window.destroy()

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
                xdata = itr_x(x + 0.5)  # get the middle of the pixel
                ydata = itr_y(y + 0.5)

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
        self.cusor.connect("cursor-moved", self.on_cursor_moved)
        self.profile_window.draw()

        return True

    def on_draw(self, event):
        AbstractTwoPointsRequest.on_draw(self, event)
        self.pos_background = None

    def on_cursor_moved(self, object, positions):
        x = positions[0][0]
        y = positions[1][0]
        self.path_position.set_offsets([y, x])
        self.draw_position()

    def draw_position(self):
        if self.pos_background is None:
            self.pos_background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.canvas.restore_region(self.pos_background)
        self.canvas.figure.draw_artist(self.path_position)
        self.canvas.blit(self.axes.bbox)

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
        self.stats_window.destroy()

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
        uiutils.UI.__init__(self, 300, 200, "Statistics", parent)
        self.canvas = canvas

        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.add(self.notebook)
        self.connect("delete-event", self.on_delete)

    def on_delete(self, widget, event):
        self.hide()
        return True

    def init(self):
        while self.has_data():
            self.notebook.remove_page(0)

    def has_data(self):
        return self.notebook.get_n_pages() > 0

    def add_stat_entry(self, vbox, text, value):
        hbox = gtk.HBox()
        hbox.set_border_width(2)
        vbox.add(hbox)

        label = gtk.Label()
        label.set_markup("<b>%s:</b>" % (text))
        label.set_width_chars(20)
        label.set_alignment(0, 0)
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(gtk.Label(value), False, False, 5)

    def add_data(self, axes, data, title, fct_index2coord):
        vbox = gtk.VBox()
        self.add_stat_entry(vbox, "Dimensions", "%s n=%s" % (str(data.shape), data.size))
        self.add_stat_entry(vbox, "Mean", "%g" % data.mean())
        self.add_stat_entry(vbox, "Median", "%g" % np.median(data))
        self.add_stat_entry(vbox, "Sum", "%g" % data.sum())

        coord_max = fct_index2coord(nputils.coord_max(data))
        self.add_stat_entry(vbox, "Maximum", "%g at %s" % (data.max(), coord_max))

        coord_min = fct_index2coord(nputils.coord_min(data))
        self.add_stat_entry(vbox, "Minimum", "%g at %s" % (data.min(), coord_min))

        self.add_stat_entry(vbox, "Standart deviation", "%g" % data.std())
        self.add_stat_entry(vbox, "P90", "%g" % np.percentile(data, 90))

        coord_com = fct_index2coord(measurements.center_of_mass(data))
        self.add_stat_entry(vbox, "Center of mass", str(np.round(coord_com, decimals=2)))

        self.notebook.append_page(vbox, gtk.Label(title))

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

        self.canvas.blit(axes.bbox)

    def show(self):
        self.show_all()
        self.present()


class BaseFigureWindow(uiutils.UI):

    def __init__(self, figure=None, name="", parent=None, extended_toolbar=True):
        uiutils.UI.__init__(self, 600, 500, name, parent)

        self.box = gtk.VBox(False, 10)
        self.add(self.box)

        self.tooltip_manager = TooltipManager(self)

        if figure is None:
            figure = BaseCustomFigure()

        self.figure = figure

        if isinstance(self.figure.canvas, NotAutoResizeFigureCanva):
            self.view_widget = NotAutoResizeFigureCanva(self.figure)
        else:
            self.view_widget = FigureCanvas(self.figure)
        self.box.pack_start(self.view_widget, True, True)

        if hasattr(self.figure, "navigation") and self.figure.navigation is not None:
            self.navigation = self.figure.navigation
            self.navigation.canvas = self.figure.canvas
        else:
            if extended_toolbar:
                self.navigation = ExtendedNavigationToolbar(figure.canvas, self)
            else:
                self.navigation = NavigationToolbar(figure.canvas, self)

        self.box.pack_start(self.navigation, False, False)

        self.connect("delete-event", self.on_destroy)

    def on_destroy(self, event, window):
        self.figure.clf()
        self.tooltip_manager.destroy()
        return False

    def show(self):
        self.start()


class ExtFigureWindow(BaseFigureWindow):

    def __init__(self, figure, name, figure_stack, pos):
        BaseFigureWindow.__init__(self, figure, name, figure_stack)

        self.figure_stack = figure_stack
        self.pos = pos
        self.connect("destroy", self.on_destroy)

    def on_destroy(self, window):
        self.box.remove(self.view_widget)
        self.box.remove(self.navigation)
        self.figure.canvas = None
        self.figure_stack.add_figure(self.get_title(), self.figure, position=self.pos)


class ProfileWindow(BaseFigureWindow):

    def __init__(self, parent=None):
        BaseFigureWindow.__init__(self, None, "Profile", parent, extended_toolbar=False)
        self.connect("delete-event", self.on_delete)

    def on_delete(self, widget, event):
        self.hide()
        return True

    def get_figure(self):
        return self.figure

    def get_axes(self):
        figure = self.get_figure()
        figure.clear()
        ax = figure.subplots()
        return ax

    def draw(self):
        self.figure.canvas.draw()
        self.show_all()
        self.present()


class Tooltip(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLTIP)
        self.set_name("gtk-tooltip")
        thickness = 5

        alignement = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignement.set_padding(thickness, thickness, thickness, thickness)
        self.add(alignement)

        box = gtk.VBox(False, spacing=thickness)
        alignement.add(box)

        self.label = gtk.Label("")
        box.pack_start(self.label, False, False, 0)
        self.label.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(46, 52, 54))

        self.connect("expose-event", self.expose_event)

    def expose_event(self, widget, event):
        w, h = self.get_size()
        self.get_style().paint_flat_box(
            self.get_window(), gtk.STATE_NORMAL,
            gtk.SHADOW_OUT, None, self,
            "tooltip", 0, 0, w, h)

    def show(self, parent, x, y, text):
        posx, posy = parent.get_position()
        sizex, sizey = parent.get_size()
        self.move(x + posx + 20, (sizey - y) + posy - 10)
        self.label.set_markup(text)
        self.show_all()


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


class Timeout(object):

    def __init__(self, timeout, callback):
        self.callback = callback
        self.timeout = timeout
        self.id = None
        self.user_callback = callback

    def _callback(self, *args):
        self.id = None
        self.user_callback(*args)

    def activate(self, *args):
        if self.id is None:
            self.id = gobject.timeout_add(self.timeout, self._callback, *args)
            # print "Add:", self.id

    def reset(self):
        if self.id is not None:
            gobject.source_remove(self.id)
            # print "Del:", self.id
            self.id = None


class TooltipManager:

    def __init__(self, window):
        self.tooltip = Tooltip()
        self.tooltips = dict()
        self.current_figure = None
        self.current_text = None
        self.show_timeout = Timeout(400, self.show_tooltip)
        window.connect("leave-notify-event", self.on_window_focus_out)
        self.cid_motion = None
        # window.connect("delete-event", self.on_window_delete)

    def set_current_figure(self, figure):
        self.current_figure = figure
        if figure in self.tooltips:
            self.cid_motion = figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def get_figure_tooltip(self, figure):
        return self.tooltips.get(figure)

    def add_figure_tooltip(self, figure, figure_tooltip):
        self.tooltips[figure] = figure_tooltip

    def show_tooltip(self, event, text):
        self.source_show_timeout = None
        parent = self.current_figure.canvas.get_toplevel()
        self.tooltip.show(parent, event.x, event.y, text)

    def on_motion(self, event):
        if event.inaxes:
            tooltips = self.tooltips[self.current_figure]
            text = tooltips.get_tooltip(event.inaxes, np.array([event.ydata, event.xdata]))
            if text is None or text == "":
                self.show_timeout.reset()
            elif text != self.current_text:
                self.tooltip.hide()
                self.show_timeout.reset()
                self.show_timeout.activate(event, text)

            self.current_text = text
        else:
            self.show_timeout.reset()
            self.tooltip.hide()

    def on_window_focus_out(self, widget, event):
        self.show_timeout.reset()
        self.tooltip.hide()

    def destroy(self):
        if self.cid_motion is not None and self.current_figure.canvas is not None:
            self.current_figure.canvas.mpl_disconnect(self.cid_motion)
        self.show_timeout.reset()
        self.tooltip.destroy()


class ExtendedNavigationToolbar(NavigationToolbar):

    def __init__(self, canvas, window, profile=True):
        NavigationToolbar.__init__(self, canvas, window)

        for button in self:
            if isinstance(button, gtk.ToolButton):
                button.connect('clicked', self.on_navigation_toolbar_clicked)

        self.connect("hide", self.on_hide)
        window.connect("delete-event", self.on_window_delete)

        icon = gtk.Image()
        icon.set_from_file(os.path.join(imgutils.RESSOURCE_PATH, "profile.png"))

        self.profile_bn = gtk.ToggleToolButton()
        self.profile_bn.set_label("Profile")
        self.profile_bn.set_icon_widget(icon)
        self.insert(self.profile_bn, 5)
        self.profile_bn.connect('toggled', self.on_profile_toggled)

        icon = gtk.Image()
        icon.set_from_file(os.path.join(imgutils.RESSOURCE_PATH, "stats.png"))

        self.stats_bn = gtk.ToggleToolButton()
        self.stats_bn.set_label("Stat")
        self.stats_bn.set_icon_widget(icon)
        self.insert(self.stats_bn, 6)
        self.stats_bn.connect('toggled', self.on_stats_toggled)

        self.explore_bn = gtk.ToolButton(gtk.STOCK_EDIT)
        self.insert(self.explore_bn, 7)
        self.explore_bn.connect('clicked', self.on_explore_clicked)


    def on_window_delete(self, window, event):
        self.destroy()
        return False

    def destroy(self):
        self.win = None
        self.canvas = None

    def on_navigation_toolbar_clicked(self, bn):
        if bn.get_label() in ["Pan", "Zoom"]:
            self.profile_bn.set_active(False)
            self.stats_bn.set_active(False)

    def on_profile_toggled(self, widget):
        if widget.get_active():
            self.toogle_off_all_active(widget)
            self.profile_line = ProfileLine(self.win, self.canvas)
        else:
            self.profile_line.release()

    def on_stats_toggled(self, widget):
        if widget.get_active():
            self.toogle_off_all_active(widget)
            self.image_stats = PlotImageStats(self.win, self.canvas)
        else:
            self.image_stats.release()

    def on_explore_clicked(self, widget):
        explorer = FigureExplorer(self.canvas.figure, self.win)
        explorer.show_all()

    def on_hide(self, widget):
        self.profile_bn.set_active(False)
        self.stats_bn.set_active(False)

    def set_canvas(self, canvas):
        self.canvas = canvas

    def toogle_off_all_active(self, excep):
        if self._active == 'ZOOM':
            self.zoom()
        elif self._active == 'PAN':
            self.pan()
        if excep != self.stats_bn and self.stats_bn.get_active():
            self.stats_bn.set_active(False)
        if excep != self.profile_bn and self.profile_bn.get_active():
            self.profile_bn.set_active(False)

    def save_figure(self, *args):
        self.canvas.figure.navigation = self
        sf = SaveFigure(self.canvas.figure, parent=self.win)


class BaseCustomCanvas(FigureCanvas):

    def __init__(self, figure=None):
        if figure is None:
            figure = BaseCustomFigure(dpi=90, frameon=True)
        self.figure = figure
        FigureCanvas.__init__(self, figure)


class NotAutoResizeFigureCanva(BaseCustomCanvas):

    def configure_event(self, widget, event=None):
        self.queue_draw()


class FixedAspectRatioFigureView(gtk.ScrolledWindow):

    def __init__(self, figure, auto_dpi=True, auto_dpi_height=True):
        gtk.ScrolledWindow.__init__(self)
        self.figure = figure
        self.auto_dpi = auto_dpi
        self.auto_dpi_height = auto_dpi_height

        self.layout = gtk.Layout()

        self.add(self.layout)
        self.figure = figure
        NotAutoResizeFigureCanva(self.figure)
        self.layout.put(self.figure.canvas, 0, 0)

        self.layout.connect('size-allocate', self.cb_size_allocate)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.delayed_resize = Timeout(200, self.do_canvas_resize)

    def cb_size_allocate(self, w, rect):
        self.delayed_resize.reset()
        self.delayed_resize.activate(rect)

    def do_canvas_resize(self, rect):
        winch, hinch = self.figure.get_size_inches()

        if self.auto_dpi:
            w, h = (rect.width, rect.height)
            if self.auto_dpi_height:
                dpi = h / hinch
            else:
                dpi = w / winch
            self.figure.set_dpi(dpi)
        else:
            dpi = self.figure.get_dpi()

        w = int(winch * dpi)
        h = int(hinch * dpi)

        self.layout.set_size(w, h)
        self.figure.canvas.set_size_request(w, h)

        self.figure.canvas._need_redraw = True

class RcPresetTreeModel(gtk.TreeStore):

    def __init__(self, preset):
        self.preset = preset
        gtk.TreeStore.__init__(self, str, str, str, int)

        parents_iter = []
        for group in preset.get_groups():
            group_row = self.append(None, [group, '', '', pango.WEIGHT_NORMAL])
            parents_iter.append(group_row)
            for setting, value in preset.get_settings(group):
                iter = self.append(group_row, [group, setting, value, pango.WEIGHT_NORMAL])
                self.set_weight(iter)

        for parent in parents_iter:
            self.set_parent_weight(parent)

    def set_weight(self, iter):
        group, setting = self.get(iter, 0, 1)
        if self.preset.is_preset(group, setting):
            weight = pango.WEIGHT_BOLD
        else:
            weight = pango.WEIGHT_NORMAL
        self.set(iter, 3, weight)

    def set_parent_weight(self, parent):
        current_iter = self.iter_children(parent)
        get_pp = lambda iter: self.get_path(self.iter_parent(iter))
        while current_iter is not None and get_pp(current_iter) == self.get_path(parent):
            if self.get(current_iter, 3)[0] == pango.WEIGHT_BOLD:
                self.set(parent, 3, pango.WEIGHT_BOLD)
                break
            current_iter = self.iter_next(current_iter)

    def set_value(self, iter, value):
        if value == self.get(iter, 2)[0]:
            return

        group, setting = self.get(iter, 0, 1)
        if value == "":
            self.preset.set_default(group, setting)
        else:
            self.preset.set(group, setting, value)
        self.set(iter, 2, self.preset.get(group, setting))
        self.set_weight(iter)
        self.set_parent_weight(self.iter_parent(iter))

    def get_value(self, iter):
        return self.get(iter, 2)[0]

    def get_key(self, iter):
        return self.get(iter, 0, 1)

    def is_setting(self, iter):
        return iter is not None and len(self.get(iter, 1)[0]) > 0


class PresetEditor(uiutils.UI):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    def __init__(self, preset, parent):
        title = "Preset Editor: %s" % preset.get_name()
        uiutils.UI.__init__(self, 400, 400, title, parent=parent)

        self.preset = preset
        self.model = RcPresetTreeModel(preset)

        col_group = gtk.TreeViewColumn('Group', gtk.CellRendererText(), text=0, weight=3)
        col_setting = gtk.TreeViewColumn('Setting', gtk.CellRendererText(), text=1, weight=3)

        renderer_value = gtk.CellRendererText()
        renderer_value.set_property("editable", True)
        renderer_value.connect("edited", self.on_value_edit)
        col_value = gtk.TreeViewColumn('Value', renderer_value, text=2, weight=3)

        vbox = gtk.VBox(spacing=5)
        self.add(vbox)

        scrollview = gtk.ScrolledWindow()
        scrollview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollview.set_shadow_type(gtk.SHADOW_IN)
        vbox.add(scrollview)

        self.model_filter = self.model.filter_new()

        self.treeview = gtk.TreeView(self.model_filter)
        self.treeview.append_column(col_group)
        self.treeview.append_column(col_setting)
        self.treeview.append_column(col_value)
        self.treeview.connect("row-activated", self.on_row_activated)

        self.treeselection = self.treeview.get_selection()
        self.treeselection.connect("changed", self.on_treeselection_changed)

        scrollview.add(self.treeview)

        ctl = gtk.HBox(spacing=5)
        vbox.pack_start(ctl, False, True)

        self.set_default_bn = gtk.Button("Set to default")
        self.set_default_bn.connect("clicked", self.on_set_default_clicked)
        ctl.pack_start(self.set_default_bn, False, True)

        self.save_bn = gtk.Button("Save")
        self.save_bn.connect("clicked", self.on_save_clicked)
        self.save_bn.set_sensitive(False)
        ctl.pack_end(self.save_bn, False, True)

        self.filter_entry = uiutils.EntryDescription("Filter")
        self.filter_entry.connect("changed", self.on_filter_changed)
        self.filter_entry.connect("key-press-event", self.on_filter_key_press_event)

        ctl.pack_end(self.filter_entry, False, True)

        self.model_filter.set_visible_func(self.match_func)

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
            self.save_bn.set_sensitive(False)

    def on_filter_changed(self, entry):
        self.model_filter.refilter()
        if self.filter_entry.get_text() == "":
            self.treeview.collapse_all()
        else:
            self.treeview.expand_all()

    def on_filter_key_press_event(self, entry, event):
        if event.keyval == gtk.keysyms.Escape:
            entry.set_text("")

    def on_treeselection_changed(self, treeselection):
        model, iter_filter = treeselection.get_selected()
        if iter_filter is not None:
            iter = model.convert_iter_to_child_iter(iter_filter)
            self.set_default_bn.set_sensitive(self.model.is_setting(iter))

    def on_row_activated(self, treeview, path, col):
        if not treeview.row_expanded(path):
            treeview.expand_to_path(path)
        else:
            treeview.collapse_row(path)

    def on_set_default_clicked(self, bn):
        model, iter_filter = self.treeselection.get_selected()
        if iter_filter is not None:
            iter = model.convert_iter_to_child_iter(iter_filter)
            self.model.set_value(iter, "")
            self.save_bn.set_sensitive(True)
            self.emit('changed')

    def on_value_edit(self, renderer, path, value):
        iter_filter = self.model_filter.get_iter(path)
        iter = self.model_filter.convert_iter_to_child_iter(iter_filter)
        current_value = self.model.get_value(iter)
        if current_value != value:
            self.model.set_value(iter, value)
            self.save_bn.set_sensitive(True)
            self.emit('changed')


class ArtistList(object):

    def __init__(self, artists):
        self.artists = artists

    def get_keys(self):
        sets = [set(artist.properties().keys()) for artist in self.artists]
        return set.intersection(*sets)

    def is_settable(self, key):
        return all([hasattr(a, "set_%s" % key) for a in self.artists])

    def get_value(self, key):
        value = None
        for artist in self.artists:
            new_value = getattr(artist, "get_%s" % key)()
            # print self.artists, artist, key, value, new_value
            if value is not None and str(value) != str(new_value):
                return "(Multiple values)"
            value = new_value
        return value

    def get_pp_value(self, value):
        if isinstance(value, np.ndarray):
            value = PrettyPrintNdArray(value)
        return str(value)

    def set_value(self, key, value):
        for artist in self.artists:
            getattr(artist, "set_%s" % key)(value)

    def properties(self):
        for key in self.get_keys():
            yield key, self.get_value(key)

    def doc(self, key):
        docs = set()
        for artist in self.artists:
            getter = getattr(artist, "get_%s" % key)
            docs.add(nputils.safe_strip(getter.__doc__))
        if len(docs) == 1:
            return docs.pop()
        return "(Multiple values)"

    def get_valid_values(self, key):
        valids = set()
        for artist in self.artists:
            valids.add(nputils.safe_strip(ArtistInspector(artist).get_valid_values(key)))
        if len(valids) == 1:
            return valids.pop()
        return "(Multiple values)"

    def get_aliases(self):
        artist = self.artists[0]
        aliases = []
        inspector = ArtistInspector(artist)
        for key in self.get_keys():
            try:
                fct = getattr(artist, "set_%s" % key)
            except AttributeError:
                fct = getattr(artist, "get_%s" % key)
            if inspector.is_alias(fct):
                aliases.append(key)
        return set(aliases)

    def valid_value_is_class(self, key):
        return ":class:" in self.get_valid_values(key) or ":class:" in self.doc(key)


class PrettyPrintNdArray(object):

    def __init__(self, array):
        self.array = array

    def __str__(self):
        return "[" + ", ".join([str(k) for k in self.array]) + "]"


class ArtistTreeModel(gtk.ListStore):

    key_blacklist = ["agg_filter", "animated", "axes", "clip_on", "contains", "gid",
                     "picker", "rasterized", "url", "axes_locator", "position",
                     "subplotspec", "data", "xdata", "ydata", "bbox_to_anchor",
                     "default_handler_map", ]

    def __init__(self, filter=True):
        gtk.ListStore.__init__(self, str, str)
        self.artist = None
        self.filter = filter

    def set_artist(self, artist):
        self.artist = artist
        self.reload()

    def reload(self):
        if self.artist is None:
            return

        self.clear()
        aliases = self.artist.get_aliases()

        for key, value in self.artist.properties():
            if self.filter:
                if not self.artist.is_settable(key) or key in self.key_blacklist \
                        or key in aliases or self.artist.valid_value_is_class(key):
                    continue
            self.append([key, self.artist.get_pp_value(value)])

    def get_artist(self):
        return self.artist


class FigureExplorer(uiutils.UI):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    def __init__(self, figure, parent):
        uiutils.UI.__init__(self, 700, 400, "Figure explorer", parent=parent)
        self.figure = figure

        hpane = gtk.HPaned()
        self.add(hpane)

        scrollview = gtk.ScrolledWindow()
        scrollview.set_size_request(250, 400)
        scrollview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollview.set_shadow_type(gtk.SHADOW_OUT)
        hpane.pack1(scrollview, False, False)

        self.figure_model = gtk.TreeStore(object, str)

        def recursive_append(artist, parent_iter):
            if hasattr(artist, "get_children"):
                for child_artist in artist.get_children():
                    child_iter = self.figure_model.append(parent_iter, [child_artist, str(child_artist)])
                    recursive_append(child_artist, child_iter)

        recursive_append(figure, None)

        figure_treeview = gtk.TreeView(self.figure_model)
        figure_treeview.get_selection().connect("changed", self.on_artist_changed)

        col_artist = gtk.TreeViewColumn('Artist', gtk.CellRendererText(), text=1)
        figure_treeview.append_column(col_artist)
        figure_treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        figure_treeview.connect("row-activated", self.on_artist_activated)

        scrollview.add(figure_treeview)

        artist_vbox = gtk.VBox()
        hpane.pack2(artist_vbox, True, True)

        self.artist_model = ArtistTreeModel()
        self.artist_treeview = gtk.TreeView(self.artist_model)
        self.artist_treeview.connect("cursor_changed", self.on_prop_changed)

        col_key = gtk.TreeViewColumn('Key', gtk.CellRendererText(), text=0)
        col_key.set_sort_column_id(0)
        col_key.set_resizable(True)
        self.artist_model.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.artist_treeview.append_column(col_key)

        renderer_value = gtk.CellRendererText()
        renderer_value.set_property("editable", True)
        renderer_value.connect("edited", self.on_prop_value_edit)
        col_value = gtk.TreeViewColumn('Value', renderer_value, text=1)
        self.artist_treeview.append_column(col_value)

        scrollview = gtk.ScrolledWindow()
        scrollview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollview.set_shadow_type(gtk.SHADOW_IN)
        scrollview.add(self.artist_treeview)

        artist_vbox.pack_start(scrollview)

        self.prop_label = gtk.Label("")
        self.prop_label.set_padding(5, 5)
        self.prop_label.set_alignment(0, 0)
        self.prop_label.set_line_wrap(True)
        artist_vbox.pack_start(self.prop_label, False, False)

        artist_vbox.pack_start(gtk.HSeparator(), False, False)

        hbox = gtk.HBox()
        hbox.set_border_width(5)
        artist_vbox.pack_start(hbox, False, False)

        checkbox = gtk.CheckButton("Filter non settable properties")
        checkbox.connect("toggled", self.on_checkbox_toggle)
        checkbox.set_active(self.artist_model.filter)
        hbox.pack_start(checkbox, False, True, 0)

    def on_artist_changed(self, selection):
        model, pathlist = selection.get_selected_rows()
        artistlist = [model.get_value(model.get_iter(path), 0) for path in pathlist]
        if len(artistlist) > 0:
            artists = ArtistList(artistlist)
            self.artist_model.set_artist(artists)

    def on_artist_activated(self, treeview, path, col):
        if not treeview.row_expanded(path):
            treeview.expand_to_path(path)
        else:
            treeview.collapse_row(path)

    def on_checkbox_toggle(self, bn):
        self.artist_model.filter = bn.get_active()
        self.artist_model.reload()

    def on_prop_changed(self, treeview):
        artists = self.artist_model.get_artist()

        path = treeview.get_cursor()[0]
        iter = self.artist_model.get_iter(path)
        key = self.artist_model.get_value(iter, 0)

        esc = lambda s: gobject.markup_escape_text(s)

        label = "<b>Documentation:</b> %s\n" % esc(artists.doc(key))
        label += "\n"
        label += "<b>Valid values:</b> %s" % esc(artists.get_valid_values(key))

        self.prop_label.set_markup(label)

    def on_prop_value_edit(self, renderer, path, value):
        iter = self.artist_model.get_iter(path)
        key = self.artist_model.get_value(iter, 0)
        artists = self.artist_model.get_artist()

        try:
            try:
                v = ast.literal_eval(value)
            except Exception:
                v = value
            artists.set_value(key, v)
            new_value = artists.get_pp_value(artists.get_value(key))
            self.artist_model.set_value(iter, 1, new_value)
            self.figure.canvas._need_redraw = True
            self.figure.canvas.queue_resize()
            self.emit('changed')
        except Exception, e:
            print "edit error:", e


class SaveFigure(uiutils.UI):

    def __init__(self, figure, auto_dpi=True, parent=None):
        uiutils.UI.__init__(self, 700, 500, "Save plot", parent=parent)
        self.figure = figure

        vbox = gtk.VBox(spacing=10)
        self.add(vbox)

        self.current_canvas = self.figure.canvas
        sp_keys = ["left", "right", "top", "bottom", "wspace", "hspace"]
        self.current_subplotpars = dict([(key, getattr(self.figure.subplotpars, "%s" % key)) for key in sp_keys])
        self.curent_dpi = self.figure.get_dpi()

        figure_view = FixedAspectRatioFigureView(self.figure, auto_dpi=auto_dpi)
        vbox.add(figure_view)

        ctl = gtk.HBox(homogeneous=False, spacing=10)
        vbox.pack_start(ctl, False, True)

        self.combo_presets = uiutils.ObjectComboBox(presetutils.get_all_presets())
        self.combo_presets.connect("changed", self.on_preset_changed)
        ctl.pack_start(self.combo_presets, False, True)

        bn_edit = gtk.Button('Edit preset')
        bn_edit.connect("clicked", self.on_edit_clicked)
        ctl.pack_start(bn_edit, False, True)

        bn_explore = gtk.Button("Explore figure")
        bn_explore.connect("clicked", self.on_explore_clicked)
        ctl.pack_start(bn_explore, False, True)

        bn_subplot = gtk.Button("Subplot param")
        bn_subplot.connect("clicked", self.on_subplot_clicked)
        ctl.pack_start(bn_subplot, False, True)

        self.entry_x = uiutils.EntryDescription('Width in "', n_chars=12)
        self.entry_x.connect("activate", self.on_xy_changed)
        ctl.pack_start(self.entry_x, False, False)

        label_xy = gtk.Label("x")
        ctl.pack_start(label_xy, False, False)

        self.entry_y = uiutils.EntryDescription('Height in "', n_chars=12)
        self.entry_y.connect("activate", self.on_xy_changed)
        ctl.pack_start(self.entry_y, False, False)

        bn_save = gtk.Button('Save figure')
        bn_save.connect("clicked", self.on_save_clicked)
        ctl.pack_end(bn_save, False, True)

        if not isinstance(figure, ReplayableFigure):
            bn_edit.set_sensitive(False)

        self.connect("delete-event", self.on_leave)

        self.show_all()
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
        preset = self.combo_presets.get_current()
        editor = PresetEditor(preset, self)
        editor.connect("changed", self.on_editor_changed)
        editor.show_all()

    def on_explore_clicked(self, bn):
        explorer = FigureExplorer(self.figure, self)
        explorer.connect("changed", self.on_explorer_changed)
        explorer.show_all()

    def on_subplot_clicked(self, bn):
        self.figure.navigation.configure_subplots(bn)

    def on_editor_changed(self, widget):
        self.update()

    def on_explorer_changed(self, widget):
        self.update(False)

    def on_xy_changed(self, entry):
        preset = self.combo_presets.get_current()
        x = self.entry_x.get_text()
        y = self.entry_y.get_text()
        if nputils.is_str_number(x) and nputils.is_str_number(y):
            preset.set_key("figure.figsize", "%s, %s" % (x, y))
        self.update(True)

    def update(self, replay=True):
        preset = self.combo_presets.get_current()
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
            self.figure.canvas.queue_resize()


class FigureStack(uiutils.UI, BaseFigureStack):

    def __init__(self, title="Figure Stack", fixed_aspect_ratio=False, **kwargs):
        BaseFigureStack.__init__(self, title=title, 
                                 fixed_aspect_ratio=fixed_aspect_ratio, **kwargs)
        uiutils.UI.__init__(self, 750, 600, title)
        self.canvas_klass = FigureCanvas
        self.window_title = title

        self.connect('delete-event', self.on_destroy)

        self.box = gtk.VBox(False, 10)
        self.add(self.box)

        self.figure = None
        self.canvas = None
        self.navigation = None
        self.profile_line = None
        self.view_widget = None

        self.canva_box = gtk.HBox()
        self.canva_box.connect('size-allocate', self.on_canva_box_size_allocated)
        self.box.pack_start(self.canva_box, True, True)

        self.ctl = gtk.HBox(False, 10)
        self.box.pack_start(self.ctl, False, False)

        self.figures = gtk.ListStore(gobject.TYPE_PYOBJECT, str)

        self.combobox = gtk.ComboBox(self.figures)
        cell = gtk.CellRendererText()
        self.combobox.pack_start(cell, True)
        self.combobox.add_attribute(cell, 'text', 1)
        self.combobox.connect("changed", self.on_list_changed)
        self.ctl.pack_start(self.combobox, False, False)

        previous = gtk.Button(' < ')
        previous.connect("clicked", self.on_previous_pressed)
        self.ctl.pack_start(previous, False, False)

        next = gtk.Button(' > ')
        next.connect("clicked", self.on_next_pressed)
        self.ctl.pack_start(next, False, False)

        save = gtk.Button('Save')
        save.connect("clicked", self.on_save_pressed)
        self.ctl.pack_start(save, False, False)

        ext = gtk.Button('Ext')
        ext.connect("clicked", self.on_ext_clicked)
        self.ctl.pack_start(ext, False, False)

        self.tooltip_manager = TooltipManager(self)

    def on_destroy(self, event, window):
        self.tooltip_manager.destroy()
        self.tooltip_manager = None
        self.destroy()
        if self.view_widget is not None:
            self.view_widget = None
        if self.navigation is not None:
            self.navigation.destroy()
            self.navigation = None
        return False

    def on_canva_box_size_allocated(self, box, allocation):
        size = "%s x %s" % (allocation.width, allocation.height)
        self.set_title("%s (%s)" % (self.window_title, size))

    def on_next_pressed(self, widget):
        active = self.combobox.get_active()
        if active < len(self.figures) - 1:
            self.combobox.set_active(active + 1)
        else:
            self.combobox.set_active(0)

    def on_previous_pressed(self, widget):
        active = self.combobox.get_active()
        if active > 0:
            self.combobox.set_active(active - 1)
        else:
            self.combobox.set_active(len(self.figures) - 1)

    def on_stats_toggled(self, widget):
        if self.stats.get_active():
            self.navigation.toogle_off_all_active()
            self.profile_line.start()
        else:
            if self.profile_line is not None:
                self.profile_line.release()
            self.profile_line = None

    def on_list_changed(self, widget):
        self.on_figure_changed()

    def on_ext_clicked(self, widget):
        i = self.combobox.get_active()
        figure, name = self.figures[i][0], self.figures[i][1]

        self.figures.remove(self.figures.get_iter(i))

        self.combobox.set_active(max(i - 1, 0))
        self.on_figure_changed()

        ext = ExtFigureWindow(figure, name, self, i)
        ext.show_all()

    def select_file(self):
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()
        dest = None
        if response == gtk.RESPONSE_OK:
            dest = dialog.get_filename()
        dialog.destroy()
        return dest

    def on_save_pressed(self, widget):
        f = self.select_file()
        if f is not None:
            self.save_all(f, preset="printer_us_letter")

    def on_figure_changed(self):
        # import resource
        # print "Usage:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.ctl.set_sensitive(True)

        if self.view_widget is not None and self.view_widget in self.canva_box:
            self.canva_box.remove(self.view_widget)
        if self.navigation is not None:
            self.navigation.hide()
            self.ctl.remove(self.navigation)

        i = self.combobox.get_active()

        if i >= 0:
            self.figure = self.figures[i][0]
            if self.figure.canvas is None:
                if self.fixed_aspect_ratio:
                    self.figure.view_widget = FixedAspectRatioFigureView(self.figure)
                else:
                    self.figure.view_widget = FigureCanvas(self.figure)
            if not hasattr(self.figure, "navigation") or self.figure.navigation is None:
                self.figure.navigation = ExtendedNavigationToolbar(self.figure.canvas, self)
            self.figure.navigation.canvas = self.figure.canvas
            self.canva_box.pack_start(self.figure.view_widget, True, True)
            self.view_widget = self.figure.view_widget
            self.navigation = self.figure.navigation
        else:
            self.figure = None

        if len(self.figures) == 0:
            self.ctl.set_sensitive(False)

        self.tooltip_manager.set_current_figure(self.figure)

        if self.navigation is not None:
            self.ctl.pack_start(self.navigation, True, True)

        self.show_all()

    def add_figure(self, name="None", figure=None, position=None):
        figure = BaseFigureStack.add_figure(self, name=name, figure=figure, position=position)
        if position is not None:
            self.combobox.set_active(position)
        self.add_intensity_tooltip(figure)
        return figure

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
        self.combobox.set_active(0)
        self.on_figure_changed()

        if start_main:
            gtk.main()
