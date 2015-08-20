from plotutils_base import *

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


class FigureStack(BaseFigureStack):

    def __init__(self, *args, **kargs):
        BaseFigureStack.__init__(self, *args, **kargs)
