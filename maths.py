"""
    Missile Defence Game
    Mathematics functions.
    
    Copyright (C) 2011-2012 Ryan Lothian.
    See LICENSE (GNU GPL version 3 or later).
"""

import numpy
import math

def size_squared(a):
    return numpy.ma.innerproduct(a, a)
    
def normalize(a):
    size = math.sqrt(size_squared(a))
    if size == 0:
        return a
    else:
        b = a / size
        return b

