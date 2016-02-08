import os
import ast
import shutil
import random
import tempfile
import datetime
import numpy as np
from scipy.ndimage import measurements

import matplotlib
import matplotlib.animation as animation
import matplotlib.cm as cm
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import matplotlib.colors as mcolors

from matplotlib.text import Text
from matplotlib.lines import Line2D
from matplotlib.image import AxesImage
from matplotlib.artist import ArtistInspector
from matplotlib.colors import LogNorm, Normalize
from matplotlib.figure import Figure, SubplotParams
from matplotlib.patches import PathPatch, Rectangle, Shadow
from matplotlib.ticker import ScalarFormatter

from matplotlib.backends.backend_pdf import PdfPages

from mpl_toolkits.axisartist import Subplot
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredEllipse
from mpl_toolkits.axisartist.grid_helper_curvelinear import GridHelperCurveLinear
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

import imgutils
import nputils
import presetutils


presetutils.set_rc_preset("display")

color_cycle = ['#3465a4', '#4e9a06', '#cc0000', '#F57900', '#75507b', '#EDD400', '#555753']
blue, green, red, orange, magenta, yellow, black = color_cycle

color_cycle_light = ['#729FCF', '#8AE234', '#EF2929', '#FCAF3E', '#AD7FA8', '#FCE94F', '#888A85']
lblue, lgreen, lred, lorange, lmagenta, lyellow, lblack = color_cycle_light

color_cycle_dark = ['#204A87', '#4E9A06', '#A40000', '#CE5C00', '#5C3566', '#C4A000', '#2E3436']
dblue, dgreen, dred, dorange, dmagenta, dyellow, dblack = color_cycle_dark

matplotlib.rcParams["axes.color_cycle"] = color_cycle + color_cycle_light + color_cycle_dark

all_markers = {'o': 'circle', 'D': 'diamond', 's': 'square', '*': 'star', 'h': 'hexagon1', 
           '^': 'triangle_up', 'p': 'pentagon', 0: 'tickleft', 1: 'tickright', 2: 'tickup', 3: 'tickdown',
           4: 'caretleft', 6: 'caretup', 7: 'caretdown',
           '|': 'vline', '': 'nothing', 'None': 'nothing',
           'x': 'x', 5: 'caretright', '_': 'hline',
           None: 'nothing', 'd': 'thin_diamond', ' ': 'nothing',
           '+': 'plus', ',': 'pixel',
           '.': 'point', '1': 'tri_down',
           '3': 'tri_left', '2': 'tri_up', '4': 'tri_right',
           'H': 'hexagon2', 'v': 'triangle_down', '8': 'octagon',
           '<': 'triangle_left', '>': 'triangle_right'}

best_map_markers = ['o', 'D', 's', '*', 'h', '^', 'p']

white = "#FFFFFF"

black_cmap = mcolors.ListedColormap([black])


def hash_fill_between(ax, x, y1, y2=0, **kargs):
    ''' For x, hash region between y1 and y2. Equivalent of ax.fill_between '''
    p = ax.fill_between(x, y1, y2, **kargs)
    p.set_facecolors("none")
    p.set_edgecolors("none")

    for path in p.get_paths():
        p1 = PathPatch(path, fc="none", hatch="//", alpha=1)
        ax.add_patch(p1)
        p1.set_zorder(p.get_zorder() - 0.1)


def axes_has_artist(axes, klass):
    ''' check if axes contain artist of type klass '''
    for child in axes.get_children():
        if isinstance(child, klass):
            return True
    return False


def twin_yaxis(ax, fct, fmt="%.3f"):
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.grid(False)
    ticks = ax.get_yticks()
    ax2.set_yticks(ticks)
    ax2.set_yticklabels([fmt % k for k in fct(ticks)])
    ax2.set_ylim(ax.get_ylim())
    return ax2


def twin_xaxis(ax, fct, fmt="%.3f"):
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.grid(False)
    ticks = ax.get_xticks()
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([fmt % k for k in fct(ticks)])
    ax2.set_xlim(ax.get_xlim())
    return ax2


