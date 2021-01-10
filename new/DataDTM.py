'''
create one raster DTM (.tif) out of many tiles

todo:
* check if coordinate system is the same

* write algorithm to merge pairs together
'''

from osgeo import gdal
import pandas as pd
import os, sys, gdal
import numpy as np

class DataDTM(object):

    def __init__(self, input_dir, output_file):

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
            if not os.path.exists(os.path.join(self.input_dir, 'dtm_info.csv')):
                print("file 'dtm_info.csv' not found")
                print("creating file 'dtm_info.csv' ...")
                # create dtm_info.csv
                self.create_index()
            # set index (dataframe with all the information)
            print("reading file 'dtm_info.csv' ...")
            self.index = self.read_index()

            self.extend = 0,0,0,0
            print("dtm initialised")

        self.output_file = output_file


    def set_extend_by_raster(self, file_path):
        '''
        get extend of raster
        '''
        src = gdal.Open(file_path)
        ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)

        self.extend = ulx,uly,lrx,lry


    def set_extend_by_coordinates(self, ulx, uly, lrx, lry):
        self.extend = ulx,uly,lrx,lry


    def get_extend(self):
        '''
        get extend of raster
        '''
        return(self.extend)


    def extract_extend(self, file_path):
        '''
        extract extend out of raster
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
                ulx,uly,lrx,lry = self.extract_extend(self.input_dir + filename)
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
        t_ulx, t_uly, t_lrx, t_lry = self.extend
        # filter relevant tiles for extend
        idx_fil = self.index[(t_ulx <= self.index['lrx']) &
                             (t_lrx >= self.index['ulx']) &
                             (t_uly >= self.index['uly']) &
                             (t_lry <= self.index['lry'])]

        # set path to text file with all tif file paths to be merged
        merge_list_path = os.path.join(self.input_dir, 'dtm_merge_list.txt')
        # create txt file with all tif files needed
        with open(merge_list_path, 'w+') as f:
            for name in idx_fil['filename']:
                f.write(os.path.join(self.input_dir, name) + '\n')

        # create string containing bash command
        cmd = "gdal_merge.py -ot Float32 -of GTiff -o {} --optfile {}".format(self.output_file, merge_list_path)

        # execute bash command
        os.system(cmd)

        print("Tif files merged")
