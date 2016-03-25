#!/usr/bin/python

"""
    Missile Defence Game
    
    Copyright (C) 2011-2016 Ryan Lothian.
    See LICENSE (Apache 2).
"""

import pygame
import pygame.font

import collections

import numpy
from   numpy import array

import math
from maths import size_squared, normalize

import random
from random import uniform


# imports from my files
import background
import projectiles
from background import grad
from cannon import DefenceCannon
from buildings import Buildings, generate_city


class Physics(object):
    """Physics related constants"""
    air_resistance = 0.999
    gravity        = 0.05
    wind           = 0.0
    
    def __init__(self, game):
        self.game = game
        self.location_map = collections.defaultdict(list)
            
    def _get_adjacent_projectiles(self, position):
        orig_cell = self._get_cell_for(position)
        cells = []
        for xdiff in [-1, 0, 1]:
            for ydiff in [-1, 0, 1]:  
                new_cell = ((orig_cell[0] + xdiff, orig_cell[1] + ydiff))
                if new_cell in self.location_map:
                    for p in self.location_map[new_cell]:
                        yield p
        
    def _get_cell_for(self, position):
        return tuple(int(x) / 50 for x in position)
        
    def update_location_cache(self):
        self.location_map.clear()
        for p in self.game.projectiles:
            self.location_map[self._get_cell_for(p.position)].append(p)            
    
    def position_iterator(self, p):
        count = 10
        for x in range(0, count + 1):
           yield array(p.position) + array(p.velocity) * (x / float(count))
           
    def check_collision(self, p):
        for pos in self.position_iterator(p):
            if (not p.cannon_fire and
                self.game.shield_dome.collision_check(p.position)):
                
                p.exploding = True
                p.position = pos # don't hit inside
                return

            if self.game.buildings.get(pos[0], pos[1]) == 1:
                p.exploding = True
                p.position = pos # don't hit inside
                return        
            
            for q in self._get_adjacent_projectiles(pos):
                if p is not q and (not p.cannon_fire or not q.cannon_fire):
                    radius_sum = q.radius + p.radius
                    radius_sum_sq = radius_sum * radius_sum            
                    diff_vec = array(pos) - array(q.position)
                    distance_squared = numpy.ma.innerproduct(diff_vec, diff_vec)
                    if distance_squared <= radius_sum_sq:
                        if not p.exploding and not p.cannon_fire:
                            self.game.score += 200                            
                        p.exploding = True
                        
                        if not q.exploding and not q.cannon_fire:
                            self.game.score += 200                        
                        q.exploding = True
                        
                        return

class ShieldDome(object):
    def __init__(self, resolution):
        self.size       = (resolution[0] * 4 / 5, resolution[1] / 3)
        self.resolution = resolution
        self.tmpsurface = pygame.Surface(self.resolution, flags=pygame.SRCALPHA)
        self.draw_rect  = (((self.resolution[0] - self.size[0]) / 2,
                            self.resolution[1] - self.size[1]),
                           ((self.resolution[0] + self.size[0]) / 2,
                            self.resolution[1] + self.size[1] * 2))
        self.bright = 0
        self.health = 10
        self.draw_to_tmpsurface()
        
    def draw_to_tmpsurface(self):
        opacity = 20 + self.health * 3
        if opacity > 150:
            opacity = 150

        edge_colour = (255, 120, 255, opacity + self.bright)
        
        pygame.draw.ellipse(self.tmpsurface, edge_colour,
                            ((0,0), (self.size[0], self.size[1] * 3)))
        border = 4
        pygame.draw.ellipse(self.tmpsurface, (200, 50, 200, opacity),
                            ((border,border), (self.size[0]-border * 2,
                             self.size[1] * 3 - border * 2)))
    
    def is_online(self):
        return self.health > 0
        
    def draw(self, surface):
        if self.is_online():
            self.draw_to_tmpsurface()
        
            surface.blit(self.tmpsurface, self.draw_rect[0])
            if self.bright > 0:
                self.bright -= 1
        
    def collision_check(self, (x,y)):
        if not self.is_online():
            return False
        else:
            x_centre = (self.draw_rect[0][0] + self.draw_rect[1][0]) / 2
            y_centre = (self.draw_rect[0][1] + self.draw_rect[1][1]) / 2
            width    = (self.draw_rect[1][0] - self.draw_rect[0][0])
            height   = (self.draw_rect[1][1] - self.draw_rect[0][1])

            x_diff = (x - x_centre) / (width / 2)
            y_diff = (y - y_centre) / (height / 2)
            
            hit = ((x_diff * x_diff) + (y_diff * y_diff)) <= 1
            if hit:
               self.bright += 30
               if self.bright > 70: self.bright = 70
               self.health -= 1
               
            return hit
            
class MissileDefenceGame(object):
    def reset(self):
        self.background = background.StarryBackground(self.resolution)                       
        self.physics = Physics(self)        
        self.cannon = DefenceCannon(centre=(self.resolution[0] / 2,
                                            self.resolution[1] - 99),
                                    game=self)
        self.buildings = Buildings(generate_city(self.resolution),
                                   self.resolution)
        self.firing = False
        self.fire_cycle = 0
        self.shield_dome = ShieldDome(self.resolution)
        self.shield_dome.health = 2
        self.missile_threshold = 0.01
        self.projectiles = []
        self.initial_buildings_sum = self.get_buildings_sum()
        self.buildings_sum = self.initial_buildings_sum
        self.score = 0
        
    def __init__(self):
        self.buildings_colour = (0,0,10)   # blue-black
        self.resolution = (640, 480)
        self.auto_mode = False
                
        pygame.init()
        pygame.surfarray.use_arraytype("numpy")        
        
