'''
Created on Feb 28, 2012

@author: fmertens
'''

try:
    from plotutils_ui import *
except ImportError:
    from plotutils_noui import *

from plotutils_noui import FigureStack as FigureStackNoUI


def test_figure_stack():
    # app = QtGui.QApplication([])
    stack = FigureStack(fixed_aspect_ratio=False)

    fig, axs = stack.add_subplots("Random", n=2)

    for ax in axs.flatten():
        ax.imshow(np.random.randn(20, 20), extent=[-50, 100, -20, 160])

    def do_plot(fig):
        ax = fig.subplots()
        img = imgutils.Image(imgutils.galaxy())
        # imshow_image(ax, img)
        prj = img.get_projection(relative=True)
        set_grid_helper(ax, prj.get_gh())
        ax.imshow(img.data, alpha=0.5)
        ax.imshow(np.roll(imgutils.galaxy(), 10), alpha=0.5)

    stack.add_replayable_figure("Images", do_plot)

    walks = [nputils.random_walk() for i in range(7)]

    def do_plot(fig):
        axs = fig.subplots(nrows=2)
        for walk in walks:
            axs[0].plot(walk)

        x = np.linspace(0, 5, 1000)
        axs[1].plot(x, np.cos(2 * np.pi * x))
        axs[1].plot(x, np.sin(x))

    stack.add_replayable_figure("Plot", do_plot)

    stack.show()
    # app.exec_()


def test_projection():
    stack = FigureStack()

    img = imgutils.Image(imgutils.galaxy())
    prj = imgutils.Projection(imgutils.ScaleTransform(2, np.array(img.data.shape) / 2), "X", "Y", 
                              imgutils.u.pix, imgutils.PixelCoordinateSystem())

    fig, ax = stack.add_subplots()
    imshow_image(ax, img, projection=prj)

    stack.show()


def test_save_plot():

    def draw_fct(figure):
        ax1 = figure.subplots(nrows=1)
        x = np.linspace(0, 2 * np.pi, 1000)
        ax1.plot(x, np.cos(x), label="Cosinus")
        ax1.plot(x, np.sin(x), label="Sinus")
        ax1.set_title("Test")
        ax1.legend()

    fig = ReplayableFigure(draw_fct)
    # fig = BaseCustomFigure()
    # draw_fct(fig)

    w = SaveFigure(fig, auto_dpi=True)
    w.start()


def test_plot():
    stack = FigureStack()
    fig, ax = stack.add_subplots("Test")

    ax.plot([0, 1])
    ax.text(0.2, 0.2, "A")

    matplotlib.rc("font", size=30)
    fig, ax = stack.add_subplots("Test")
    ax.plot([0, 1])
    ax.text(0.4, 0.4, "A")

    stack.show()


def test_colors():
    stack = FigureStack()
    for cycle in [color_cycle, color_cycle_dark, color_cycle_light]:
        fig, ax = stack.add_subplots("Test")

        for color, a in zip(cycle, np.arange(0.5, 1.5, 0.1)):
            x = np.linspace(0, 10, 500)
            y = a * x
            ax.plot(x, y, c=color, lw=3)

    stack.show()


def test_linestyle():
    stack = FigureStack()
    fig, ax = stack.add_subplots("Test")

    for ls, a in zip(['-', '--', '-.', ':'], np.arange(0.5, 1.5, 0.1)):
        x = np.linspace(0, 10, 500)
        y = a * x
        ax.plot(x, y, c=black, lw=3, ls=ls)

    stack.show()


def test_dashes():
    stack = FigureStack()
    fig, ax = stack.add_subplots("Test")

    for ls, a in zip([[10, 0], [10, 2], [5, 5], [20, 2], [10, 2, 5, 2]], np.arange(0.5, 1.5, 0.1)):
        x = np.linspace(0, 10, 500)
        y = a * x
        ax.plot(x, y, c=black, lw=3, dashes=ls)

    stack.show()


def test_markers():
    stack = FigureStack()
    color = ColorSelector()
    markers = all_markers
    fig, ax = stack.add_subplots("Test")
    all_y = np.linspace(1, 40, len(markers))
    for marker, a in zip(markers.keys(), all_y):
        x = np.linspace(0, 10, 10)
        y = a * np.ones_like(x)
        ax.plot(x, y, c=color.get(), lw=2, marker=marker)

    ax.set_yticks(all_y)
    ax.set_yticklabels(['%s (%s)' % (v, k) for k, v in markers.items()])
    stack.show()


def test_share():
    win = BaseFigureWindow(None, "Test")

    axs = win.figure.subplots(nrows=3, sharex=True)

    # x = np.linspace(0, 6, 1000)
    x = np.arange(1000)
    y = np.cos(2 * np.pi * 1 / 100. * x)
    axs[0].plot(x, y)
    axs[1].plot(x, -np.sin(0.006 * x))
    axs[2].plot(x, np.gradient(y))
    # x = np.linspace(0, 2, 1000)
    # axs[2].plot(x, np.tan(x))

    win.start()


def test_arrow():
    import matplotlib.pyplot as plt
    g = imgutils.galaxy()

    stack = FigureStack()
    fig, ax = stack.add_subplots()

    ax.imshow(g)

    patch = plt.Arrow(50, 50, 20, 30, width=10)
    ax.add_patch(patch)

    stack.show()


