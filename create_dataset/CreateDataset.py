import numpy as np
import pandas as pd
import h5py

from osgeo import gdal
from osgeo import gdal_array
from osgeo import osr
from osgeo import gdalconst

from glob import glob
#from os import listdir
#from os.path import splitext
import logging
import os

class CreateDataset(object):

    def __init__(self, input_dir):
        self.input_dir = input_dir



    def find_files(self):
        """

        """
        ids_ortho = []
        ids_ground_truth = []

        sufix_ortho = 'ortho/'
        sufix_gt = 'ground_truth/'

        # loop over all files found in directory
        for file in os.listdir(dir_img+sufix_ortho):
            # create path to ground truth
            path_gt = dir_img + sufix_gt + 'tile_ground_truth' + file[file.rfind('_'):]
            # if file is .tif and the ID is alo found in the grooound truth dictonary
            if file[file.rfind('.'):] == '.tif' and os.path.isfile(path_gt):
                # add path to lists
                ids_ortho.append(dir_img + sufix_ortho + file)
                ids_ground_truth.append(path_gt)


    def tif2array(input_file, dtype=np.uint8):
        """
        read GeoTiff and convert to numpy array.
        inputs:
            input_file (str) : the name of input GeoTiff file.
        return:
            image(np.array) : image for each bands
            dataset : for gdal's data drive.
        """
        dataset = gdal.Open(input_file, gdal.GA_ReadOnly)

        if dataset is None:
            return None

        # Allocate our array using the first band's datatype
        image_datatype = dataset.GetRasterBand(1).DataType
        image = np.zeros((dataset.RasterYSize, dataset.RasterXSize, dataset.RasterCount),
                         dtype=dtype)

        # Loop over all bands in dataset
        for b in range(dataset.RasterCount):
            # Remember, GDAL index is on 1, but Python is on 0 -- so we add 1 for our GDAL calls
            band = dataset.GetRasterBand(b + 1)
            # Read in the band's data into the third dimension of our array
            image[:, :, b] = band.ReadAsArray()#buf_type=gdalconst.GDT_Byte)

        #image = image[2:-2,2:-2,:]

        return image


    def cut_img(self, img, x, y):
        """
        cut input numpy array to the width(x) and height(y)
        inputs:
            img (np.array) : image as numpy array
            x (int) : target width
            y (int) : target height
        return:
            img (np.array) : image cutted to the target width(x) and height(y)
        """
        # set pixel sizes
        x_i, y_i, z_i = img.shape
        # dict to store the sliceing information
        d = {}

        for var, var_i, key in [(x, x_i, 'x'), (y, y_i, 'y')]:
            # if image pixel size is grater than the target pixel size
            if (var_i > var):
                # if even cut same amount of pixels from both sides
                if var_i%2 == 0:
                    sub = int(var_i/2 - var/2)
                    d[key+'0'] = sub
                    d[key+'1'] = sub
                # if odd cut 1 pixel more from right/bottom
                else:
                    sub = int(var_i/2 - var/2)
                    d[key+'0'] = sub
                    d[key+'1'] = sub + 1
            else:
                print('image too small')
        # cut image
        img = img[d['x0']:-d['x1'],d['y0']:-d['y1']]

        return img


    # pass ids_ortho, ids_dsm, ids_dtm, ids_slope
    def create_array(self, ids, dtype):
        """
        creates numpy array with all images stacked
        inputs:
            ids (list) : list of paths to image files
            dtype (dtype) : dtype for storing the loaded image
        return:
            arr (np.array) : numpy array containing all the images stacked
        """
        # list to store the loaded images
        imgs = []

        if dtype == np.uint8:
            # add all
            for i in ids:
                # load image to numpy array
                img = tif2array(i, np.uint8)
                # cut into right shape
                img = self.cut_img(img, 512, 512)
                # append array to list
                imgs.append(img)

            # convert list with arrays to numpy array
            arr = np.stack(imgs, axis=0)
            print(arr.shape)

            # calculate mean
            #mean = np.mean(arr, dtype='float32')
            # calculate standard deviation
            #std = np.std(arr, dtype='float32')

        else:
            # add all
            for i in ids:

                # load image to numpy array
                img = tif2array(i, np.float32)
                # cut into right shape
                img = cut_img(img, 512, 512)
                # append array to list
                imgs.append(img)
                x, y, z = img.shape

            # convert list with arrays to numpy array
            arr = np.stack(imgs, axis=0)
            arr[arr < 0] = np.nan
            print(arr.shape)

            # calculate mean
            #mean = np.nanmean(arr, dtype='float32')
            # calculate standard deviation
            #std = np.nanstd(arr, dtype='float32')
            # convert nan to 0
            arr = np.nan_to_num(arr)

        # normalize data
        #arr = (arr - mean) / std

        return arr#, mean, std