def get_cmap(map, bad_color=white, bad_alpha=1):
    ''' bad color: color used for mask values'''
    if isinstance(map, cm.colors.Colormap):
        return map
    cmap = cm.get_cmap(map)
    cmap.set_bad(color=bad_color, alpha=bad_alpha)
    return cmap


def set_grid_helper(axes, grid_helper):
    if not hasattr(axes, "_grid_helper") or type(axes._grid_helper) != type(grid_helper):
        axes._grid_helper = grid_helper
        if grid_helper is not None:
            axes.cla()

def update_grid_helper(axes, **kw):
    axes._grid_helper.grid_finder.update(**kw)


def img_axis(ax):
    ax.axhline(0, ls='-', c='k', lw=2)
    ax.axvline(0, ls='-', c='k', lw=2)
    ax.grid(True)


def get_projection(img, projection):
    if projection is None:
        projection = img.get_projection()

    return projection


def add_beam(ax, image, loc=3, pad=0.2, borderpad=0.2, frameon=True):
    ''' image is an imgutils.Image object.
        It will check if image has a beam and add it to ax as a parasite ax'''
    beam = image.get_beam()
    if beam is not None and isinstance(beam, imgutils.GaussianBeam):
        ae = AnchoredEllipse(ax.transData, width=beam.bmin, height=beam.bmaj, angle=np.degrees(beam.bpa),
                             loc=loc, pad=pad, borderpad=borderpad, frameon=frameon)
        ae.ellipse.set_facecolor(orange)
        ae.ellipse.set_edgecolor(black)
        ae.ellipse.set_alpha(0.8)
        ax.add_artist(ae)


def plot_region(ax, region, projection=None, text=False, color=None, fill=False, **kargs):
    region = region.get_pyregion(projection.get_coordinate_system())
    patch_list, artist_list = region.get_mpl_patches_texts(origin=0, text_offset=0)
    for p in patch_list:
        if color is None:
            color = p.get_ec()
        p.set_ec(color)
        ax.add_patch(p)
        if fill:
            p_face = Shadow(p, 0, 0, props={'color': color, 'alpha': 0.2})
            ax.add_patch(p_face)
    if text:
        for t in artist_list:
            if color is not None:
                t.set_color(color)
            ax.add_artist(t)


def imshow_image(ax, img, projection=None, beam=True, title=True, contour=False,
                 intensity_colorbar=False, **kargs):
    ''' show an imgutils.Image '''
    projection = get_projection(img, projection)
    set_grid_helper(ax, projection.get_gh())

    checkargs(kargs, "norm", LogNorm())
    if contour:
        intensity_colorbar = False
        ax.contour(img.data, **kargs)
        ax.set_aspect('equal')
    else:
        im_mappable = ax.imshow(img.data, **kargs)
    ax.set_autoscale_on(False)

    if title:
        ax.set_title(img.get_title())
    ax.set_xlabel(projection.get_xlabel())
    ax.set_ylabel(projection.get_ylabel())

    if beam:
        add_beam(ax, img)
    ax.grid(True)

    if intensity_colorbar:
        colorbar_pos = ColorbarOutterPosition()
        ticks = mticker.LinearLocator()
        if isinstance(kargs["norm"], LogNorm):
            ticks = mticker.LogLocator()
        colorbar = ColorbarSetting(colorbar_pos, ticks_locator=ticks)
        colorbar.add_colorbar(im_mappable, ax)

    return projection


def switch_axis(ax):
    ax.axis["left"].get_helper().change_tick_coord(0)
    ax.axis["bottom"].get_helper().change_tick_coord(1)

    xlabel = ax.get_xlabel()
    ylabel = ax.get_ylabel()

    ax.set_xlabel(ylabel)
    ax.set_ylabel(xlabel)


