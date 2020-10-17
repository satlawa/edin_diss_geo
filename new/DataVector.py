'''
create

todo:
    test
'''

import sys
import os

import geopandas as gpd
import pandas as pd

from osgeo import gdal
from pyproj import CRS

class DataVector(object):

    def __init__(self, path_wo, year):

        self.wo_vector = gpd.read_file(path_wo, layer="Waldorte")
        # add id
        self.add_id_gis()
        # add year the data is valid from
        self.wo_vector['year_data'] = year
        self.year = year

        self.sap_tax = None


    def change_crs(self, crs='std'):

        if crs == 'std':
            # define crs of orthophotos (Lambert)
            new_crs = CRS.from_user_input('PROJCS["Austria_Lambert",GEOGCS["GCS_BESSEL_AUT",DATUM["D_BESSEL_AUT",SPHEROID["Bessel_1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["latitude_of_origin",47.5],PARAMETER["central_meridian",13.333333333],PARAMETER["standard_parallel_1",46],PARAMETER["standard_parallel_2",49],PARAMETER["false_easting",400000],PARAMETER["false_northing",400000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]')

        # reproject to new crs
        self.wo_vector = self.wo_vector.to_crs(new_crs)


    def merge_sap(self, path, kind = 'all'):
        '''
        GIS & SAP - merde GIS-data with SAP-data on 'id'
        in:     path (string) - path to SAP-data
                kind (string) - all (all stands), wwie (Wirtschaftswald in Ertrag)
        '''
        # read SAP data from path
        self.read_sap(path)
        # get filter STOE information
        sap_tax_stoe = self.filter_sap_stoe()
        # merge GIS-data and SAP-data on 'id'
        self.wo_vector = self.wo_vector.merge(sap_tax_stoe, on='id')

        if kind == 'wwie':
            # filter -> just Wirtschaftswald in Ertrag
            self.wo_vector = self.wo_vector[(self.wo_vector['Bwirt']=='W') & (self.wo_vector['Esit']=='I')]


    def read_sap(self, path):
        '''
        SAP - read metadata about SAP-data, call read fuction, set class data
        in:     path (string) - path to directory where SAP-data is stored
        '''
        # read metadata
        sap_tax = pd.read_csv(path + "/sap_meta.csv", sep=',')
        # filter metadata for a given year
        sap_tax_year = sap_tax[['FB', self.year]]
        # create array with all TOs for a given year
        tos = sap_tax[year_data].unique()
        # load data from files
        self.sap_tax = self.get_sap_tax_data(tos, sap_tax_year)
        # add necessary data
        self.add_id_sap()


    def get_sap_tax_data(self, tos, sap_tax_year):
        '''
        SAP - obtain file names with data, read data and concatonate
        in:     tos (numpy array) - list of TOs
                sap_tax_year (DataFrame) - lookup table to get the Forstbetrieb
        out:    sap_tax (DataFrame) - concatinated information from all TOs
        '''
        # create list for keeping loaded data
        sap_tax_tos = []

        for to in tos:
            # find Forstbetrieb for the giveb Teiloperat
            fb = sap_tax_year.loc[sap_tax_year[year_data] == to, 'FB'].unique()[0]
            # create path to file
            path = sap_path + "/" + str(fb) + "/TO_" + str(to) + ".XLS"
            # append data read from the file
            sap_tax_tos.append(pd.read_csv(path, sep='\t', encoding = "ISO-8859-1", decimal=',', error_bad_lines=False, na_values=0))

        return pd.concat(sap_tax_tos)


    def add_id_gis(self):
        '''
        GIS - in SAP-data create a unique identifier for merging with the SAP-data
        * 'id'= unique identifier
        '''
        # create id
        self.wo_vector['id'] = self.wo_vector['FB_KURZ'].astype(str) + self.wo_vector['FR_KURZ'].astype(str) + \
        self.wo_vector['ABTEILUNG'].astype(str) + self.wo_vector['UNTERABTEILUNG'].astype(str)


    def add_id_sap(self):
        '''
        SAP - in SAP-data create a unique identifier for merging with the GIS-data
        * 'id'= unique identifier
        * 'year_to_start' = year the TO is starting to be active
        * 'year_to_end' = year the TO is ending to be active
        '''
        # create id
        self.sap_tax['id'] = self.sap_tax['Forstbetrieb'].astype(str) + \
        self.sap_tax['Forstrevier'].astype(str) + self.sap_tax['Abteilung'].astype(str) + \
        self.sap_tax['Unterabteil.'].astype(str) + self.sap_tax['Teilfl.'].astype(str)

        # create year the TO started and ended
        self.sap_tax['year_to_start'] = self.sap_tax['Beg. Laufzeit'].str[-4:].astype(int)
        self.sap_tax['year_to_end'] = self.sap_tax['Ende Laufzeit'].str[-4:].astype(int)


    def filter_sap_stoe(self):
        '''
        SAP - filter SAP-data for stand (STOE) information and renaming the attributes
        out:    sap_tax_stoe (DataFrame)
        '''
        # filter information about the stand
        sap_tax_stoe = self.sap_tax.loc[self.sap_tax['Schichtanteil'] == 0, ['id', 'Forstbetrieb', 'Forstrevier', \
        'Abteilung', 'Unterabteil.', 'Teilfl.', 'Ertragssituation', 'Bewirtschaftungsform', \
        'Schutzwaldkategorie', 'Standorteinheit', 'Vegetationstyp', 'Wuchsgebiet', 'year_to_start', \
        'year_to_end']]

        # rename columns
        sap_tax_stoe.rename(columns = {'Forstbetrieb':'FB', 'Forstrevier':'FR', 'Abteilung':'Abt', \
                               'Unterabteil.':'UAbt', 'Teilfl.':'TFl', 'Ertragssituation':'Esit', \
                               'Bewirtschaftungsform':'Bwirt', 'Schutzwaldkategorie':'SWKat', \
                               'Standorteinheit': 'Stoe', 'Vegetationstyp' : 'Vtyp', 'Wuchsgebiet': 'Wgeb', \
                               'year_to_start' : 'year_start', 'year_to_end' : 'year_end'}, inplace = True)

        # fill nan
        sap_tax_stoe = sap_tax_stoe.fillna(0)
        sap_tax_stoe['Stoe'] = sap_tax_stoe['Stoe'].astype(int)

        return sap_tax_stoe


    def save(self, path):
        # save to file
        self.wo_vector.to_file(path)
