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
import argparse

# DATA SOURCE
# https://s3.amazonaws.com/capitalbikeshare-data/index.html


def pd_csv_group(data_folder,num=-1):
    '''Returns a DataFrame built from all csv/txt files in a directory, up to "num" of files. '''
    if num == -1:
        file_count = len(os.listdir(data_folder))
    else:
        file_count = num
    df_list = []
    #print('files to be included: ', files)
    print("stacking dataframes....")
    #print('(Please be patient for ~ 30 seconds)')
    for file_num,file in enumerate(os.listdir(data_folder)):
        f = pd.read_csv(data_folder+file)
        print(f'appending df #{file_num+1}...')
        df_list.append(f)
        # if there is a file number limit, stop here. 
        if file_num == file_count-1:
            print(f'Primary data gathered from {num} files into single dataframe   :D')
            return pd.concat(df_list, axis=0, ignore_index=True, sort=False)
    print(f'Primary data gathered from {num} files into single dataframe   :D')
    return pd.concat(df_list, axis=0, ignore_index=True, sort=False)

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
    '''INPUT: DataFrame or Series where the values are of datetime data type (have a .hour attribute)
        RETURN: Dictionary of unique items and their frequency / count'''
    
    lst = [x.hour for x in df[column_name].values]
    return freq_dict(lst)

class BikeReport(object):
    def __init__(self, df, bike_number):
        self.bike_number = bike_number
        self.duration = lifetime(df[df['Bike number'] ==bike_number].agg({'Duration':'sum'}).Duration )  
        self.trips = df[df['Bike number'] ==bike_number].count()[0]

    def __repr__(self):
        return f'<BikeReport.obj>\n\tBikeNumber:{self.bike_number}\n\tServiceLifetime:{self.duration}\n\tTotalTrips:{self.trips}'

    def lifetime(self):
        dct = {}
        dct['days'] = self.duration//86400
        dct['hours']= self.duration%86400//3600
        dct['minutes'] = (self.duration%86400)%3600//60
        dct['seconds'] = (self.duration%86400)%3600%60
        #self.duration = dct
        return dct

def time_filter(df, colname, start_time, end_time):
    ''' Returns a mask-modified dataframe with items between start_time and end_time as found in 'colname' column. '''
    if type(start_time) != type(dt.time(0,0,0)):
        print('Error: Given start time must be dt.time() obj.')
        return None
    mask_low = df[colname] > start_time
    mask_hi = df[colname] < end_time
    mask = mask_low & mask_hi
    return df[mask]
    
def station_super_dict(df,popular_stations_df ):
    station_time_hist=dict()
    station_groups = df.groupby('Start station')
    pass    
    # - - - build the super dict
    for station in popular_stations_df.ADDRESS.values: 
        try:
            station_by_hour = station_groups.get_group(station)
        except:
            # sometimes there is a space at the end of the station name as found in the address column's values for station names. 
            station_by_hour = station_groups.get_group(station+' ')
        
        # - - - The super-dict's keys are the station names, and the super-dict's values for each key are the time this station 
        station_time_hist[station] = series_freq_dict(station_by_hour, 'Start time')
    return station_time_hist

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

def plot_popstations(popstations_df, name):
    fig = plt.figure(figsize=(10,15))
    plt.style.use('ggplot')

    station_time_hist=station_super_dict(df, popstations_df)
    for i in range(len(popstations_df)):
        ax = fig.add_subplot(5,2,i+1)
        st_name = popstations_df.ADDRESS[i]
        d = station_time_hist[st_name]

        # keys are likely out of order in regards to ride count - fix with OrderedDict()
        d = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        x = [i[0] for i in list(d.items())]   
        y = [i[1] for i in list(d.items())]  
        # as these are the most popular stations in the am, lets look only at the am data (4pm-10am) *** including 9:59am ***
        ax.bar(x[4:10], y[4:10], color = 'b', width=0.8)
        ax.set_title(f'{st_name}')
        if i==0:
            ylim = 1.2* max(d.values())
        ax.set_ylim(0,ylim)
    fig.suptitle(f'Top Ten Capital Bikeshare Stations \n Bike Rentals Per Hour in the {name}',fontsize=18)
    plt.subplots_adjust(hspace=0.5)

