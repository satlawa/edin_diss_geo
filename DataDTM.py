'''
create one raster DTM (.tif) out of many tiles

todo:
* check if coordinate system is the same
'''

from osgeo import gdal
import sys
import os
import pandas as pd
import os, sys, gdal
from gdalconst import *
import numpy as np
import math

class DataDTM(object):

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


    def get_extend(self, file_path):
        '''
        get extend of raster
        '''
        src = gdal.Open(file_path)
        ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)
        return(ulx,uly,lrx,lry)


    def create_index(self):
        '''
        creates a csv file with the information:
        | filename | x (tile row number) | y (tile column number) |
        | ulx (upper left x-coordinate)  | uly (upper left y-coordinate)  |
        | lrx (lower right x-coordinate) | lry (lower right y-coordinate) |
        from the raster tiles
        '''
        # set directory from path string
        directory = os.fsencode(self.input_dir)

        # create llist for storing the extend of every tile
        tiles_extend = []

        # loop over all filenames
        for file in os.listdir(directory):
            # get filename
            filename = os.fsdecode(file)
            # if the filename contains .tif -> it is a raster file
            if filename.endswith(".tif"):
                # get extend (upper left and lower right coodrdinates)
                ulx,uly,lrx,lry = self.get_extend(self.input_dir + filename)
                # get tile number out of filename
                pos = filename.replace('.tif','').split('-')
                # append to list
                tiles_extend.append([filename, pos[0], pos[1], ulx, uly, lrx, lry])

        # create dataframe out of list with extend data
        df = pd.DataFrame(tiles_extend)
        # name columns
        df.columns =['filename', 'y', 'x','ulx','uly','lrx','lry']
        # sort dataframe on filename
        df = df.sort_values('filename')
        # save as csv
        df.to_csv(self.input_dir + 'dtm_info.csv')


    def read_index(self):
        '''
        reads a csv file with the information:
        | filename | x (tile row number) | y (tile column number) |
        | ulx (upper left x-coordinate)  | uly (upper left y-coordinate)  |
        | lrx (lower right x-coordinate) | lry (lower right y-coordinate) |
        about all raster tiles
        '''
        # read csv into dataframe
        df = pd.read_csv(self.input_dir + 'dtm_info.csv', index_col=False)
        # return index (dataframe with all the information)
        return df[['filename', 'y', 'x','ulx','uly','lrx','lry']]


    def create_dtm(self):
        # get extend
        t_ulx, t_uly, t_lrx, t_lry = self.shape
        # filter relevant tiles for extend
        idx_fil = self.index[(t_ulx <= self.index['lrx']) & (t_lrx >= self.index['ulx']) & (t_uly >= self.index['uly']) & (t_lry <= self.index['lry'])]
        # get relevant colum numbers
        idx_fil_y = idx_fil['y'].unique()

        column_list = []

        for y in idx_fil_y:
            # filter column
            index_y = self.index[self.index['y'] == y]
            # fliter relevant row tiles
            index_y_x = index_y[(t_lry <= index_y['uly']) & (t_uly >= index_y['lry'])]
            # set pathout as the output path of the merged tiles
            pathout = self.output_dir + 'col_' + str(y) + '.tif'
            # merge tilse in column
            self.create_column(index_y_x['filename'].to_list(), pathout)

            column_list.append(pathout)

        # set pathout as the output path of the merged tiles
        pathout = self.output_dir + 'dtm_final.tif'
        # merge tilse in column
        self.create_column(column_list, pathout)

        print('end')


    def create_column(self, index_y_x, pathout):
        # set path1 as the path to the first tile
        path1 = self.input_dir + index_y_x[0]

        for i in range(1, len(index_y_x)):
            # set path2 as the path to the next tile
            path2 = hd_path + index_y_x[i]
            # merge two tiles
            self.mosaic(path1, path2, pathout)
            # set path1 to the output path
            path1 = pathout

        print('tile column |' + str(pos) + '| finished')


    def mosaic(self, path1, path2, pathout):
        '''
        merge two raster tiles together into one raster tile
        '''
        # register all of the GDAL drivers
        gdal.AllRegister()

        # read in doq1 and get info about it
        ds1 = gdal.Open(path1)
        band1 = ds1.GetRasterBand(1)
        rows1 = ds1.RasterYSize
        cols1 = ds1.RasterXSize

        # get the corner coordinates for doq1
        transform1 = ds1.GetGeoTransform()
        minX1 = transform1[0]
        maxY1 = transform1[3]
        pixelWidth1 = transform1[1]
        pixelHeight1 = transform1[5]
        maxX1 = minX1 + (cols1 * pixelWidth1)
        minY1 = maxY1 + (rows1 * pixelHeight1)

        # read in doq2 and get info about it
        ds2 = gdal.Open(path2)
        band2 = ds2.GetRasterBand(1)
        rows2 = ds2.RasterYSize
        cols2 = ds2.RasterXSize

        # get the corner coordinates for doq2
        transform2 = ds2.GetGeoTransform()
        minX2 = transform2[0]
        maxY2 = transform2[3]
        pixelWidth2 = transform2[1]
        pixelHeight2 = transform2[5]
        maxX2 = minX2 + (cols2 * pixelWidth2)
        minY2 = maxY2 + (rows2 * pixelHeight2)

        # get the corner coordinates for the output
        minX = min(minX1, minX2)
        maxX = max(maxX1, maxX2)
        minY = min(minY1, minY2)
        maxY = max(maxY1, maxY2)

        # get the number of rows and columns for the output
        cols = int(math.ceil((maxX - minX) / pixelWidth1))
        rows = int(math.ceil((maxY - minY) / abs(pixelHeight1)))

        # compute the origin (upper left) offset for doq1
        xOffset1 = int((minX1 - minX) / pixelWidth1)
        yOffset1 = int((maxY1 - maxY) / pixelHeight1)

        # compute the origin (upper left) offset for doq2
        xOffset2 = int((minX2 - minX) / pixelWidth1)
        yOffset2 = int((maxY2 - maxY) / pixelHeight1)

        # create the output image
        driver = ds1.GetDriver()
        dsOut = driver.Create(pathout, cols, rows, 1, band1.DataType)
        bandOut = dsOut.GetRasterBand(1)

        # read in doq1 and write it to the output
        data1 = band1.ReadAsArray(0, 0, cols1, rows1)
        bandOut.WriteArray(data1, xOffset1, yOffset1)

        # read in doq2 and write it to the output
        data2 = band2.ReadAsArray(0, 0, cols2, rows2)
        bandOut.WriteArray(data2, xOffset2, yOffset2)

        # compute statistics for the output
        bandOut.FlushCache()
        stats = bandOut.GetStatistics(0, 1)

        # set the geotransform and projection on the output
        geotransform = [minX, pixelWidth1, 0, maxY, 0, pixelHeight1]
        dsOut.SetGeoTransform(geotransform)
        dsOut.SetProjection(ds1.GetProjection())

        # build pyramids for the output
        #gdal.SetConfigOption('HFA_USE_RRD', 'YES')
        #dsOut.BuildOverviews(overviewlist=[2,4,8,16])
