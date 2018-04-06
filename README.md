# ArcToolbox Repo
# Download toolbox (tbx) and open in ArcGIS
""" 
Creator: M.Schaefer, GIS Manager, University of Portsmouth
Title: Point to point comparison over time
Purpose: Monitor change over time for uniquely identified points.
Data Requirements: A list of identified points that have been measured over 
    multiple surveys. This program will work out the distance, 
    azimuth and change in height between every instance of a point with
    the same ID.    
    Input is a csv file with no heading:
        year (or survey ID), id, x, y, z
            e.g. 2008,FEAT01,449850.6,75308.663,19.9
Required modules: sys, os, csv, pandas, numpy, arcpy
Python version: 2, 3       
ESRI: ArcGIS Desktop, ArcGIS Pro
Data output: Two shapefiles, point and line. Two csv files, one with movement 
    between surveys and one with total movement between first and last survey.
"""