def imshow_images(stack, images, projection=None, beam=True, title=True, **kargs):
    def do_plot(fig):
        if len(images) == 3:
            axs = fig.subplots(ncols=3)
        else:
            axs = fig.subplots(n=len(images))

        for i, img in enumerate(images):
            if len(images) == 1:
                ax = axs
            else:
                ax = axs.flatten()[i]
            imshow_image(ax, img, beam=beam, projection=projection, **kargs)

    fig = stack.add_replayable_figure("Images", do_plot)
    return fig


def plot_size_bar(ax, value, value_str, loc=4, pad=0.1, borderpad=0.5, sep=5, frameon=False):
    asb =  AnchoredSizeBar(ax.transData, value, value_str,
                          loc=loc, pad=pad, borderpad=borderpad, sep=sep, frameon=frameon)
    ax.add_artist(asb)


def plot_coords(ax, xy, projection=None, scatter=True, **kargs):
    if projection is not None:
        xy = projection.s2p(xy)
    x, y = xy.T
    checkargs(kargs, 'zorder', 2)
    if scatter:
        ax.scatter(x, y, **kargs)
    else:
        ax.plot(x, y, **kargs)


def plot_mask(ax, mask, **kargs):
    ax.contour(mask.get_mask(), [0.5], **kargs)


def plot_fit(ax, x, y, fct, n=1000, **kwargs):
    fit_fct = fct.fit(x, y)
    x = np.linspace(x.min(), x.max(), n)
    ax.plot(x, fit_fct(x), label=fit_fct.get_text_equ(), **kwargs)

    return fit_fct


def plot_error_span(ax, x, y1, y2, c='y', **kwargs):
    ax.plot(x, y1, c=c, **kwargs)
    ax.plot(x, y2, c=c, **kwargs)
    ax.fill_between(x, y1, y2, color=c, alpha=0.25)



class AbsFormatter(object):
    def __init__(self, useMathText=True):
        self._fmt = ScalarFormatter(useMathText=useMathText, useOffset=False)
        self._fmt.create_dummy_axis()

    def __call__(self, direction, factor, values):
        self._fmt.set_locs(values)
        return [self._fmt(abs(v)) for v in values]


def add_rotated_axis(ax, projection, theta, axis_pos=(1, 3), locator=None, formatter=None):
    """Add an Additional rotated axis
    
    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
    projection : :class:`libwise.imgutils.Projection`
    theta : float
        Angle of rotation of the axis in radians
    axis_pos : tuple, optional
        Position of the axis. Default is (1, 3)
    locator : a grid helper locator, optional
    formatter : a grid helper formatter, optional
    """
    axis = projection.new_rotated_floating_axis([0, 0], theta, axis_pos[0], 
        axis_pos[1], ax)
    axis.set_ticklabel_direction("+")
    axis.major_ticklabels.set_axis_direction("bottom")
    
    axis.set_axis_direction("bottom")
    axis.set_axislabel_direction("+")

    finder = axis._axis_artist_helper.grid_helper.grid_finder
    finder.update(grid_locator1=locator, tick_formatter1=formatter)

    return axis


def p2i(xy_pixel):
    ''' Tramsform [[x, y], ...] to [[y, x]...]'''
    return np.array(xy_pixel).T[::-1].T


def checkargs(kargs, name, value_if_not):
    if name not in kargs:
        kargs[name] = value_if_not


def build_epochs_mappable(epochs, cmap='jet'):
    epochs.sort()
    norm = EpochNormalize(epochs[0], epochs[-1])
    colormap = cm.get_cmap(cmap)
    epochs_map = cm.ScalarMappable(norm, colormap)
    epochs_map.set_array(epochs)

    return epochs_map


class ColorSelector(object):
    ''' Cycle over all colors '''

    def __init__(self):
        self.colors = list(matplotlib.rcParams["axes.color_cycle"]
                           + color_cycle_dark + color_cycle_light)
        self.ids = dict()

    def set(self, id, color):
        self.ids[id] = color

    def get(self, id=None):
        ''' get next color '''
        if id is not None and id in self.ids:
            return self.ids[id]

        if len(self.colors) > 0:
            color = self.colors.pop(0)
        else:
            rnd = nputils.get_random()
            color = rnd.random_sample(3)

        if id is not None:
            self.set(id, color)

        return color

    def get_ids(self):
        return self.ids.keys()

    def get_legend_handler(self, id):
        color = self.get(id)
        return Line2D([0], [0], color=color, ls='', marker='o')


