import numpy as np 
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import os
import utm
import shapefile as shp
import seaborn as sns
from collections import OrderedDict
import geopandas as gpd 

# DATA SOURCE
# https://s3.amazonaws.com/capitalbikeshare-data/index.html


def pd_csv_group(data_folder):
    '''Returns a DataFrame built from all csv/txt files in a directory'''
    #files = [f if os.path.isfile(f) f in listdir(data_folder) ]
    files = [f for f in os.listdir(data_folder) if os.path.isfile(f)]

    df_list = []
    print("stacking dataframes....")
    print('(Please be patient for ~ 30 seconds)')
    for file in os.listdir(data_folder):
        f = pd.read_csv(data_folder+file)
        df_list.append(f)

    return pd.concat(df_list, axis=0, ignore_index=True, sort=True)

def lifetime(duration):
    '''Returns dict{days:days, hours:hours, minutes:minutes, seconds:seconds}'''
    dct = {}
    dct['days'] = duration//86400
    dct['hours']= duration%86400//3600
    dct['minutes'] = (duration%86400)%3600//60
    dct['seconds'] = (duration%86400)%3600%60
    return dct

def freq_dict(lst):
    dct = dict()
    for item in lst:
        if item not in dct:
            dct[item]=0
        else:
            dct[item]+=1
    return dct

def series_freq_dict(df, column_name):
    '''INPUT: DataFrame or Series or List
        RETURN: Dictionary of unique items and their frequency / count'''
    
    lst = [x.hour for x in df[column_name].values]
    return freq_dict(lst)

class BikeReport(object):
    def __init__(self, df, bike_number):
        self.bike_number = bike_number
        self.duration = df[df['Bike number'] ==bike_number].agg({'Duration':'sum'}).Duration   
        self.trips = df[df['Bike number'] ==bike_number].count()[0]

    def __repr__(self):
        return f'<BikeReport.obj>\nBikeNumber:{self.bike_number}\nLifetime:{self.duration}s\nTrips:{self.trips}'

    def lifetime(self):
        dct = {}
        dct['days'] = self.duration//86400
        dct['hours']= self.duration%86400//3600
        dct['minutes'] = (self.duration%86400)%3600//60
        dct['seconds'] = (self.duration%86400)%3600%60
        return dct

def read_shapefile(sf):
    """
    Read a shapefile into a Pandas dataframe with a 'coords' 
    column holding the geometry information. This uses the pyshp
    package
    """
    fields = [x[0] for x in sf.fields][1:]
    records = sf.records()
    shps = [s.points for s in sf.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shps)
    return df


