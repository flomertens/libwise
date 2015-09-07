from plotutils_base import *

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


def subplots(**kargs):
    figure = BaseCustomFigure()
    axes = figure.subplots(**kargs)

    return axes

class FigureStack(BaseFigureStack):

    def __init__(self, *args, **kargs):
        BaseFigureStack.__init__(self, *args, **kargs)
        self.canvas_klass = FigureCanvas
