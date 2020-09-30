'''
create one raster DTM (.tif) out of many tiles

todo:
* check if coordinate system is the same

* write algorithm to merge pairs together
'''

import geopandas as gpd
import pandas as pd
from osgeo import gdal
import sys
import os

import multiprocessing as mp

class DataGrid(object):

    def __init__(self, input_dir, output_dir, shape):

        # check if path to the dtm tiles is valid
        if not os.path.exists(input_dir):
            print("provided path does not exist!")

        else:
            print("provided path found")
            # check if path contains / at the end
            if input_dir[-1] == '/':
                self.input_dir = input_dir
            else:
                self.input_dir = input_dir + '/'

            # check if dtm_info.csv extists (contains info about tiles)
            if not os.path.exists(self.input_dir + 'dtm_info.csv'):
                print("file 'dtm_info.csv' not found")
                print("creating file 'dtm_info.csv' ...")
                # create dtm_info.csv
                self.create_index()
            # set index (dataframe with all the information)
            print("reading file 'dtm_info.csv' ...")
            self.index = self.read_index()

            self.shape = shape
            print("dtm initialised")

        self.output_dir = output_dir


    def create_grid(self, extend, length, crs):
        '''
        create grid (vector - polygons) within extend
        in:
        out: GeoDataFrame with grid
        '''

        minx, miny, maxx, maxy = extend

        polys = []

        # loop over coordinates
        for col in np.arange(minx, maxx, length):
            for row in np.arange(maxy, miny, -length):
                # create polygon and append to list
                polys.append(Polygon ([(col, row), (col+length, row), (col+length, row-length), (col, row-length), (col, row)]))

        # create and return GeoDataFrame
        return(gpd.GeoDataFrame({'id': range(len(polys)), 'geometry': polys}, crs=crs))
