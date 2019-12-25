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
import descartes
import argparse


# PRIMARY DATA SOURCE
# https://s3.amazonaws.com/capitalbikeshare-data/index.html

# - - - - - - - - - - - - - - - - 
# - - CHECK OUT MY DOCSTRINGS!!! 
# - - NumPy/SciPy Docstring Format
# - - - - - - - - - - - - - - - - 
 
def pd_csv_group(data_folder,num=-1):
    """Read many csv data files from a specified directory into a single data frame. 
    
    Parameters
    ----------
    data_folder : str 
        path to directory containing ONLY csv data files.
    num (int), optional 
        number of csv files to read and integrate into the primary dataframe. 
        
    Returns
    -------
    DataFrame()
        dataframe built from csv files in given directory. 
    """

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
    print(f'Primary data gathered from {file_num+1} files into single dataframe   :D')
    return pd.concat(df_list, axis=0, ignore_index=True, sort=False)

def lifetime(duration):
    """Returns a dictionary that converts a number of seconds into a dictionary object with keys of 'days', 'hours', 'minutes', and 'seconds'. 

    Parameters
    ----------
    duration (int): 
        The duration (in seconds) to be transformed into a dictionary. 
    
    Returns
    -------
    dict
        a dictionary in the form of dict('days':int(), 'hours':int(), 'minutes':int(),'seconds':int())
    """

    dct = {}
    dct['days'] = duration//86400
    dct['hours']= duration%86400//3600
    dct['minutes'] = (duration%86400)%3600//60
    dct['seconds'] = (duration%86400)%3600%60
    return dct

def freq_dict(lst):
    """Returns a dictionary with keys of unique values in the given list and values representing the count of occurances. 

    Parameters
    ----------
    lst (list)
        a list of items to determine number of occurances for. 

    Returns
    -------
    dict
        a dictionary of the format dict('unique_value_n': int(), 'unique_value_(n+1)': int(), ... )
    """

    dct = dict()
    for item in lst:
        if item not in dct:
            dct[item]=0
        else:
            dct[item]+=1
    return dct

def series_freq_dict(df, column_name):
    """Performs the function "freq_dict()" for df["column_name"] 
    after extracting the "datetime.hour" value from each element.  
    
    Parameters
    ----------
    df (DataFrame)
        the dataframe object 
    column_name (str)
        name of column in dataframe. *** Must contain ONLY datetime() objects. 
    
    Returns
    -------
    dict()
        a frequency dictionary from freq_dict()
    """
    
    lst = [x.hour for x in df[column_name].values]
    return freq_dict(lst)

class BikeReport(object):
    """Creates an instance of the BikeReport object. 

    Attributes
    ----------
    bike_number (str)
        bike-specific identification number. Example, "W32432".
    duration (dict) 
        dictionary representation of the duration of bike service life as determined from the data given        
    
    Parameters
    ----------
    df (DataFrame)
        dataframe that contains the bike of interest.
    bike_number (str)
        bike-specific identification number. Example, "W32432". 
    """

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
        return dct

def time_filter(df, colname, start_time, end_time):
    """Returns a filtered dataframe at a specified column for time occurances between a start and end time. 

    Parameters
    ----------
    df (dataframe)
        dataframe object to apply filter to.
    colname (str)
        name of column in given dataframe to filter through. 
    start_time (datetime)
        datetime object representing the lower bound of the filter.
    end_time (datetime)
        datetime object representing the upper bound of the filter. 

    Returns
    -------
    copy 
        a filtered copy of the given dataframe    
    
    """
    if type(start_time) != type(dt.time(0,0,0)):
        print('Error: Given start time must be datetime.time() obj.')
        return None
    mask_low = df[colname] > start_time
    mask_hi = df[colname] < end_time
    mask = mask_low & mask_hi
    return df[mask].copy()
    