def test_memory_release():
    test_arrow()
    test_colorbar()
    test_share()


def test_colorbar():
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    stack = FigureStack()
    fig, (ax1, ax2) = stack.add_subplots("Colorbar test", ncols=2)

    # axins1 = inset_axes(ax1,
    #                     width=3.5, # width = 10% of parent_bbox width
    #                     height=0.05, # height : 50%
    #                     loc=1, bbox_transform=ax1.transAxes, bbox_to_anchor=(-0, 0, 1, 1), borderpad=0.5)

    cb_position = ColorbarInnerPosition(orientation='horizontal', location=1, pad=0, tick_position='bottom')

    colorbar = ColorbarSetting(cb_position, mticker.FixedLocator([1, 2, 3]))

    im1 = ax1.imshow([[1,2],[2, 3]])
    cb = colorbar.add_colorbar(im1, ax1)
    # fig.colorbar(im1, cax=axins1, orientation="horizontal", ticks=[1,2,3])
    # cb.ax.yaxis.set_ticks_position("default")

    # cax = inset_axes(ax2,
    #                    width="5%", # width = 10% of parent_bbox width
    #                    height="100%", # height : 50%
    #                    loc=4,
    #                    bbox_to_anchor=(0.1, 0., 1, 1),
    #                    bbox_transform=ax2.transAxes,
    #                    borderpad=0, 
    #                    )

    colorbar = ColorbarSetting()

    # Controlling the placement of the inset axes is basically same as that
    # of the legend.  you may want to play with the borderpad value and
    # the bbox_to_anchor coordinate.

    im = ax2.imshow([[1,2],[2, 3]])
    colorbar.add_colorbar(im, ax2)
    # cb.ax.get_yaxis().set_ticks_position('right')
    # cb.ax.get_yaxis().set_label_position('right')
    # cb.update_ticks()
    # print cb.orientation
    # print cb.ax.get_yaxis().get_ticks_position()

    stack.show()


def test_noui():
    stack = FigureStackNoUI()

    fig, axs = stack.add_subplots("Random", n=2)

    for ax in axs.flatten():
        ax.imshow(np.random.randn(20, 20), extent=[-50, 100, -20, 160])

    def do_plot(fig):
        ax = fig.subplots()
        img = imgutils.Image(imgutils.galaxy())
        # imshow_image(ax, img)
        prj = img.get_projection(relative=True)
        set_grid_helper(ax, prj.get_gh())
        ax.imshow(img.data, alpha=0.5)
        ax.imshow(np.roll(imgutils.galaxy(), 10), alpha=0.5)

    stack.add_replayable_figure("Images", do_plot)

    walks = [nputils.random_walk() for i in range(7)]

    def do_plot(fig):
        axs = fig.subplots(nrows=2)
        for walk in walks:
            axs[0].plot(walk)

        x = np.linspace(0, 5, 1000)
        axs[1].plot(x, np.cos(2 * np.pi * x))
        axs[1].plot(x, np.sin(x))

    stack.add_replayable_figure("Plots", do_plot)

    filename = "/tmp/test_figure_stack_no_ui.pdf"
    stack.save_pdf(filename, "thesis")
    os.system("evince %s" % filename)


def test_lmc():
    import mpl_toolkits.axisartist.angle_helper as angle_helper

    stack = FigureStack()
    fig, ax = stack.add_subplots("LMC")

    lmc = imgutils.FitsImage(os.path.expanduser("~/data/lmc/lmc_bothun_R_ast.fits"))
    # lmc = imgutils.FitsImage(os.path.expanduser("~/data/crab/H1-FL.FITS"))

    # lmc.rotate(np.radians(60), spline_order=0, smooth_len=0)
    # lmc.resize([600, 600])
    prj = lmc.get_projection(relative=False, unit=imgutils.u.deg, center='center')

    def do_plot_lmc(ax):
        imshow_image(ax, lmc, projection=prj)
        # update_grid_helper(ax, tick_formatter1=angle_helper.FormatterHMS(), tick_formatter2=angle_helper.FormatterDMS(),
                               # grid_locator1=angle_helper.LocatorHMS(4), grid_locator2=angle_helper.LocatorDMS(4))

    do_plot_lmc(ax)

    def do_plot(fig):
        do_plot_lmc(fig.subplots())

    stack.add_replayable_figure("LMC replayable", do_plot)

    stack.show()


def test_m87():
    stack = FigureStack()
    fig, ax = stack.add_subplots()

    m87 = imgutils.FitsImage(os.path.expanduser("~/data/m87/cwalker/run001/reference_image"))

    cmap = get_cmap('YlGnBu_r')
    # cmap.set_bad(color='white', alpha=1)

    imshow_image(ax, m87, cmap=cmap)

    stack.show()


if __name__ == '__main__':
    test_figure_stack()
    # test_save_plot()
    # test_lmc()
    # test_m87()
    # test_markers()
    # test_colors()
    # test_colorbar()
    # test_noui()

    # for i in range(10):
    # import gc
    # test_lmc()

    # from meliae import scanner
    # scanner.dump_all_objects(os.path.expanduser('~/memory.json'))
