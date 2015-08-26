"""
Interactive tool to draw mask on an image or image-like array.

Adapted from https://gist.github.com/tonysyu/3090704

Adapted from matplotlib/examples/event_handling/poly_editor.py

"""
import os

import numpy as np

from libwise import uiutils, imgutils, plotutils

import gtk
import pyregion

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.mlab import dist_point_to_segment


class PolyRegionEditor(uiutils.UI):

    def __init__(self, img, prj=None, max_ds=10, current_folder=None):
        self.max_ds = max_ds
        self.showverts = True
        self.current_folder = current_folder

        uiutils.UI.__init__(self, 750, 600, "PolyRegion Editor")

        vbox = gtk.VBox(False, 10)
        self.add(vbox)

        canva_box = gtk.HBox()
        vbox.pack_start(canva_box, True, True)

        self.canvas = plotutils.BaseCustomCanvas()
        canva_box.pack_start(self.canvas, True, True)

        ctl = gtk.HBox(False, 10)
        vbox.pack_start(ctl, False, False)

        ctl.pack_start(plotutils.NavigationToolbar(self.canvas, self), True, True)

        self.title_entry = uiutils.EntryDescription("Title")
        ctl.pack_start(self.title_entry, False, False)

        self.color_entry = uiutils.EntryDescription("Color")
        ctl.pack_start(self.color_entry, False, False)

        save_bn = gtk.Button("Save")
        save_bn.connect("clicked", self.on_save_clicked)
        ctl.pack_end(save_bn, False, True)

        load_bn = gtk.Button("Load")
        load_bn.connect("clicked", self.on_load_clicked)
        ctl.pack_end(load_bn, False, True)

        save_bn = gtk.Button("New")
        save_bn.connect("clicked", self.on_new_clicked)
        ctl.pack_end(save_bn, False, True)

        self.ax = self.canvas.figure.subplots()

        if prj is None:
            prj = img.get_projection()

        self.prj = prj
        self.img = img

        plotutils.imshow_image(self.ax, self.img, projection=self.prj, title=False)

    def get_axes(self):
        return self.ax

    def load_poly_region(self, poly_region):
        self.title_entry.set_text(poly_region.title)
        self.color_entry.set_text(poly_region.color)
        self.poly.set_fc(poly_region.color)
        vertices = list(poly_region.vertices)
        vertices.append(vertices[0])
        self.poly.xy = vertices
        self._update_line()
        self.canvas.draw()

    def load_default(self):
        default_poly_region = imgutils.PolyRegion.default_from_ax(self.ax)
        self.load_poly_region(default_poly_region)

    def start(self):
        self.poly = Polygon([[0, 0]], animated=True,
                    fc='b', ec='none', alpha=0.4)

        self.ax.add_patch(self.poly)
        self.ax.set_clip_on(False)
        self.ax.set_title("Click and drag a point to move it; "
                     "'i' to insert; 'd' to delete.")

        x, y = zip(*self.poly.xy)
        self.line = plt.Line2D(x, y, color='none', marker='o', mfc='r',
                               alpha=0.8, animated=True, lw=2, markersize=self.max_ds)
        self._update_line()
        self.ax.add_line(self.line)

        self.poly.add_callback(self.poly_changed)
        self._ind = None # the active vert

        canvas = self.poly.figure.canvas
        canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas

        self.load_default()

        self.show_all()
        gtk.main()

    def on_load_clicked(self, bn):
        filename = uiutils.select_file(parent=self, current_folder=self.current_folder,
                                       action=gtk.FILE_CHOOSER_ACTION_OPEN)
        if filename is not None:
            try:
                poly_region = imgutils.PolyRegion.from_file(filename, self.img.get_coordinate_system())
                self.load_poly_region(poly_region)
            except:
                msg = "Failed to load region %s" % filename
                print msg
                uiutils.error_msg(msg, self)

    def on_save_clicked(self, bn):
        filename = uiutils.select_file(parent=self, current_folder=self.current_folder)

        if filename is not None:
            vertices = self.poly.xy
            color = self.color_entry.get_text()
            title = self.title_entry.get_text()
            poly_region = PolyRegion(vertices, color=color, title=title)
            try:
                poly_region.to_file(filename, self.img.get_coordinate_system())
            except:
                msg = "Failed to save region %s" % filename
                print msg
                uiutils.error_msg(msg, self)

    def on_new_clicked(self, bn):
        self.load_default()

    def get_points(self):
        return self.poly.xy

    def poly_changed(self, poly):
        'this method is called whenever the polygon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        #Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state

    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        ignore = not self.showverts or event.inaxes is None or event.button != 1
        if ignore:
            return
        self._ind = self.get_ind_under_cursor(event)

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        ignore = not self.showverts or event.button != 1
        if ignore:
            return
        self._ind = None

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes:
            return
        if event.key=='t':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts:
                self._ind = None
        elif event.key=='d':
            ind = self.get_ind_under_cursor(event)
            if ind is None:
                return
            if ind == 0 or ind == self.last_vert_ind:
                print "Cannot delete root node"
                return
            self.poly.xy = [tup for i,tup in enumerate(self.poly.xy)
                                if i!=ind]
            self._update_line()
        elif event.key=='i':
            xys = self.poly.get_transform().transform(self.poly.xy)
            p = event.x, event.y # cursor coords
            for i in range(len(xys)-1):
                s0 = xys[i]
                s1 = xys[i+1]
                d = dist_point_to_segment(p, s0, s1)
                if d <= self.max_ds:
                    self.poly.xy = np.array(
                        list(self.poly.xy[:i+1]) +
                        [(event.xdata, event.ydata)] +
                        list(self.poly.xy[i+1:]))
                    self._update_line()
                    break
        self.canvas.draw()

    def motion_notify_callback(self, event):
        'on mouse movement'
        if event.inaxes is not None:
            self.canvas.grab_focus()
        ignore = (not self.showverts or event.inaxes is None or
                  event.button != 1 or self._ind is None)
        if ignore:
            return
        x,y = event.xdata, event.ydata

        if self._ind == 0 or self._ind == self.last_vert_ind:
            self.poly.xy[0] = x,y
            self.poly.xy[self.last_vert_ind] = x,y
        else:
            self.poly.xy[self._ind] = x,y
        self._update_line()

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

    def _update_line(self):
        # save verts because polygon gets deleted when figure is closed
        self.verts = self.poly.xy
        self.last_vert_ind = len(self.poly.xy) - 1
        self.line.set_data(zip(*self.poly.xy))

    def get_ind_under_cursor(self, event):
        'get the index of the vertex under cursor if within max_ds tolerance'
        # display coords
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        indseq = np.nonzero(np.equal(d, np.amin(d)))[0]
        ind = indseq[0]
        if d[ind] >= self.max_ds:
            ind = None
        return ind


