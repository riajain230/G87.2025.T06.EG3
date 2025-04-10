#   -*- coding: utf-8 -*-
from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")


name = "G8X.2025.TYY.GE2"
default_task = "publish"


@init
def set_properties(project):
    pass
