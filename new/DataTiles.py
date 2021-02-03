'''
create one raster DTM (.tif) out of many tiles

todo:
* check if coordinate system is the same

* write algorithm to merge pairs together
'''

from osgeo import gdal
import pandas as pd
import geopandas
import os, sys, gdal
import numpy as np
import multiprocessing as mp

class DataTiles(object):

    def __init__(self, path_grid, path_out_dir):

        # check if output path is valid
        if os.path.exists(path_out_dir):
            print("provided output path found")
            # check if path contains / at the end
            if path_out_dir[-1] == '/':
                self.path_out_dir = path_out_dir
            else:
                self.path_out_dir = path_out_dir + '/'
        else:
            print("provided output path does not exist!")

        # check if grid file extists
        if os.path.isfile(path_grid):
            print("provided grid file found")
            self.grid = geopandas.read_file(path_grid)
            self.grid_cut = self.grid
        else:
            print("provided grid file does not exist!")


    def get_extend(self, raster_path):
        '''
        Get raster's extend
        '''
        src = gdal.Open(raster_path)
        ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)
        return(ulx,uly,lrx,lry)


    def clip_grid(self, extend=None ,raster_path=None):
        '''
        Clips grid to extend
        '''
        if extend:
            ulx,uly,lrx,lry = extend
        elif raster_path:
            ulx,uly,lrx,lry = self.get_extend(raster_path)

        self.grid_cut = self.grid[(ulx <= self.grid['left']) &
                           (uly >= self.grid['top']) &
                           (lrx >= self.grid['right']) &
                           (lry <= self.grid['bottom'])]


    def make_tiles(self, path_raster, typ, processes=1):
        '''
        Utalizes provided grid to clip raster into tiles.
        Input:
            raster(str): path to raster
            type(str): 'ortho' | 'dsm' | 'dtm' | 'slope'
        Return:
            raster_tile
        '''
        if not os.path.isfile(path_raster):
            print("provided raster file does not exist!")

        elif typ not in {'ortho', 'dsm', 'dtm', 'slope'}:
            print("provided type does not exist!")
            print("please use one of these types:")
            print("   'ortho' | 'dsm' | 'dtm' | 'slope'")

        else:
            # check ang create folder if needed
            if not os.path.exists(os.path.join(self.path_out_dir, typ)):
                print('creating folder')
                os.mkdir(os.path.join(self.path_out_dir, typ))

            print("=========================================")
            print("starting creation of tiles")
            # get indices
            ids = self.grid_cut['id'].to_numpy()
            percent = 0
            # loop over all records
            for i, index in enumerate(ids):
                if i % (ids.shape[0] // 10) == 0:
                    os.system( 'cls' )
                    print("Progress: {}%".format(percent))
                    percent += 10
                # get extend
                extend = self.grid_cut.loc[index,'geometry'].bounds
                # construct path of output file
                path_out = self.path_out_dir + "/{}/tile_{}_{}.tif".format(typ, typ, index)
                # construct command
                bashCommand = "gdal_translate -projwin {} {} {} {} -a_nodata 0.0 -of GTiff {} {}".format(extend[0], extend[3], extend[2], extend[1], path_raster, path_out)
                # execute command
                os.system(bashCommand)

            print("finished creation of tiles")
            print("=========================================")


##################################################################
# test multiprocessing
    def command(self, index):
        typ = self.typ
        # get extend
        extend = self.grid_cut.loc[index,'geometry'].bounds
        # construct path of output file
        path_out = self.path_out_dir + "/{}/tile_{}_{}.tif".format(typ, typ, index)
        # construct command
        bashCommand = "gdal_translate -projwin {} {} {} {} -a_nodata 0.0 -of GTiff {} {}".format(extend[0], extend[3], extend[2], extend[1], path_raster, path_out)

        print(bashCommand)
        # execute command
        os.system(bashCommand)

        return index

    def collect_result(self, result):
        self.results.append(result)


    def make_tiles_m(self, path_raster, typ, processes=1):
        '''
        Utalizes provided grid to clip raster into tiles.
        Input:
            raster(str): path to raster
            type(str): 'ortho' | 'dsm' | 'dtm' | 'slope'
        Return:
            raster_tile
        '''
        if not os.path.isfile(path_raster):
            print("provided raster file does not exist!")

        elif typ not in {'ortho', 'dsm', 'dtm', 'slope'}:
            print("provided type does not exist!")
            print("please use one of these types:")
            print("   'ortho' | 'dsm' | 'dtm' | 'slope'")

        else:
            # check ang create folder if needed
            if not os.path.exists(os.path.join(self.path_out_dir, typ)):
                print('creating folder')
                os.mkdir(os.path.join(self.path_out_dir, typ))

            self.typ = typ
            self.results = []
            pool = mp.Pool(processes)

            print("=========================================")
            print("starting creation of tiles")
            # get indices
            self.ids = self.grid_cut['id'].tolist() #.to_numpy()
            print(self.ids)
            result = pool.map_async(self.command, self.ids, callback=self.collect_result)

            print("finished creation of tiles")
            print("=========================================")