def station_super_dict(df,popular_stations_df):
    """Given a primary dataframe and a dataframe representing bike stations of interest, performs the 
    series_freq_dict function for each value in popular_stations_df to get the 'by hour' frequency of each station. 

    Parameters
    ----------
    df (dataframe)
        primary dataframe of all bikeshare transactions. 
    popular_stations_df (dataframe)
        dataframe representing bike stations of interest. 

    Returns
    -------
    dict()     
        a dictionary with keys representing the values from the popular_stations_df, 
        and values are dictionaries of the output for the series_freq_dict() function for each station. 
    """

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
    """Read a shape file into a padas dataframe object. 

    Parameters
    ----------
    sf (shapefile object)
        a shape file 

    Returns
    -------
    dataframe
        the loaded dataframe from the given shapefile. 
    """
    fields = [x[0] for x in sf.fields][1:]
    records = sf.records()
    shps = [s.points for s in sf.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shps)
    return df

def plot_popstations(popstations_df, name):
    """Given a dataframe of bike stations of interest, plot the locations of those stations. 

    Parameters
    ----------
    popstations_df (dataframe)
        dataframe of bike stations of interest. 
    name (str)
        string representing "Morning", "Afternoon", or "Evening" time. Used in the title of the plot. 

    Returns
    -------
    None
        produces the plot. 
    """

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

def plot_geomap(popstation, daytime_rides, daytime,hardstop=False):
    """Plot the bike stations and lines from start to end for bike rides. 
    
    Parameters
    ----------
    popstation (dataframe)
        dataframe of bike stations of interest.
    daytime (str) 
        string of `"Morning"`, `"Afternoon"`, or `"Evening"`. Used in title of plot. 
    daytime_rides (dataframe)
        dataframe of morning_rides, afternoon_rides, or evening_rides.
    hardstop (int)
        limit the number of rides to look at in daytime_rides. Mostly for testing on subsets. Defaults to `hardstop=False`.

    Returns
    -------
    None
        Produces a GeoDataFrame plot. 
    """

    # - - - READ IN SHAPE FILE FOR BORDER OF DC
    # data source: https://opendata.dc.gov/datasets/23246020d6894453bdfcee00956df818_41
    wash_shp_path = 'misc/Washington_DC_Boundary/Washington_DC_Boundary.shp'
    gpd_washborder = gpd.read_file(wash_shp_path)
    
    # - - - READ IN SHAPE FILE FOR STREET MAP OF DC
    street_shp_path = 'misc/Street_Centerlines/Street_Centerlines.shp'
    gpd_street = gpd.read_file(street_shp_path)
    
    # - - - DEFINE X AND Y OF STATION LOCATIONS FOR SCATTER PLOTTING
    station_x = [x for x in station_locations.LONGITUDE]
    station_y = [x for x in station_locations.LATITUDE]   
    
    # - - - PLOT DC STREET LINES AND BORDER POLYGON 
    plt.style.use('ggplot')
    fig,ax = plt.subplots(figsize=(15,15))

    # - - - street map is plotted in black with very thin lines. 
    gpd_street.geometry.plot(ax = ax, color='k', linewidth=.25, )  
    gpd_washborder.geometry.plot(ax = ax, color = 'grey', linewidth  =.5, alpha = .3)
    
    # if there are fewer rows than the declared 'hardstop', change hardstop to False
    hardstop_cap = daytime_rides.size
    if hardstop > hardstop_cap:
        print(f'Given number of bikeshare transactions to plot (hardstop = {hardstop}) exceeds number available {hardstop_cap}!\nPlotting up to {hardstop_cap} transactions.')
        hardstop = False
    
    # - - - SCATTER PLOT OF ALL BIKE STATIONS AND POPULAR BIKE STATIONS
    #ax.scatter(x = station_x, y = station_y, color='b', marker="o",label = "Bikeshare Stations", alpha = .2)
    

    # handle the plotting of the popstation based on it's datatype (if multiple stations were passed in or only one was passed in)
    popstation_is_dataframe = 'DataFrame' in str(type(popstation))
    if popstation_is_dataframe: 
        # handle dataframe popstation
        ax.scatter(x =popstation.LONGITUDE.values, y=popstation.LATITUDE.values, color = 'b', s=100, zorder = 5, alpha=1, marker="*",label = f'Popular in {daytime}')
        # for the plotting of rides at that station we must handle the terminal number values being a single or multiple valued array/list. 
        terminals = [x for x in popstation.TERMINAL_NUMBER.values]
    else:
        station_name= station_locations[station_locations['TERMINAL_NUMBER'] == popstation.TERMINAL_NUMBER].ADDRESS.values[0]                                                                           
        ax.scatter(x =popstation.LONGITUDE, y=popstation.LATITUDE, color = 'b', s=100, zorder = 5, alpha=1, marker="*",label = f'{station_name}')
        # for the plotting of rides at that station we must handle the terminal number values being a single or multiple valued array/list. 
        terminals = [popstation.TERMINAL_NUMBER]
    

    # TODO: Refactor to optimize for runtime complexity. O(n) is probably not as good as it could be. Need help here. 
    # - - - NETWORK PLOT OF WHERE THE CUSTOMERS OF MORNING RIDES GO WITHIN DC
    for i,ride in daytime_rides.iterrows():
        # looking at only the most popular stations and where the customers go. 
        if ride.TERMINAL_NUMBER in terminals:
            mask = station_locations['TERMINAL_NUMBER'].values == ride['End station number']
            x1 = ride.LONGITUDE
            x2 = station_locations[mask].LONGITUDE
            y1 = ride.LATITUDE
            y2 = station_locations[mask].LATITUDE

            # sometimes the starting station is not in the station_locations df (outdated station locations? new stations?)
            # if this happens, the length of the returned x2 series will be zero
            if len(list(x2.values)) > 0 and len(list(y2.values)) > 0:
                X= [x1,x2 ]
                X_float = [float(x) for x in X]
                Y = [y1,y2 ]
                Y_float = [float(y) for y in Y]

                ax.plot(X_float,Y_float,'r',linewidth=.5, alpha=.1)
                ax.scatter(X_float[1], Y_float[1], color = 'k', marker="X",alpha=.1)

            if hardstop:
                if i > hardstop:
                    break
    
    # - - - make it sexy
    ax.set_xlim(-77.13,-76.90)
    ax.set_ylim(38.79,39)
    plt.xlabel('Longitude ($^\circ$West)')
    plt.ylabel('Latitude ($^\circ$North)')
    ax.set_title(f'Capital Bikeshare \n 10 Highest Performing Stations during the {daytime}', fontsize=20)
    plt.legend()