if __name__ == '__main__':
    # - - -Define the folder containing only data files (csv or txt)
    data_folder = "data/"
    df = pd_csv_group(data_folder)
    

    # - - - FEATURE ENGINEERING OPPORTUNITY
    # the locations of the bikes are found in another dataset from Open Data DC:
    # https://opendata.dc.gov/datasets/capital-bike-share-locations;
    # detailed description of data from this file can be found here:
    # https://www.arcgis.com/sharing/rest/content/items/a1f7acf65795451d89f0a38565a975b3/info/metadata/metadata.xml?format=default&output=html
    station_locations_df = pd.read_csv('misc/Capital_Bike_Share_Locations.csv')   

    # taking only the location information from the locations dataset...
    station_locations = station_locations_df[['ADDRESS','TERMINAL_NUMBER', 'LATITUDE', 'LONGITUDE', 'X', 'Y']].copy()

    # we can now merge the new dataset (subset) into the primary dataframe
    df=df.merge(station_locations, left_on='Start station number', right_on='TERMINAL_NUMBER')


    # - - - CLASS OBJECT INSTANTIATION
    # - - - Which bikes (by bike number) have been used the most (by duration)?
    most_used_bikes_10 = df[['Bike number', 'Duration']].groupby('Bike number').agg(sum).sort_values(by='Duration', ascending = False)[:10]
    
    # - - - most used bike and it's info
    br = BikeReport(df, most_used_bikes_10.iloc[0].name)

    # - - - unique bike stations by name and station number
    stations = pd.concat((df['Start station'],df['End station']))

    # what are the most popular bike stations for starting a ride in the morning (4am-9am)?
    # (make a 'start time' column)
    # (after recasting the 'start date' to a datetime obj)  :/
    df['Start time'] =[x.time() for x in pd.to_datetime((df['Start date']))]     
    
    # - - -  group rides that start in the morning (4am-9am)
    start_after4am = df[df['Start time'] > dt.time(4,0,0)] # mask applied to df with start times after 4am
    morning_rides = start_after4am[df['Start time'] < dt.time(9,0,0)] # mask applied to 4am starts for rides that end by 10am
    
    # - - - group rides that start in the afternoon (9am-3pm)
    start_after10am = df[df['Start time'] > dt.time(9,0,0)] # mask applied to df with start times after 10am
    afternoon_rides = start_after4am[df['Start time'] < dt.time(15,0,0)] # mask applied to 4am starts for rides that end by 3pm
    
    # - - - group rides that start in the evening (3pm>)
    evening_rides = df[df['Start time'] > dt.time(15,0,0)] # mask applied to df with start times after 3pm

    # - - - Gather data by top ten most popular stations during various times of day 
    popular_morning_stations = morning_rides.groupby('TERMINAL_NUMBER')\
        .size()\
        .reset_index()\
        .rename(columns={0:'RIDE_COUNT'})\
        .sort_values(by='RIDE_COUNT', ascending=False)[0:10]\
        .merge(station_locations, on='TERMINAL_NUMBER', how='left')
    popular_afternoon_stations = afternoon_rides.groupby('TERMINAL_NUMBER')\
        .size()\
        .reset_index()\
        .rename(columns={0:'RIDE_COUNT'})\
        .sort_values(by='RIDE_COUNT', ascending=False)[0:10]\
        .merge(station_locations, on='TERMINAL_NUMBER', how='left')
    popular_evening_stations = evening_rides.groupby('TERMINAL_NUMBER')\
        .size()\
        .reset_index()\
        .rename(columns={0:'RIDE_COUNT'})\
        .sort_values(by='RIDE_COUNT', ascending=False)[0:10]\
        .merge(station_locations, on='TERMINAL_NUMBER', how='left')

    # - - - select a style
    plt.style.use('fivethirtyeight')
    fig,ax = plt.subplots(figsize=(20,10))
    
    # - - - define the data to plot
    layer1 = np.array(popular_morning_stations.RIDE_COUNT.values)
    layer2 = np.array(popular_afternoon_stations.RIDE_COUNT.values)
    layer3 = np.array(popular_evening_stations.RIDE_COUNT.values)

    labels_mor = [popular_morning_stations.ADDRESS.values]
    labels_aft = [popular_afternoon_stations.ADDRESS.values]
    labels_eve = [popular_evening_stations.ADDRESS.values]

    # - - - build the bar plot
    width = 0.8
    xlocations = np.array(range(len(layer1)))
    ax.bar(xlocations, layer3+layer2+layer1, width, label = 'Evening Rides', color = 'y', align = 'center')
    ax.bar(xlocations, layer2+layer1, width, label = 'Afternoon Rides', color = 'b', align = 'center')
    ax.bar(xlocations, layer1, width, label = 'Morning Rides', color = 'r', align = 'center')

    # - - - make it sexy
    ax.set_xticks(ticks=xlocations)
    ax.set_xticklabels(labels_mor[0], rotation=0)
    for tick in ax.xaxis.get_major_ticks()[1::2]:
        tick.set_pad(35)
    ax.set_xlabel("Station Name/Location")
    ax.set_ylabel("Two-Year Ride Count")
    ax.yaxis.grid(True)
    ax.legend(loc='best', prop={'size':'small'})
    ax.set_title("Top 10 Popular Bike Stations by Time of Day")
    fig.tight_layout(pad=1)


    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------


    # Now build a dictionary for each station where the keys are the time(by hour)
    # and the values are the counts of rides for that hour for that station. 
    # Each station's dictionary will all be stored in a 'super dictionary'

    # - - - initiate the super dictionary 
    station_time_hist = dict()
    
    # - - - group the data by 'start station'
    station_groups = df.groupby('Start station')

    # - - - list of hours in a day, from 0 to 24
    ### time_steps = [str(x) for x in range(25)]
    time_steps = [f'{x%13}{("am" if x<12  else "pm")}' for x in range(0,25)]
    time_steps.remove('0pm')
    # - - - build the super dict
    for station in popular_morning_stations.ADDRESS: 
        # - - - get the 'nth' station group from the 'station_groups' group object
        station_by_hour = station_groups.get_group(station)
        
        # - - - assign a dictionary as a super dictionary's value for the key of this station 
        station_time_hist[station] = series_freq_dict(station_by_hour, 'Start time')

    # - - - Plot the ride frequency by hour for each bike station
    fig = plt.figure(figsize=(10,15))
    plt.style.use('ggplot')
    for i in range(len(popular_morning_stations)):
        ax = fig.add_subplot(5,2,i+1)
        st_name = popular_morning_stations.index[i]
        d = station_time_hist[st_name]
        # keys are likely out of order - fix with OrderedDict()
        d = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        x = [i[0] for i in list(d.items())]   
        y = [i[1] for i in list(d.items())]  
        # as these are the most popular stations in the am, lets look only at the am data (4pm-10am) *** including 9:59am ***
        ax.bar(x[4:10], y[4:10], color = 'b', width=0.8)
        ax.set_title(f'{st_name}')
        if i==0:
            ylim = max(d.values())
        ax.set_ylim(0,ylim)
    fig.suptitle('Top Ten Capital Bikeshare Stations \n Bike Rentals Per Hour in the Morning',fontsize=18)
    plt.subplots_adjust(hspace=0.5)

  
    #sns.set(context='paper', style='whitegrid', palette='pastel', color_codes=True)
    #sns.mpl.rc('figure', figsize=(10,6))

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------



    # - - - use the shape file to plot the boundary of washington dc
    # data source: https://opendata.dc.gov/datasets/23246020d6894453bdfcee00956df818_41
    wash_shp_path = 'misc/Washington_DC_Boundary/Washington_DC_Boundary.shp'
    wash_shp_file = shp.Reader(wash_shp_path) 
    df_wash_path = read_shapefile(wash_shp_file)
    wash_path = [(x[0],x[1]) for x in df_wash_path.coords[0]]
    # - - - build arrays for the x,y coords in lat/long for the dc boundary
    wash_path_x = [x[0] for x in wash_path]    
    wash_path_y = [x[1] for x in wash_path]
    # - - - build arrays for the x,y coords in lat/long for the bike stations
    station_x = [x for x in station_locations.LONGITUDE]
    station_y = [x for x in station_locations.LATITUDE]   
    # - - - it would be nice to see the streets as well. Geopandas to the rescue!
    street_shp_path = 'misc/Street_Centerlines/Street_Centerlines.shp'
    gpd_street = gpd.read_file(street_shp_path)
    
    # - - - plot the stations and streets with washington dc boundary
    plt.style.use('ggplot')

    # STREET VECTORS
    ax = gpd_street.geometry.plot(color='k', linewidth=.1)  
    #fig = plt.figure(figsize=(15,15))    
    # WASHINGTON DC BOUNDARY PLOT 
    ax.plot(wash_path_x, wash_path_y, 'b', linewidth=.1)
    # ALL BIKE STATIONS
    ax.plot(station_x, station_y, 'o', color = 'b')
    # TOP TEN BIKE STATIONS IN RED
    #ax.plot([x for x in popular_morning_stations.LATITUDE.values],[y for y in popular_morning_stations.LONGITUDE.values],'o',color='r' )
    ax.plot([ popular_morning_stations.LATITUDE.values],[ popular_morning_stations.LONGITUDE.values],'o',color='r', label = 'Popular Morning Stations')
    ax.plot([ popular_afternoon_stations.LATITUDE.values],[ popular_afternoon_stations.LONGITUDE.values],'o',color='r', label = 'Popular Afternoon Stations')
    ax.plot([ popular_evening_stations.LATITUDE.values],[ popular_evening_stations.LONGITUDE.values],'o',color='r', label = 'Popular Evening Stations')
    
    # - - - make it sexy
    ax.set_xlim(-77.13,-76.90)
    ax.set_ylim(38.79,39)
    plt.xlabel('Latitude (in degrees))')
    plt.ylabel('Longitude (in degrees))')
    ax.set_title('Capital Bikeshare Across Washington DC', fontsize=30)
