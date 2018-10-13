# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-10-30 16:10:58
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2018-01-19 18:07:33

#python
import math

#Robolcd
from RoboLCD import roboprinter

class circle_plotter(object):
    '''Circle Plotter will get the center of the bed on the current printer and return a GCODE 
       script that will make a circle at the given radius'''
    def __init__(self):
        super(circle_plotter, self).__init__()
        self.get_bed_center()
        

    def get_bed_center(self):
        #get bed dimensions
        bed_x = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','width'])
        bed_y = roboprinter.printer_instance._settings.global_get(['printerProfiles','defaultProfile', 'volume','depth'])

        #calculate final positions (x and y are the center of the print bed)
        self.bed_x = float(bed_x) / 2.0
        self.bed_y = float(bed_y) / 2.0

    def point_in_circle(self, radius, angle):
        
        #find the point at a given radius and angle
        x = self.bed_x + radius * math.cos(angle)
        y = self.bed_y + radius * math.sin(angle)
    
        return [x,y]

    def get_step_ratio(self, radius):
        ''' 
        This function exists to preserve detail when making large or small circles. 
        With a fixed step length as you go bigger the circle will become less defined and as you go smaller the circle will be overdefined. 

        circumference = 578.053048261
        step = 0.01
        points = 628.318530718
        
        points per mm = 1.086956522
        
        formula for finding step
        points = circumference x ppm
        step = (2 * pi) / points'''

        circ = (2.0 * math.pi) * radius
        points = circ * 1.086956522 # this magic number represents the ratio of points per mm
        step = (2.0 * math.pi) / points 

        return step
    
    def make_circle_points(self, radius):
        points = []
        #for each angle in the range 0 - 2*pi radians get the xy coordinate
        for x in self.frange(0, stop=2 * math.pi, step=self.get_step_ratio(radius)):
            point = self.point_in_circle(radius, x)
            points.append(point)
        
        #find the distance between the first two points as the distance between all points should be the same
        distance = self.distance_between_points(points[0], points[1])
        extrusion_amount = distance * (1.0/12.0) #conversion for 1mm of extrusion for 12 mm of bed length
        e_length = extrusion_amount

        script = []
        #make a GCODE script that convers the points into gcode with an X, Y, and E value
        for p in points:
            script.append("G1 X" + str(p[0]) + " Y" + str(p[1]) + " E" + str(e_length) + " F2000")
            e_length += extrusion_amount

        #return a GCODE script with a starting point
        circle = {
            'start_point': points[0],
            'end_e': e_length,
            'script': script,

        }

        return circle
    
    def distance_between_points(self, p1, p2):
        distance = 0
        
        #this calculates the distance between the two given points.
        pow_2_x = math.pow((p1[0] - p2[0]), 2.0)
        pow_2_y = math.pow((p1[1] - p2[1]), 2.0)
    
        add_xy = pow_2_x + pow_2_y
    
        distance = math.sqrt(add_xy)
    
        return distance
    
    def frange(self, start, stop = None, step = 1):
        """frange generates a set of floating point values over the 
        range [start, stop) with step size step
    
        frange([start,] stop [, step ])"""
    
        if stop is None:
            for x in range(int(math.ceil(start))):
                yield x
        else:
            # create a generator expression for the index values
            indices = (i for i in range(0, int((stop-start)/step)))  
            # yield results
            for i in indices:
                yield start + step*i