if __name__ == '__main__':
    # Argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--barchart', help = 'activate barcharts', type=bool, default = 'store_true')
    parser.add_argument('--geoplot', help='activate geographic data map', type = bool, default ='store_true')
    parser.add_argument('--dflim', help = 'limit the number of files used to build main df', type=int, default = 0)
    
    args = parser.parse_args()


    print('geoplot set to ',args.geoplot)
    print('dflim set to ', args.dflim)
    if args.dflim != 0:
        dflim = args.dflim
    
    # - - -Define the folder containing only data files (csv or txt)
    data_folder = "data/"
    df = pd_csv_group(data_folder, dflim)
    

    # - - - FEATURE ENGINEERING 
    # the locations of the bike stations in lat/long are found in another dataset from Open Data DC:
    # https://opendata.dc.gov/datasets/capital-bike-share-locations;
    # detailed description of data from this file can be found here:
    # https://www.arcgis.com/sharing/rest/content/items/a1f7acf65795451d89f0a38565a975b3/info/metadata/metadata.xml?format=default&output=html
    station_locations_df = pd.read_csv('misc/Capital_Bike_Share_Locations.csv')   

    # taking only the location information from the locations dataset...
    station_locations = station_locations_df[['ADDRESS','TERMINAL_NUMBER', 'LATITUDE', 'LONGITUDE']].copy()

    # we can now merge the new locations dataframe into the primary dataframe
    df=df.merge(station_locations, left_on='Start station number', right_on='TERMINAL_NUMBER')

    # (make a 'start time' and 'end time' column)
    # (after recasting the 'start date' to a datetime obj)  :/
    df['Start time'] =[x.time() for x in pd.to_datetime((df['Start date']))]     
    df['End time'] =[x.time() for x in pd.to_datetime((df['End date']))]     
    

    # - - - CLASS OBJECT INSTANTIATION: BIKEREPORT()
    # - - - Which bikes (by bike number) have been used the most (by duration)?
    most_used_bikes_10 = df[['Bike number', 'Duration']].groupby('Bike number').agg(sum).sort_values(by='Duration', ascending = False)[:10]
    
    # - - - Generate reports for each of the top ten most used bikes.
    for i in range(9):
        br = BikeReport(df, most_used_bikes_10.iloc[i].name)
        str(br)


    # ADDRESS THE BUSINESS QUESTIONS
    # - What are the most popular bike stations for starting a ride in the morning (4am-9am)?
    # - - - group rides that start in the morning (4am-9am)
    morning_rides = time_filter(df, 'Start time', dt.time(4,0,0), dt.time(9,0,0))

    # - - - group rides that start in the afternoon (9am-3pm)
    afternoon_rides = time_filter(df, 'Start time', dt.time(9,0,0), dt.time(15,0,0))
    
    # - - - group rides that start in the evening (3pm>)
    evening_rides = time_filter(df, 'Start time', dt.time(15,0,0), dt.time(23,59,59))

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


    bar_chart = False
    if bar_chart:
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
        # (adding subsequent layers to build a stacked bar chart)
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


    station_time_hist2_pop_morn_stations = station_super_dict(df, popular_morning_stations)
    station_time_hist2_pop_aft_stations = station_super_dict(df, popular_afternoon_stations)
    station_time_hist2_pop_eve_stations = station_super_dict(df, popular_evening_stations)



    plot_popstations(popular_morning_stations, 'Morning')
    plot_popstations(popular_afternoon_stations, 'Afternoon')

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    geomap = True

    if geomap:

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
        fig,ax = plt.subplots(figsize=(10,10))
        gpd_street.geometry.plot(ax = ax, color='k', linewidth=.25, )  

        # WASHINGTON DC BOUNDARY PLOT 
        ax.plot(wash_path_x, wash_path_y, 'r', linewidth=.5, alpha = .4)
        # ALL BIKE STATIONS
        #ax.plot(station_x, station_y, 'o', color = 'b', label='Bikeshare Stations')
        ax.scatter(x = station_x, y = station_y, color='b', label = "Bikeshare Stations", alpha = .2)

        ax.scatter(x =popular_morning_stations.LONGITUDE.values, y=popular_morning_stations.LATITUDE.values, color = 'r'  , label = 'Popular in Morning')
        ax.scatter(x =popular_afternoon_stations.LONGITUDE.values, y=popular_afternoon_stations.LATITUDE.values, color = 'b',  label = 'Popular in Afternoon')
        ax.scatter(x =popular_evening_stations.LONGITUDE.values, y=popular_evening_stations.LATITUDE.values, color = 'g' ,label = 'Popular in Evening' )

        '''
        for all rides that start from a popular morning station, 
            plot a line from that start station to the end station
        '''
        
        ax.plot(morning_rides.LONGITUDE.values, morning_rides.LATITUDE.values, color='g', linewidth=.1)     
        
        
        # - - - make it sexy
        ax.set_xlim(-77.13,-76.90)
        ax.set_ylim(38.79,39)
        plt.xlabel('Latitude ($^\circ$West)')
        plt.ylabel('Longitude ($^\circ$North)')
        ax.set_title('Capital Bikeshare Across Washington DC', fontsize=30)
        plt.legend()
