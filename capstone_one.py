import numpy as np 
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from os import listdir

# DATA SOURCE
# https://s3.amazonaws.com/capitalbikeshare-data/index.html


def pd_csv_group(data_folder):
    '''Returns a DataFrame built from all csv/txt files in a directory'''
    files = listdir(data_folder)
    df_list = []

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
    # Define the folder containing only data files (csv or txt)
    data_folder = "/Users/casey/Documents/galvanize/capstone_one/data/"
    df = pd_csv_group(data_folder)

    # Histogram of stations and their cumulative duration of rides started there. 
    df[['Start station number','Duration']]\
        .groupby('Start station number')\
            .count().sort_values(by='Duration', ascending = False)\
                .hist(bins = 100) 
    
    # Which bikes (by bike number) have been used the most (by duration)?
    most_used_bikes_10 = df[['Bike number', 'Duration']].groupby('Bike number').agg(sum).sort_values(by='Duration', ascending = False)[:10]
    
    # most used bike and it's info
    br = BikeReport(df, most_used_bikes_10.iloc[0].name)

    # unique bike stations by name and station number
    stations = pd.concat((df['Start station'],df['End station']))

    # what are the most popular bike stations for starting a ride in the morning (4am-9am)?
    # (make a 'start time' column)
    # (after recasting the 'start date' to a datetime obj)  :/
    df['Start time'] =[x.time() for x in pd.to_datetime((df['Start date']))]     
    
    ##  of rides the start in the morning (4am-9am)
    start_after4am = df[df['Start time'] > dt.time(4,0,0)] # mask applied to df with start times after 4am
    morning_rides = start_after4am[df['Start time'] < dt.time(9,0,0)] # mask applied to 4am starts for rides that end by 10am
    ##  of rides the start in the afternoon (9am-3pm)
    start_after10am = df[df['Start time'] > dt.time(9,0,0)] # mask applied to df with start times after 10am
    afternoon_rides = start_after4am[df['Start time'] < dt.time(15,0,0)] # mask applied to 4am starts for rides that end by 3pm
    ##  of rides the start in the evening (3pm>)
    evening_rides = df[df['Start time'] > dt.time(15,0,0)] # mask applied to df with start times after 3pm


    # ###     grouped by start station and summing along 'Duration' column for each group
        # popular_morning_stations = morning_rides.groupby('Start station').agg({'Duration':'sum'}).sort_values(by = 'Duration', ascending = False)
        # ####        what are the top 10% of all stations
        # top_morning_stations = popular_morning_stations[:popular_morning_stations.count()[0]//10-1].index # .index gives the station names in this DF
        
        # ###     grouped by start station and summing along 'Duration' column for each group
        # popular_afternoon_stations = afternoon_rides.groupby('Start station').agg({'Duration':'sum'}).sort_values(by = 'Duration', ascending = False)
        # ####        what are the top 10% of all stations
        # top_afternoon_stations = popular_afternoon_stations[:popular_afternoon_stations.count()[0]//10-1].index # .index gives the station names in this DF
        
        # ###     grouped by start station and summing along 'Duration' column for each group
        # popular_evening_stations = evening_rides.groupby('Start station').agg({'Duration':'sum'}).sort_values(by = 'Duration', ascending = False)
        # ####        what are the top 10% of all stations
        # top_evening_stations = popular_evening_stations[:popular_evening_stations.count()[0]//10-1].index # .index gives the station names in this DF
    
    # ------- SECOND TAKE AT ANALYSIS
    popular_morning_stations = morning_rides['Start station'].value_counts()[0:10]
    popular_afternoon_stations = afternoon_rides['Start station'].value_counts()[0:10]
    popular_evening_stations = evening_rides['Start station'].value_counts()[0:10]

 
    '''Lets see a plot that compares the most popular start stations in the morning 
    '''
    # # - - - select a style
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
    