def print_args(args):
    """Print to console the values for all args. For visual verification. 
    Parameters
    ----------
    args (argparse object)
        contains all args and their values. 
    Returns
    -------
    None
        prints to console.
    """
    
    # - - - Output the args for visual verification. Especially useful during testing. 
    print('ARG STATUS \n')
    
    print(f'--barchart \t{args.barchart}')
    print(f'--geoplot \t{args.geoplot}')
    print(f'--testgeo \t{args.testgeo}')
    if args.dflim != 0:
        dflim = args.dflim
        print(f'dflim \t{dflim}')
    else:
        dflim = -1
        print(f'dflim \t{dflim}')
    print('-'*72)

class StationStats(object):
    def __init__(self, df, station_terminal_number):
        self.station_id = station_terminal_number

        def calc_station_rates(self, df, station_terminal_number): 
            ''' Gets the ride rate of a given station by hour for each day Mon-Sun. Returned as a dictionary of dictionaries'''

            # define keys for dictionaries
            days = list(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
            hours = list(f'{x}hr_rates' for x in range(24))
            
            # super dict (dict of dicts) for each day and each hour of each day
            dct = dict({k:dict({k:list() for k in hours}) for (k,v) in list(zip(days, hours))}) 
            
            # filter df by station number of interest
            terminal_number_mask = df['TERMINAL_NUMBER'] == station_terminal_number
            
            # isolate the columns we care about
            cols_we_care_about = ['Start date', 'Start station number','Start time', 'End time' ]
            df_filtered_for_terminal = df[terminal_number_mask][cols_we_care_about].copy()

            # extract and separate the date and the time from the timestamp
            df_filtered_for_terminal['Timestamp_date'] = df_filtered_for_terminal['Start date'].map(lambda x: x.split(' ')[0])
            df_filtered_for_terminal['Timestamp_hour'] = df_filtered_for_terminal['Start time'].map(lambda x: str(x.hour))
            
            # since all entries are now from the same station, drop the station number (its the same value all the way down).
            # we also no longer need the 'End time' or 'Start time', as we only needed the hour of the start time. 
            df_filtered_for_terminal.drop(columns=['Start date','Start time', 'End time','Start station number'], inplace = True)
            
            # lets look at each date separately for what the ride rates are by hour. 
            # we do this by setting the rate as the number of rides in a particular hour. 
            # this will be collected for each day of the week and analyzed. 
            groupedby_date = df_filtered_for_terminal.groupby('Timestamp_date')

            for datename, dategroup in groupedby_date:
                dayname = pd.Timestamp(datename).day_name()
                for hr, grp in dategroup.groupby('Timestamp_hour'):
                    dct[dayname][f'{hr}hr_rates'].append(grp.size)
            return dct
        self.rates = calc_station_rates(self, df, station_terminal_number)
        
    def quickstat(self, daystring):
        for k,v in self.rates[daystring].items(): 
            print(f"{k}:\t median: {np.median(v)} \t mean: {np.mean(v):0.4f} \t variance: {np.var(v):0.4f}") 
    
    def stats(self, daystring):
        df = pd.DataFrame()
        
        
        pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - MAIN  - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 



if __name__ == '__main__':
    # - - - Argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--barchart', help = 'activate barcharts', type=bool, default = False)
    parser.add_argument('--geoplot', help='activate geographic data map', type = bool, default = False)
    parser.add_argument('--testgeo', help='activate geographic data map function', type = bool, default = False)
    parser.add_argument('--dflim', help = 'limit the number of files used to build main df', type=int, default = 0)
    args = parser.parse_args()

    # - - - Parse the arguments into variable names
    show_barchart = args.barchart
    show_geomap = args.geoplot
    testgeo = args.testgeo
    dflim = args.dflim

    # - - - Print to console the args for visual verification
    print_args(args)
    
    # - - -Define the folder containing only data files (csv or txt)
    data_folder = "data/"
    df = pd_csv_group(data_folder, dflim)
    
    # - - - Program appears to hang while handling the remaining code base. Output a "I am thinking" status.
    print('Doing data science...')

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

    # - - - Create 'start time' and 'end time' columns after recasting to datetime objects.
    df['Start time'] =[x.time() for x in pd.to_datetime((df['Start date']))]     
    df['End time'] =[x.time() for x in pd.to_datetime((df['End date']))]     
    
    # - - - CLASS OBJECT INSTANTIATION: BIKEREPORT()
    # - - - Which bikes (by bike number) have been used the most (by duration)?
    most_used_bikes_10 = df[['Bike number', 'Duration']].groupby('Bike number').agg(sum).sort_values(by='Duration', ascending = False)[:10]
    
    # - - - Generate reports for each of the top ten most used bikes.
    show_bike_reports = False
    if show_bike_reports:
        for i in range(9):
            br = BikeReport(df, most_used_bikes_10.iloc[i].name)
            print(br)


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


    if show_barchart:
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

    if show_barchart:
        station_time_hist2_pop_morn_stations = station_super_dict(df, popular_morning_stations)
        station_time_hist2_pop_aft_stations = station_super_dict(df, popular_afternoon_stations)
        station_time_hist2_pop_eve_stations = station_super_dict(df, popular_evening_stations)
        
        # These barcharts need some serious devine intervention...   :/
        plot_popstations(popular_morning_stations, 'Morning')
        plot_popstations(popular_afternoon_stations, 'Afternoon')
        plot_popstations(popular_evening_stations, 'Evening')

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------


    if testgeo:
        #plot_geomap(popular_morning_stations, morning_rides, "Morning",hardstop=1000 )

        #plot_geomap(popular_morning_stations, morning_rides, "Morning",hardstop=500 )                                                                                                                           
        plot_geomap(popular_morning_stations.iloc[0], morning_rides, "Morning")





    # - - - End of program
    print('...done \n')