class MarkerSelector(object):
    ''' Cycle over all colors '''

    def __init__(self):
        self.markers = list(best_map_markers + list(set(all_markers.keys()) - set(best_map_markers)))
        self.ids = dict()

    def get(self, id=None):
        ''' get next color '''
        if id is not None and id in self.ids:
            return self.ids[id]

        if len(self.markers) > 0:
            marker = self.markers.pop(0)
        else:
            marker = random.choice(all_markers.keys())

        if id is not None:
            self.ids[id] = marker

        return marker

    def get_ids(self):
        return self.ids.keys()

    def get_legend_handler(self, id):
        marker = self.get(id)
        return Line2D([0], [0], color='none', mfc='none', mew=1.5, marker=marker, ls='')


class EpochNormalize(Normalize):

    def __init__(self, epoch0, epoch1):
        Normalize.__init__(self, self.mktime(epoch0), self.mktime(epoch1))

    def __call__(self, epoch, **kargs):
        if isinstance(epoch, np.ndarray) and len(epoch.shape) == 0:
            epoch = epoch.item()
        return Normalize.__call__(self, self.mktime(epoch), **kargs)

    def mktime(self, epoch):
        if isinstance(epoch, datetime.datetime):
            return mdates.date2num(epoch)
        return epoch


class ColorbarInnerPosition(object):

    def __init__(self, orientation="horizontal", width="5%", height="50%", location=1, pad=0.5, 
                 tick_position=None):
        '''
        width, height: inch if number, percentage of parent axes if string (like '5%')
        pad: points
        location are :
        'upper right' : 1,
        'upper left' : 2,
        'lower left' : 3,
        'lower right' : 4,
        'right' : 5,
        'center left' : 6,
        'center right' : 7,
        'lower center' : 8,
        'upper center' : 9,
        'center' : 10,
        '''
        self.orientation = orientation
        if orientation == 'vertical':
            self.width = width
            self.height = height
            if tick_position is None:
                tick_position = 'left'
        else:
            self.width = height
            self.height = width
            if tick_position is None:
                tick_position = 'bottom'
        self.location = location
        self.pad = pad
        self.tick_position = tick_position

    def get_cb_axes(self, ax):
        cax = inset_axes(ax, width=self.width, height=self.height, loc=self.location, borderpad=self.pad)
        return cax

    def post_creation(self, colorbar):
        if self.orientation == 'vertical':
            if self.tick_position == 'left':
                colorbar.ax.yaxis.set_ticks_position(self.tick_position)
                colorbar.ax.yaxis.set_label_position(self.tick_position)
        else:
            if self.tick_position == 'top':
                colorbar.ax.xaxis.set_ticks_position(self.tick_position)
                colorbar.ax.xaxis.set_label_position(self.tick_position)

    def get_orientation(self):
        return self.orientation


class ColorbarOutterPosition(object):

    def __init__(self, width="5%", pad="3%", location="right"):
        ''''
        width: inch if number, percentage of parent axes if string (like '5%')
        pad: inch if number, percentage of parent axes if string (like '5%')
        location: top, bottom, right, left
        '''
        self.width = width
        self.pad = pad
        self.location = location

    def get_cb_axes(self, ax):
        divider = make_axes_locatable(ax)
        cax = divider.append_axes(self.location, self.width, pad=self.pad)
        cax.axis[:].toggle(ticklabels=False)
        cax.axis[self.location].toggle(ticklabels=True)
        return cax

    def get_orientation(self):
        if self.location in ['left', 'right']:
            return "vertical"
        return "horizontal"

    def post_creation(self, colorbar):
        pass


