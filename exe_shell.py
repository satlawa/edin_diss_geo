import os

raster = '/home/philipp/Data/edin_diss/rasterized_3.tif'
vector = '/home/philipp/Data/edin_diss/dringlich.shp'
com = 'gdal_rasterize'
opt = ' -l dringlich -a Nutzdringl -tr 0.2 0.2 -a_nodata 0.0 -te 398455.8400000036 335265.01000000164 413826.6400000006 354796.4200000018 -ot Byte -of GTiff '
os.system(com + opt + vector + ' ' + raster)