#        self.score_font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self.score_font = pygame.font.Font(pygame.font.match_font("Monospace", True), 20)
        self.reset()
        
        self.screen = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption("Missile defence")

#                                              pygame.FULLSCREEN)
        
        self.buildings_surface = pygame.Surface(self.resolution, 0, 8)
        self.buildings_surface.set_palette(((0,0,0), self.buildings_colour))
        self.buildings_surface.set_colorkey(0, pygame.RLEACCEL)
        
    def generate_missile(self):
        p = projectiles.Missile(position=(uniform(-500, self.resolution[0] + 500), -50),
                                velocity=(uniform(-3, 3), 
                                          uniform(2, 7)))
        
        count = 0
        while p.position[1] < -20 and count < 100:
            p.apply_physics(self.physics, self.buildings)
            count += 1
            
        return p

    def handle_events(self):
        force_fire = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            elif event.type == pygame.KEYDOWN and event.key == ord("q"):
                self.done = True
            elif event.type == pygame.KEYDOWN and event.key == ord("s"): # screenshot
                pygame.image.save(self.screen, "screenshot.png")
            elif event.type == pygame.KEYDOWN and event.key == ord("a"): # auto mode
                self.auto_mode = not self.auto_mode
            elif event.type == pygame.KEYDOWN and event.key == ord("r"): # reset
                self.reset()
            elif event.type == pygame.KEYDOWN and event.key == ord("d"):
                self.shield_dome.health += 20
            elif event.type == pygame.MOUSEBUTTONDOWN:
                force_fire  = True # fire event if there was a mouse up too
                self.fire_cycle = 0
                self.firing = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.firing = False
       
        stuff_nearby = any(
            size_squared(array(p.position) - array(self.cannon.centre)) < p.radius * p.radius  
            for p in self.projectiles)
            
        if not self.auto_mode:
            self.cannon.target = array(pygame.mouse.get_pos())

        if not stuff_nearby:
            if self.auto_mode and self.cannon.can_fire():

                valid_targets = [p for p in self.projectiles if
                                 p.position[0] > 0 and p.position[1] > 0 and
                                 p.position[0] < self.resolution[0] and
                                 p.position[1] < self.resolution[1] - 300 and
                                 p.velocity[1] > 0 and not p.exploding]
                if len(valid_targets) > 0:
                    target = random.choice(valid_targets)
                    target_pos = array(target.position) + array(target.velocity) * 4
                    self.cannon.fire(target_pos)
                    self.cannon.target = target_pos
                    
            elif self.firing or force_fire:            
                self.cannon.fire(pygame.mouse.get_pos()) 
                
    def get_buildings_sum(self):
        # restart if most of the buildings are destroyed and no explosions in progress
        sum = 0
        for y in range(self.resolution[1] - 100, self.resolution[1]):
            sum += numpy.ma.sum(self.buildings.pixeldata[y])
        return sum
        
    def draw(self, intro=False):
        self.background.draw(self.screen)
        pygame.surfarray.blit_array(self.buildings_surface,
                                    self.buildings.pixeldata)
        
        self.screen.blit(self.buildings_surface, (0,0))

        self.shield_dome.draw(self.screen)
                
        for p in self.projectiles:
            p.draw(self.screen)
            
        self.cannon.draw(self.screen)
        
        # draw score
        score_surf = self.score_font.render(format(self.score, "08"), True, (255,255,255))
        self.screen.blit(score_surf, (30, 30))
        pygame.display.flip()
    
    
    
    def apply_physics(self):
        self.physics.update_location_cache()
        
        projectiles_keep = []  
        # process projectiles
        for p in self.projectiles:
            p.apply_physics(self.physics, self.buildings)
            
            # keep any projectiles that aren't destroyed/off-screen
            if not p.is_garbage(self.resolution):
               projectiles_keep.append(p)               
        self.projectiles = projectiles_keep        
        self.buildings.apply_physics()   
        self.cannon.apply_physics()
        
                
    def run(self):                
        clock = pygame.time.Clock()        

        self.projectiles = [] 
        tick_count = 0
        self.done  = False

        # Introduction
        
        #while tick_count < 30
        #    clock.tick(30)
        #    
        #    tick_count += 1
        #    self.apply_physics()
        #     self.draw()
                    
        while not self.done:
            clock.tick(30)
            self.handle_events()
                        
            tick_count += 1

            if tick_count % 100 == 0:
                self.background.darken()        
                
            if tick_count % 30 == 0:
                self.buildings_sum   = self.get_buildings_sum()
                if float(self.buildings_sum) / self.initial_buildings_sum < 0.2:
                    self.reset()
             
                self.score += 100
                           
            # randomly add more projectiles
            self.missile_threshold += 0.0001
            
            m = self.missile_threshold
            while m > 0:
                m -= random.random() 
                if m > 0:
                    self.projectiles.append(self.generate_missile())
            
            self.apply_physics()
            
            self.draw()
        
        pygame.quit()           
            

if __name__ == "__main__":
    game = MissileDefenceGame()
    game.run()
