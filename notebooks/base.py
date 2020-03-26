import os
import sys

import pandas as pd
import numpy as np

from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import Range1d

output_notebook()

sys.path.append("..")

from util import DataSources, Storage
from sources import *


def get_datetime_formatter():
    return DatetimeTickFormatter(
        seconds=["%Y-%m-%d %H:%M:%S"],
        minsec=["%Y-%m-%d %H:%M:%S"],
        minutes=["%Y-%m-%d %H:%M"],
        hourmin=["%Y-%m-%d %H:%M"],
        hours=["%Y-%m-%d %H:%M"],
        days=["%Y-%m-%d"],
        months=["%Y/%m"],
        years=["%Y"],
    )