class ColorbarSetting(object):

    def __init__(self, cb_position=None, ticks_locator=None, ticks_formatter=None, cmap='jet'):
        if cb_position is None:
            cb_position = ColorbarOutterPosition()
        self.cb_position = cb_position
        self.ticks_locator = ticks_locator
        self.ticks_formatter = ticks_formatter
        self.cmap = cmap

    def add_colorbar(self, mappable, ax):
        fig = ax.get_figure()
        cb = fig.colorbar(mappable, ticks=self.ticks_locator, format=self.ticks_formatter,
                            orientation=self.cb_position.get_orientation(), cax=self.cb_position.get_cb_axes(ax))
        self.cb_position.post_creation(cb)
        if not hasattr(fig, '_plotutils_colorbars'):
            fig._plotutils_colorbars = dict()
        fig._plotutils_colorbars[ax] = cb
        return cb

    def get_cmap(self):
        return self.cmap


class BaseCustomFigure(Figure):

    def subplots(self, nrows=1, ncols=1, n=None, sharex=False, sharey=False,
                 sharex_hspace=0.15, sharey_wspace=0.15, axisartist=True, reshape=True):
        if n is not None and n > 1:
            ncols = np.ceil(np.sqrt(n))
            nrows = np.ceil(n / ncols)

        # Create empty object array to hold all axes. It's easiest to make it 1-d
        # so we can just append subplots upon creation, and then reshape
        nplots = int(nrows * ncols)
        axarr = np.empty(nplots, dtype=object)

        sharedx_axes = None
        sharedy_axes = None

        if sharex:
            self.subplots_adjust(hspace=sharex_hspace)
        if sharey:
            self.subplots_adjust(wspace=sharey_wspace)

        for i in range(nplots):
            if axisartist:
                subplot = Subplot(self, nrows, ncols, i + 1, sharex=sharedx_axes, sharey=sharedy_axes)
                axarr[i] = self.add_subplot(subplot)
            else:
                axarr[i] = self.add_subplot(nrows, ncols, i + 1, sharex=sharedx_axes, sharey=sharedy_axes)
            if ncols == 1 and sharex:
                if not sharedx_axes:
                    sharedx_axes = axarr[i]
                if i != nplots - 1:
                    axarr[i].axis["top", "bottom"].toggle(ticklabels=False)
                    # for label in axarr[i].get_xticklabels():
                    #     label.set_visible(False)
            if nrows == 1 and sharey:
                if not sharedy_axes:
                    sharedy_axes = axarr[i]
                if i != 0:
                    axarr[i].axis["left", "right"].toggle(ticklabels=False)
                    # for label in axarr[i].get_yticklabels():
                    #     label.set_visible(False)

        if reshape:
            if nplots == 1:
                return axarr[0]
            elif nrows == 1 or ncols == 1:
                return axarr

            axarr = axarr.reshape(nrows, ncols)

        return axarr


class ReplayableFigure(BaseCustomFigure):

    def __init__(self, draw_fct, *args, **figure_kargs):
        BaseCustomFigure.__init__(self, **figure_kargs)
        self.draw_callbacks = []
        self.last_args = []

        self.add_callback(draw_fct)

        self.replay(*args)

    def add_callback(self, fct):
        self.draw_callbacks.append(fct)

    def done(self):
        self.canvas = None

    def replay(self, *args):
        if len(args) == 0 and len(self.last_args) != 0:
            args = self.last_args

        self.clear()
        for callback in self.draw_callbacks:
            callback(self, *args)

        # Keep the last arguments in case we need to replay without knowing
        # the arguments, e.g. for SaveFigure
        self.last_args = args


class Movie(Figure):

    def __init__(self, interval, repeat_delay):
        super(Movie, self).__init__()
        self.ims = []
        self.interval = interval
        self.repeat_delay = repeat_delay
        self.ax = self.add_subplot(1, 1, 1)
        self.anim = None

    def add_image(self, img, **kwargs):
        self.ims.append([self.ax.imshow(img, **kwargs)])

    def snapshot(self):
        childs = [k for k in self.ax.get_children() if isinstance(k, AxesImage) or isinstance(k, Text)]
        self.ims.append(childs)
        return childs

    def draw(self, canva):
        super(Movie, self).draw(canva)
        if self.anim is None:
            self.anim = animation.ArtistAnimation(self, self.ims,
                                                  interval=self.interval,
                                                  blit=False,
                                                  repeat_delay=self.repeat_delay)
            self.anim._start()


