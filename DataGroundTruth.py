'''
create ground truth (raster) out of a shape (vector) file

requirements:
    * installed bash
    * installed gdal

todo:
    test
'''

import sys
import os

import geopandas as gpd
import pandas as pd

from osgeo import gdal
#from pyproj import CRS

class DataGroundTruth(object):

    #def __init__(self):


    def get_extend(self, path):
        db_data = gpd.read_file(path)

    def create_gt(self, path, name_in, name_layer, name_out, extend, pixel_res=1):
        '''
            creates a raster out of vector data with the help of gdal_rasterize
            output:
                GTiff
        '''

        print('creating ground truth ...')

        # create string for bash command
        bashCommand = "gdal_rasterize -l " + name + " -a " + name_layer + \
        " -tr " + str(pixel_res) + " " + str(pixel_res) + " -a_nodata 0.0 -te " + \
        str(c0) + " " + str(c1) + " " + str(c2) + " " + str(c3) + \
        " -ot Byte -of GTiff " + path_shp + " " + path_out

        # execute bash command
        os.system(bashCommand)

        print('finished')
