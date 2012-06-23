"""
    Missile Defence Game
    Background-drawing module (sky gradient and stars).
    
    Copyright (C) 2011-2012 Ryan Lothian.
    See LICENSE (GNU GPL version 3 or later).
"""


import random
from random import uniform

import pygame
import math


def grad(x, y, proportion):
    colour = [int(b * proportion + a * (1 - proportion)) for
              (a,b) in zip(x, y)]
    return colour
  
class VerticalGradient(object):
    def __init__(self, top_colour, bottom_colour):
        self.top_colour    = top_colour
        self.bottom_colour = bottom_colour
        
    def draw(self, surface):        
        for y in range(0, surface.get_height()):
            proportion = float(y) / (surface.get_height() - 1)
            colour = grad(self.top_colour, self.bottom_colour,
                          proportion)
            pygame.draw.line(surface, colour, (0, y),
                             (surface.get_width() - 1, y))

class Star(object):
    def __init__(self, position, max_brightness):
        self.phase = random.uniform(0, 3.14159265 * 2)
        self.position = position
        self.max_brightness = max_brightness
        self.min_brightness = random.uniform(0, self.max_brightness)
        self.rate = random.uniform(0.03, 0.1)
    
    def tick(self, resolution):
        self.phase += random.uniform(0, self.rate)
                
    def draw(self, surface, tmp_surf):
        brightness = (self.min_brightness + 
                     ((self.max_brightness - self.min_brightness) * 
                      (math.sin(self.phase) + 1.0) / 2.0))
                      
        if brightness > 1.0:
            brightness = 1.0
        
        tmp_surf.set_alpha(int(255 * brightness))
        surface.blit(tmp_surf, [int(x) for x in self.position])
            
class StarryBackground(object):
    def darken(self):    
        new_colour = [max(0, x - 1) for x in 
                      self.grad.bottom_colour]

        # don't go too dark or you won't be able to see the buildings
        if sum(new_colour) < 80:
            new_colour = list(self.grad.bottom_colour)
        
        if new_colour[0] < 50: new_colour[0] += 1               
        
        self.grad.bottom_colour = new_colour
                      
    def make_star(self):
        position   = [uniform(0, limit) for limit in self.resolution]
        
        # max stars nearer to the horizon duller
        max_brightness = 0.2 + 1.2 * random.random() * (1.0 - (position[1] / self.resolution[1]))
        if max_brightness > 1.0:
            max_brightness = 1.0
        return Star(position, max_brightness)
        
    def __init__(self, resolution):
        self.resolution = resolution

        bottom_colour = (0,)
        
        # make sure we get a bright enough colour to see the buildings
        while sum(bottom_colour) < 120:        
            bottom_colour = (max(0, uniform(-100, 100)),
                             max(0, uniform(-100, 50)),
                             max(0, uniform(-100, 200)))
            

        self.grad = VerticalGradient(top_colour=(0,0,20),
                                     bottom_colour=bottom_colour)
                                 
        self.stars = [self.make_star() for i in range(1000)]
    
    def draw(self, surface):
        self.grad.draw(surface)
        tmp_surf = pygame.Surface((1, 1))
        tmp_surf.fill((255, 255, 255))
        
        for star in self.stars:
            star.tick(self.resolution)
            star.draw(surface, tmp_surf)
            