class BaseFigureStack(object):

    def __init__(self, title="Figure Stack", fixed_aspect_ratio=False, **kwargs):
        self.window_title = title
        self.fixed_aspect_ratio = fixed_aspect_ratio
        self.figures = []
        self.kwargs = kwargs

    def save_picture(self, dirpath, basename, ext='.png', preset=None):
        if preset is not None:
            printer_preset = presetutils.RcPreset.load(preset)
            display_preset = presetutils.RcPreset.load("display")

        for i, figure in enumerate(self.figures):
            if preset is not None:
                printer_preset.apply(figure)
            figure.tight_layout(pad=0.3)
            remove_canvas = False
            if figure.canvas is None:
                self.canvas_klass(figure)
                remove_canvas = True
            filepath = os.path.join(dirpath, '%s_%s%s' % (basename, i, ext))
            print "Saving: %s" % filepath
            figure.savefig(filepath)
            if preset is not None:
                display_preset.apply(figure)
            if remove_canvas:
                figure.canvas = None

    def save_movie(self, dirpath, basename, ext='.avi'):
        tempdir = tempfile.mkdtemp()
        self.save_picture(tempdir, basename, '.png')
        input_files = os.path.join(tempdir, '%s_%s.png' % (basename, "%d"))
        output_file = os.path.join(dirpath, '%s%s' % (basename, ext))

        cmd = 'avconv -r 1 -i %s %s' % (input_files, output_file)
        os.system(cmd)
        shutil.rmtree(tempdir)

    def save_pdf(self, filepath, preset=None):
        pdf = PdfPages(filepath)
        print "Saving: %s" % filepath
        if preset is not None:
            printer_preset = presetutils.RcPreset.load(preset)
            display_preset = presetutils.RcPreset.load("display")

        for figure in self.figures:
            if preset is not None:
                printer_preset.apply(figure)
            figure.tight_layout(pad=0.3)
            remove_canvas = False
            if figure.canvas is None:
                self.canvas_klass(figure)
                remove_canvas = True
            pdf.savefig(figure)
            if preset is not None:
                display_preset.apply(figure)
            if remove_canvas:
                figure.canvas = None
        pdf.close()

    def save_all(self, filename, preset=None):
        filepath, ext = os.path.splitext(filename)
        dirpath, basename = os.path.split(filepath)
        if ext == '.pdf':
            self.save_pdf(filename, preset=preset)
        elif ext in ['.jpg', '.png']:
            self.save_picture(dirpath, basename, ext, preset=preset)
        elif ext in ['.avi', '.mp4']:
            self.save_movie(dirpath, basename, ext)

    def add_figure(self, name="None", figure=None, position=None):
        if figure is None:
            figure = BaseCustomFigure(dpi=75, **self.kwargs)
        if position is not None:
            self.figures.insert(position, figure)
        else:
            self.figures.append(figure)
        return figure

    def add_replayable_figure(self, name, draw_fct, *args):
        figure = ReplayableFigure(draw_fct, *args, dpi=75)
        self.add_figure(name, figure)
        return figure

    def add_subplots(self, name="", nrows=1, ncols=1, n=None, sharex=False, sharey=False,
                     sharex_hspace=0.15, sharey_wspace=0.15, axisartist=True, reshape=True):
        fig = self.add_figure(name)
        return fig, fig.subplots(nrows, ncols, n, sharex, sharey, sharex_hspace, sharey_wspace, 
                                 axisartist=axisartist, reshape=reshape)

    def add_tooltip(self, axes, coord, text, tol=5):
        pass

    def add_intensity_tooltip(self, figure):
        pass

    def show(self, start_main=True):
        # maybe save it
        pass

    def destroy(self):
        for figure in self.figures:
            figure.clf()
            figure.canvas = None
