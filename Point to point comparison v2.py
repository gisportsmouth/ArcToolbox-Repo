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

import sys
import os
import arcpy
import csv
import pandas as pd
import numpy as np
import itertools

def proc_main():
    """ 
    Main try-except-finally block  with error handling
    """
    arcpy.AddMessage('Starting...')
    try:
        #Run actual functionality
        proc_run()
    except Exception as e:
        arcpy.AddMessage  ('Error: {}'.format(str(e)))
    finally:
        arcpy.AddMessage ('Completed')
   
def proc_run():     
    """ 
    Main program functionality
    """  
    # Overwrite pre-existing files
    arcpy.env.overwriteOutput = True		
    in_file = arcpy.GetParameterAsText(0)
    proj = arcpy.GetParameterAsText(1)
    #
    arcpy.AddMessage('Processing: {}'.format(in_file))
    #file management
    fsplit = func_pathsplit(in_file)
    survey_comp = os.path.join(fsplit[0], fsplit[2] + '_InterSurveyData.csv')
    total_comp = os.path.join(fsplit[0], fsplit[2] + '_TotalSurveyData.csv')
    shpoutput = os.path.join(fsplit[0], fsplit[2] + '_MovementLine.shp')
    #create line shp
    arcpy.AddMessage('Creating: {}'.format(shpoutput)) 
    arcpy.CreateFeatureclass_management(fsplit[0], 
                                        fsplit[2] + '_MovementLine.shp', 'POLYLINE', '',
                                        'DISABLED', 'ENABLED', proj)
    #create point shapefile from input     
    proc_point(in_file, proj)
    #process movement
    header = ('timestamp', 'id', 'x', 'y', 'z')
    df = pd.read_csv(in_file, names = header, index_col = False)
    #process data
    c_o_time, c_total = func_change(df)
    #write output file        
    #arcpy.AddMessage('Writing: {}'.format(survey_comp))
    c_o_time.to_csv(survey_comp, index_label = 'index')
    c_total.to_csv(total_comp, index_label = 'index')
    #create line shp
    lines = proc_create_lines(df, shpoutput)
    arcpy.AddField_management(shpoutput, 'Length', 'FLOAT', 8,2)
    arcpy.CalculateField_management(shpoutput, 'Length', '!shape.length!', 'PYTHON') 

def func_pathsplit(in_file):
    """
    Helper function, splits full paths into components
     Output: [dir,full filename, filename no ext, ext]
                0        1               2         3
    """
    dir = os.path.dirname(in_file)
    fullfile = os.path.basename(in_file)
    noext = os.path.splitext(fullfile)[0]
    ext = os.path.splitext(fullfile)[1]
    return [dir, fullfile, noext, ext]  
      
def proc_point(in_file, proj):      
    """
    Take a csv file with no header and XYZ in fields 3,4,5
    """
    fsplit = func_pathsplit(in_file)
    outShp = os.path.join(fsplit[0], fsplit[2] + '_MovementPoints.shp')
    arcpy.MakeXYEventLayer_management(in_file,'FIELD3','FIELD4','Lyr',proj,'FIELD5')
    #create point shp
    arcpy.AddMessage('Creating: {}'.format(outShp)) 
    arcpy.CopyFeatures_management('Lyr',outShp)
        
def proc_create_lines(in_df, shpoutput):   
    """
    input [key: [year, id, x, y, z]]
                   0    1  2  3  4
    """ 
    #Check ID Datatype
    if in_df['id'].dtype.kind in 'i':
        arcpy.AddField_management(shpoutput, 'Point_ID', 'SHORT', 8)
    elif in_df['id'].dtype.kind in 'f':
        arcpy.AddField_management(shpoutput, 'Point_ID', 'DOUBLE', 8,2)
    else:
        arcpy.AddField_management(shpoutput, 'Point_ID', 'TEXT', 12)
    #loop through df
    exclude = []
    for values in in_df.itertuples():
        #process every point id only once
        if values[2] not in exclude:
            #for each point find all instances of that point --> df of all matching points
            df1 = (in_df[in_df['id'] == values[2]]).sort_values('timestamp')
            proc_write_line(df1, shpoutput)
            #
            exclude.append(values[2])

   
def proc_write_line(df_coords, shpoutput):                  
    """
    input coordinates of movement of one point over x years
    Input: df('timestamp', 'id', 'x', 'y', 'z')
    """
    point = arcpy.Point()
    array = arcpy.Array()
    cursor = arcpy.da.InsertCursor(shpoutput, ['Point_ID', 'SHAPE@'])
    for i in df_coords.itertuples(): 
        point.X = i[3]
        point.Y = i[4]
        point.Z = i[5]
        array.add(point)   
    polyline = arcpy.Polyline(array)
    array.removeAll() 
    cursor.insertRow([df_coords.iloc[0][1], polyline])
    del cursor 

    

def func_change(df):
    """
    Run through df of points and calc distance between same points in different surveys
    Input: df('timestamp', 'id', 'x', 'y', 'z')
    Output: df change over surveys  
            df change first to last survey
    """
    l = []
    l2 = []
    exclude = []
    #iterate through point data set
    for values in df.itertuples():
        #process every point id only once
        if values[2] not in exclude:
            #for each point find all instances of that point --> df of all matching points
            df1 = (df[df['id'] == values[2]]).sort_values('timestamp')
            length = len(df1)
            index = 0
            #compare every point to the subsequent timestamp 
            while index < length - 1:
                l.append(itertools.chain(df1.iloc[index].values.tolist(), df1.iloc[index + 1].values.tolist()))
                index += 1
            #compare the first to the last timestamp for total change
            l2.append(itertools.chain(df1.iloc[0].values.tolist(), df1.iloc[length - 1].values.tolist()))
            #
            exclude.append(values[2])
    #convert to df         
    cols = ('from_year', 'from_id', 'x1' ,'y1', 'z1', 'to_year', 'to_id', 'x2', 'y2', 'z2')        
    df_yr_on_yr =  pd.DataFrame(l, columns = cols)
    df_final =  pd.DataFrame(l2, columns = cols)
    #calculate change through broadcasting
    df_yr_on_yr = calc_dist(df_yr_on_yr)
    df_final = calc_dist(df_final)
    return df_yr_on_yr.sort_values(['from_id', 'from_year']), df_final.sort_values(['from_id', 'from_year'])

   
def calc_dist(df_out):
    """
    Calculates columns for dist, delta_z and azimuth
    input df('from_year', 'from_id', 'x1' ,'y1', 'z1', 'to_year', 'to_id', 'x2', 'y2', 'z2')
    output: df('from_year', 'from_id', 'x1' ,'y1', 'z1', 'to_year', 'to_id', 'x2', 'y2', 'z2', 'dist', 'delta_z', 'azimuth')
    """ 
    df_out['dist'] = np.round(np.sqrt((df_out['x1'] - df_out['x2'])**2 + (df_out['y1'] - df_out['y2'])**2),3)
    df_out['delta_z'] = np.round(df_out['z2'] - df_out['z1'],3)
    df_out['azimuth'] = np.round(np.degrees((np.arctan2((df_out['x2']-df_out['x1']), (df_out['y2']-df_out['y1'])))),0)
    #if azimuth is negative add it to 360
    df_out['azimuth'] = df_out['azimuth'].map(lambda x: 360 + x if x < 0 else x)
    return df_out    
           
if __name__ == '__main__':
    #run main program
    proc_main()






























