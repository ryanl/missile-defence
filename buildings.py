"""
    Missile Defence Game
    Building generation, drawing and destruction module.
    
    Copyright (C) 2011-2012 Ryan Lothian.
    See LICENSE (GNU GPL version 3 or later).
"""

import numpy
from random import uniform

def generate_city(resolution):
    # create a byte array for buildings info
    # we will use 0 for empty, 1 for present
    pixeldata = numpy.zeros(resolution, numpy.int8)

    x = 100
    while x < resolution[0] - 120:
        gap = int(uniform(0, 5))
        x += gap
    
        width  = int(uniform(5, 20))
        height = int(uniform(10, 18))
        add_building(pixeldata, x + (width / 2), width, height)   

    x = 120
    while x < resolution[0] - 180:
        gap = int(uniform(5, 20))
        x += gap
    
        width  = int(uniform(10, 40))
        height = int(uniform(20, 50))            
        add_building(pixeldata, x + (width / 2), width, height)   

    x = 160
    while x < resolution[0] - 220:
        gap = int(uniform(30, 125))
        x += gap
    
        width  = int(uniform(8, 20))
        height = int(uniform(70, 90))
        add_building(pixeldata, x + (width / 2), width, height)   
        
    # add support for the cannon
    add_building(pixeldata, resolution[0] / 2, 20, 100)
    
    return pixeldata
    
def add_building(pixeldata, x_mid, width, height):
    # todo: add windows
    resolution = numpy.ma.shape(pixeldata)
    for x in range(x_mid - (width/2), x_mid + (width/2)):
        for y in range(resolution[1] - height, resolution[1]):
            try:
                pixeldata[x][y] = 1
            except IndexError:
                pass

class Buildings(object):
    def __init__(self, pixeldata, resolution):
        self.dirty_set  = set()
        self.pixeldata  = pixeldata
        self.resolution = resolution

    def get(self, x, y):
        x, y = int(x), int(y)
        if x < 0 or y < 0:
            return 0
            
        try:
            return self.pixeldata[x][y]
        except IndexError:
            return 0
                
    def destroy_circle(self, position, radius):        
        x_min = max(0, int(position[0] - radius))
        x_max = min(self.resolution[0], int(position[0] + radius + 1))
        y_min = max(0, int(position[1] - radius))
        y_max = min(self.resolution[1], int(position[1] + radius + 1))
        
        radius_squared = int(radius * radius)
        
        # destroy buildings in the blast radius
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):            
                dist_x = position[0] - x
                dist_y = position[1] - y
                if dist_x * dist_x + dist_y * dist_y < radius_squared:
                    if self.pixeldata[x][y] == 1:
                        self.pixeldata[x][y] = 0
                        self.dirty_set.add((x,y))
                        
    def apply_physics(self):
        ignore_set = set()
        new_dirty_set = set()
        
        for (x,y) in self.dirty_set:
            assert x >=0 and y >=0 and type(x) == type(1) and type(y) == type(1)             
            assert self.pixeldata[x][y] == 0
                            
            if (x,y) in ignore_set:
                new_dirty_set.add((x,y))
            else:
                y2 = y - 1
                any_falling = False
                while y2 > 0 and self.pixeldata[x][y2] == 1:
                    y2 -= 1
                    any_falling = True
                
                if any_falling:
                    self.pixeldata[x][y2 + 1] = 0
                    self.pixeldata[x][y] = 1
                    assert (x,y) not in new_dirty_set
                    if y + 1 < self.resolution[1] and self.pixeldata[x][y + 1] == 0:
                        new_dirty_set.add((x, y + 1))
                        ignore_set.add((x, y + 1)) # don't want it falling any further
        self.dirty_set = new_dirty_set

