import numpy as np 
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from os import listdir

# DATA SOURCE
# https://s3.amazonaws.com/capitalbikeshare-data/index.html


def pd_csv_group(data_folder, first_few=None):
    '''Returns a DataFrame built from all csv/txt files in a directory'''
    if first_few:
        files = listdir(data_folder)[0:first_few]
    else:
        files = listdir(data_folder)
    df_list = []
    print("stacking dataframes....")
    print('(Please be patient for ~ 30 seconds)')
    for file in listdir(data_folder):
        f = pd.read_csv(data_folder+file)
        df_list.append(f)

    return pd.concat(df_list, axis=0, ignore_index=True)

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

if __name__ == '__main__':
    # - - -Define the folder containing only data files (csv or txt)
    data_folder = "data/"
    df = pd_csv_group(data_folder, first_few =4)
    

    # - - - FEATURE ENGINEERING OPPORTUNITY
    # the locations of the bikes are found in another dataset from Open Data DC:
    # https://opendata.dc.gov/datasets/capital-bike-share-locations;
    # detailed description of data from this file can be found here:
    # https://www.arcgis.com/sharing/rest/content/items/a1f7acf65795451d89f0a38565a975b3/info/metadata/metadata.xml?format=default&output=html
    station_locations_df = pd.read_csv('Capital_Bike_Share_Locations.csv')   

    # taking only the location information from the locations dataset...
    station_locations = station_locations[['TERMINAL_NUMBER', 'LATITUDE', 'LONGITUDE', 'X', 'Y']].copy()

    # we can now merge the new dataset (subset) into the primary dataframe
    df=df.merge(station_locations, left_on='Start station number', right_on='TERMINAL_NUMBER')

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
    popular_morning_stations = morning_rides['Start station'].value_counts()[0:10]
    popular_afternoon_stations = afternoon_rides['Start station'].value_counts()[0:10]
    popular_evening_stations = evening_rides['Start station'].value_counts()[0:10]

    # - - - select a style
    plt.style.use('fivethirtyeight')
    fig,ax = plt.subplots(figsize=(20,10))
    
    # - - - define the data to plot
    layer1 = np.array(popular_morning_stations.values)
    layer2 = np.array(popular_afternoon_stations.values)
    layer3 = np.array(popular_evening_stations.values)
    labels = [item.replace("/","\n", 1) for item in popular_morning_stations.index]

    # - - - build the bar plot
    width = 0.8
    xlocations = np.array(range(len(layer1)))
    ax.bar(xlocations, layer3+layer2+layer1, width, label = 'Evening Rides', color = 'y', align = 'center')
    ax.bar(xlocations, layer2+layer1, width, label = 'Afternoon Rides', color = 'b', align = 'center')
    ax.bar(xlocations, layer1, width, label = 'Morning Rides', color = 'r', align = 'center')

    # - - - make it sexy
    ax.set_xticks(ticks=xlocations)
    ax.set_xticklabels(labels, rotation=0)
    for tick in ax.xaxis.get_major_ticks()[1::2]:
        tick.set_pad(35)
    ax.set_xlabel("Station Name/Location")
    ax.set_ylabel("Two-Year Ride Count")
    ax.yaxis.grid(True)
    ax.legend(loc='best', prop={'size':'small'})
    ax.set_title("Top 10 Popular Bike Stations by Time of Day")
    fig.tight_layout(pad=1)
    # ------------------------------------------------------------------------------------------
    # Now build a dictionary for each station where the keys are the time(by hour)
    # and the values are the counts of rides for that hour for that station. 
    # Each station's dictionary will all be stored in a 'super dictionary'

    # - - - initiate the super dictionary 
    station_time_hist = dict()
    
    # - - - group the data by 'start station'
    station_groups = df.groupby('Start station')

    # - - - list of hours in a day, from 0 to 24
    time_steps = [str(x) for x in range(25)]


    for station in popular_morning_stations.index: #top three of top ten popular morning stations for starting a ride 
        # - - - get the 'nth' station group from the 'station_groups' group object
        station_by_hour = station_groups.get_group(station)
        
        # - - - assign a dictionary as a super dictionary's value for the key of this station 
        station_time_hist[station] = series_freq_dict(station_by_hour, 'Start time')

    # - - - Plot the ride frequency by hour for each bike station

    fig = plt.figure(figsize=(15,10))
    plt.style.use('ggplot')
    for i in range(len(popular_morning_stations)):
        ax = fig.add_subplot(5,2,i+1)
        st_name = popular_morning_stations.index[i]
        d = station_time_hist[st_name]
        ax.bar(list(d.keys()), list(d.values()), color = 'r', width=0.8)
        ax.set_title(f'{st_name}')
        if i==0:
            ylim = max(d.values())
        ax.set_ylim(0,ylim)
    fig.suptitle('Top Ten Capitol Bikeshare Stations \n Bike Rentals Per Hour',fontsize=18)
    plt.subplots_adjust(hspace=0.5)


    # for i in range(len(popular_morning_stations.index)):
    #     d = station_time_hist[popular_morning_stations.index[0]]
    #     ax.bar(list(d.keys()), list(d.values()), width=0.8);