def test_editor():
    fits = os.path.expanduser("~/data/crab/H1-FL.FITS")
    # fits = "/homes/fmertens/data/3c273/mojave/full_stack_image.fits"
    # fits = "/homes/fmertens/data/m87/mojave/full_stack_image.fits"

    img = imgutils.FitsImage(fits)

    editor = PolyRegionEditor(img, current_folder=os.path.dirname(fits))
    editor.start()


def fix_crval(region_file, stack_image_file, fits_new_crval_file):
    stack_image = imgutils.FitsImage(stack_image_file)
    fits_new_crval = imgutils.FitsImage(fits_new_crval_file)
    region = imgutils.PolyRegion.from_file(region_file, stack_image.get_coordinate_system())
    prj1 = stack_image.get_projection(relative=False)
    prj2 = fits_new_crval.get_projection(relative=False)

    region.vertices = [prj2.s2p(prj1.p2s(coord)) for coord in region.vertices]

    region.to_file(region_file, stack_image.get_coordinate_system())


if __name__ == '__main__':
    test_editor()
    # fix_crval("/homes/fmertens/data/m87/mojave/north_rail.reg", 
    #           "/homes/fmertens/data/m87/mojave/full_stack_image.fits",
    #           "/homes/fmertens/data/m87/mojave/icn/1228+126.u.2010_09_29.icn.fits")
