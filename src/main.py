import numpy as np 
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import os
import math
#import utm
import shapefile as shp
import seaborn as sns
from collections import OrderedDict
import geopandas as gpd 
from geopy.distance import distance
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
            data = pd.concat(df_list, axis=0, ignore_index=True, sort=False)
            print(f'{len(data)/1e6:0.2}M rows of data with {len(data.columns)} features/columns derived from {file_num+1} CSV files. ')
            return data
    data = pd.concat(df_list, axis=0, ignore_index=True, sort=False)
    print(f'{len(data)/1e6:0.2}M rows of data with {len(data.columns)} features/columns derived from {file_num+1} CSV files. ')
    return data

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
    mask_low = df[colname] >= start_time
    mask_hi = df[colname] <= end_time
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
    station_groups = df.groupby('ADDRESS')
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

def plot_geomap(popstation, daytime_rides, daytime,hardstop=False, metrolines=False, metrostations=False,title=None):
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
    metrolines (bool)
        load and plot the geometry for the metro rail routes
    metrostations (bool)
        load and plot the geometry for the metro rail stations

    Returns
    -------
    None
        Produces a GeoDataFrame plot. 
    """

    # - - - READ IN SHAPE FILE FOR BORDER OF DC
    # data source: https://opendata.dc.gov/datasets/23246020d6894453bdfcee00956df818_41
    wash_shp_path = '../misc/Washington_DC_Boundary/Washington_DC_Boundary.shp'
    gpd_washborder = gpd.read_file(wash_shp_path)
    
    # - - - READ IN SHAPE FILE FOR STREET MAP OF DC
    street_shp_path = '../misc/Street_Centerlines/Street_Centerlines.shp'
    gpd_street = gpd.read_file(street_shp_path)

    # - - - PLOT DC STREET LINES AND BORDER POLYGON 
    plt.style.use('ggplot')
    fig,ax = plt.subplots(figsize=(15,15))
    gpd_street.geometry.plot(ax = ax, color='k', linewidth=.25 )  
    gpd_washborder.geometry.plot(ax = ax, color = 'grey', linewidth  =.5, alpha = .3)

    # - - - if kwarg 'metro' is not set to False
    if metrolines:
        metro_lines = gpd.read_file('../misc/Metro_Lines/Metro_Lines.shp')
        c = metro_lines.NAME.values
        for num in range(len(metro_lines)-1):
            c= metro_lines.NAME[num]
            gpd.GeoSeries(metro_lines.iloc[num].geometry).plot(ax = ax, color = c, label=f'Metro Rail: {c.capitalize()} Line')
        ax.legend()
    
    if metrostations:
        metro_stations = gpd.read_file('../misc/Metro_Stations_in_DC/Metro_Stations_in_DC.shp')
        metro_stations.geometry.plot(ax = ax, color = 'w', label = 'Metro Rail Stations',zorder=4)
        ax.legend()


    # if there are fewer rows than the declared 'hardstop', change hardstop to False
    hardstop_cap = daytime_rides.size
    if hardstop > hardstop_cap:
        print(f'Given number of bikeshare transactions to plot (hardstop = {hardstop}) exceeds number available {hardstop_cap}!\nPlotting up to {hardstop_cap} transactions.')
        hardstop = False
    
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
    if title:
        ax.set_title(title, fontsize=20)
    else:
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
    # print(f'--testgeo \t{args.testgeo}')
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
        self.rides = df[df['TERMINAL_NUMBER']==station_terminal_number]
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
            cols_we_care_about = ['Start date', 'TERMINAL_NUMBER','Start time', 'End time' ]
            df_filtered_for_terminal = df[terminal_number_mask][cols_we_care_about].copy()
            df_filtered_for_terminal['Start date'] = df_filtered_for_terminal['Start date'].apply(lambda x: str(x))
            # extract and separate the date and the time from the timestamp
            df_filtered_for_terminal['Timestamp_date'] = df_filtered_for_terminal['Start date'].map(lambda x: x.split(' ')[0])
            df_filtered_for_terminal['Timestamp_hour'] = df_filtered_for_terminal['Start time'].map(lambda x: str(x.hour))
            
            # since all entries are now from the same station, drop the station number (its the same value all the way down).
            # we also no longer need the 'End time' or 'Start time', as we only needed the hour of the start time. 
            # df_filtered_for_terminal.drop(columns=['Start date','Start time', 'End time','TERMINAL_NUMBER'], inplace = True)
            df_filtered_for_terminal.drop(columns=['Start time', 'End time','TERMINAL_NUMBER'], inplace = True)
            
            # lets look at each date separately for what the ride rates are by hour. 
            # we do this by setting the rate as the number of rides in a particular hour. 
            # this will be collected for each day of the week and analyzed. 
            groupedby_date = df_filtered_for_terminal.groupby('Start date')

            for datename, dategroup in groupedby_date:
                dayname = pd.Timestamp(datename).day_name()
                for hr, grp in dategroup.groupby('Timestamp_hour'):
                    dct[dayname][f'{hr}hr_rates'].append(grp.size)
            return dct
        self.rates = calc_station_rates(self, df, station_terminal_number)
        
    def info(self, daystring):
        ''' returns dataframe of stats for the given bike station's mean, median, and varience of useage by hour for the given day in 'daystring'. '''
        
        data = [{'MEAN':(round(np.mean(val),3) if len(val)>0 else 0), \
            'MEDIAN':(round(np.median(val),3) if len(val)>0 else 0), \
            'VARIANCE':(round(np.var(val),3) if len(val)>0 else 0)} \
                for key,val in list(zip(self.rates[daystring].keys(), self.rates[daystring].values()))  ] 
        
        return pd.DataFrame(data, index = self.rates[daystring].keys() )

    def kde(self, colname= 'MEDIAN'):
        print('working kde plot...')
        station_df = self.rides[['Start date', 'TERMINAL_NUMBER']].copy()
        station_df['dayofweek'] = pd.to_datetime(station_df['Start date'].values).dayofweek
        station_df['hour'] = pd.to_datetime(station_df['Start date'].values).hour
        
        x = station_df['dayofweek']
        y = station_df['hour']
        g = sns.jointplot(x,y,kind='kde',color='blue',xlim=(-0.5,6.5),ylim=(0,23), space=0);
        tics = list(range(0,25,2))
        g.ax_joint.set_yticks(tics)  
        g.fig.suptitle(f"{colname.capitalize()} Bike Station Utilization \n {self.rides['Start station'].values[0]}") # can also get the figure from plt.gcf()
        g.set_axis_labels('Day of Week','Time of Day (0-24)' )
        g.ax_joint.set_xticklabels(['','Mon','Tue','Wen','Thu','Fri','Sut','Sun'])
        print(' ... done')
        return g

def plot_geoms(lines=False, metrostations=False, bikestations=False, title=None):
    # - - - READ IN SHAPE FILE FOR BORDER OF DC
    # data source: https://opendata.dc.gov/datasets/23246020d6894453bdfcee00956df818_41
    gpd_washborder = gpd.read_file('../misc/Washington_DC_Boundary/Washington_DC_Boundary.shp')
    
    # - - - READ IN SHAPE FILE FOR STREET MAP OF DC
    gpd_street = gpd.read_file('../misc/Street_Centerlines/Street_Centerlines.shp')

    # - - - PLOT DC STREET LINES AND BORDER POLYGON 
    plt.style.use('ggplot')
    fig,ax = plt.subplots(figsize=(10,10))
    gpd_street.geometry.plot(ax = ax, color='k', linewidth=.25 )  
    gpd_washborder.geometry.plot(ax = ax, color = 'grey', linewidth  =.5, alpha = .3)

    # - - - if kwarg 'metro' is not set to False
    if lines:
        metro_lines = gpd.read_file('../misc/Metro_Lines/Metro_Lines.shp')
        c = metro_lines.NAME.values
        for num in range(len(metro_lines)-1):
            c= metro_lines.NAME[num]
            gpd.GeoSeries(metro_lines.iloc[num].geometry).plot(ax = ax, color = c, label=f'Metro Rail: {c.capitalize()} Line')
        ax.legend()
    
    if metrostations:
        metro_stations = gpd.read_file('../misc/Metro_Stations_in_DC/Metro_Stations_in_DC.shp')
        metro_stations.geometry.plot(ax = ax, color = 'w', label = 'Metro Rail Stations',zorder=4)
        ax.legend()
    
    if bikestations:

        ax.scatter(station_locations.LONGITUDE.values,station_locations.LATITUDE.values, c='b',alpha=.4, marker='o',label='Captial Bikeshare Bikestations')
        ax.set_xlim(-77.13,-76.90)
        ax.set_ylim(38.79,39)
        plt.xlabel('Longitude ($^\circ$West)')
        plt.ylabel('Latitude ($^\circ$North)')
        ax.legend()
    if title:
        ax.set_title(title, fontsize=20)
    else:
        ax.set_title(f'Capital Bikeshare And Metro Rail Stations', fontsize=20)
    return ax

def popular_stations(df,time_start,time_stop, top_n=10):
    ''' given the data and time range, return the top ten most popular stations in that time range.
    time_start is a string of military time expressed as such: "0500", or "1830", or "2215"
    ''' 

    """Returns the popular bike stations for bike checkout for a given time range.
    Parameters
    ----------
    df (data frame)
        data frame containing the bike checkin/checkout transactions
    Returns
    -------
    data frame
        Columns: TERMINAL_NUMBER, RIDE_COUNT, LATITUDE, LONGITUDE
    """
    # parse and recast times from strings to datetime.time() objects
    hr_0 = time_start[0:2]
    min_0 = time_start[2:4]
    t_0 = dt.time(int(hr_0),int(min_0),0)
    hr_f = time_stop[0:2]
    min_f = time_stop[2:4]
    t_f = dt.time(int(hr_f), int(min_f),59)

    # filter the primary df by "Start time" column with values between (lower bound) t_0 and (upper bound) t_f
    df_time_filtered = time_filter(df, 'Start time', t_0, t_f)

    # group this filtered dataframe subset by terminal number from which bike is checked out from,
    # get the frequency via ".size()", 
    # reset the index, 
    # rename and sort by the bogus column to RIDE_COUNT and take the top ten occurances,
    # merge with the station locations dataframe to bring in lat/long of stations
    # and return the result.
    popular_daytime_stations = df_time_filtered.groupby('TERMINAL_NUMBER')\
        .size()\
        .reset_index()\
        .rename(columns={0:'RIDE_COUNT'})\
        .sort_values(by='RIDE_COUNT', ascending=False)[0:top_n]\
        .merge(station_locations, on='TERMINAL_NUMBER', how='left')
    return popular_daytime_stations     

def bikestations_near_railstations(max_distance=200, showplot=False):
    '''returns a filtered copy of station_locations dataframe where entries are bike stations that have at least one 
    rail station within 200m. Also returns the distances dictionary, with rail stations for keys and values are tuples
    of closeby bike stations (by terminal number) and distance to the at bikestation from the rail station. Also returns 
    the matplolib object for the line plot that visualizes the rail stations and any bike station whos radial distance is 
    less than 200m away. 
    '''

    bikestation_coords = list(zip(station_locations['LONGITUDE'].values,station_locations['LATITUDE'].values, station_locations['TERMINAL_NUMBER'].values))
    metro_stations = gpd.read_file('../misc/Metro_Stations_in_DC/Metro_Stations_in_DC.shp')
    rail_coords = list(zip(metro_stations.geometry.x,metro_stations.geometry.y, metro_stations.NAME))
    ''' for each Metro rail station, we'll determine which bike stations are less than 200m away. 
    A dictionary with keys as rail stations will have values that are a list of tuples -> (bikestation_terminal_number, distance from rail station) 
    '''
    distances = dict()
    if showplot:
        plot_geoms(lines=True, metrostations=True,bikestations=True)

    flagged_bikestations=list()
    lineplot = None
    for bs in bikestation_coords:
        for rs in rail_coords:
            # the distance function requires lat/long in reversed order than what I have it, so "reversed(X_coords)" is now implemented. 
            dist = int(distance(reversed(bs[0:2]),reversed(rs[0:2])).m)
            
            if dist <= max_distance:
                flagged_bikestations.append(bs[2])
                try:
                    distances[rs[2]].append((bs,dist))
                except KeyError as err:
                    distances[rs[2]]=list()
                    distances[rs[2]].append((bs,dist))
                if showplot:
                    x = [bs[0], rs[0]]
                    y = [bs[1], rs[1]]
                    lineplot =plt.plot(x,y,'g--',linewidth=.85)
                    plt.scatter(bs[0], bs[1],color='r')
    filtered_stations_df  = station_locations[station_locations.TERMINAL_NUMBER.isin(flagged_bikestations)].copy()
    filtered_stations_df.reset_index(inplace=True)
    filtered_stations_df.drop('index', axis=1,inplace=True)
    return filtered_stations_df,distances,lineplot

    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - MAIN  - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  

if __name__ == '__main__':
    # - - - Argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--barchart', help = 'activate barcharts', type=bool, default = False)
    parser.add_argument('--geoplot', help='activate geographic data map', type = bool, default = False)
    # parser.add_argument('--testgeo', help='activate geographic data map', type = bool, default = False)
    parser.add_argument('--dflim', help = 'limit the number of files used to build main df', type=int, default = 0)
    args = parser.parse_args()

    # - - - Parse the arguments into variable names
    show_barchart = args.barchart
    show_geomap = args.geoplot
    # testgeo = args.testgeo
    dflim = args.dflim

    # - - - Print to console the args for visual verification
    print_args(args)
    
    # - - -Define the folder containing only data files (csv or txt)
    data_folder = "../data/"
    df = pd_csv_group(data_folder, dflim)
    
    # - - - Program appears to hang while handling the remaining code base. Output a "I am thinking" status.
    print('Doing data science...')

    print('# - - - FEATURE AND DATA ENGINEERING - - - #')
    # the locations of the bike stations in lat/long are found in another dataset from Open Data DC:
    # https://opendata.dc.gov/datasets/capital-bike-share-locations;
    # detailed description of data from this file can be found here:
    # https://www.arcgis.com/sharing/rest/content/items/a1f7acf65795451d89f0a38565a975b3/info/metadata/metadata.xml?format=default&output=html
    station_locations_df = pd.read_csv('../misc/Capital_Bike_Share_Locations.csv')   

    # taking only relevant information from the data
    station_locations = station_locations_df[['TERMINAL_NUMBER', 'LATITUDE', 'LONGITUDE','ADDRESS']].copy()

    # we can now merge the new bikestation locations dataframe into the primary dataframe
    df=df.merge(station_locations, left_on='Start station number', right_on='TERMINAL_NUMBER')

    # - - - Create 'start time' and 'end time' columns after recasting to datetime objects.
    df['Start time'] =[x.time() for x in pd.to_datetime((df['Start date']))]     
    df['End time'] =[x.time() for x in pd.to_datetime((df['End date']))]     
    
    print('# - - - DATA CLEANING - - - #')
    # drop unnecessary columns 
    df.drop(['End date', 'Start station', 'End station', 'Member type'], axis = 1, inplace=True)
    # drop redundant time from 'start date' col
    df['Start date'] = df['Start date'].apply(lambda x: x.split(' ')[0])
    df['Start date'] = df['Start date'].apply(lambda x: dt.date(   int(x.split('-')[0]), int(x.split('-')[1]), int(x.split('-')[2]) ))
    df.drop('Start station number', axis=1, inplace=True)


    # - - - CLASS OBJECT INSTANTIATION: BIKEREPORT()
    # - - - Which bikes (by bike number) have been used the most (by duration)?
    print('# - - - BUILDING BIKE REPORT OBJECT - - - #')
    most_used_bikes_10 = df[['Bike number', 'Duration']].groupby('Bike number').agg(sum).sort_values(by='Duration', ascending = False)[:10]
    

    # - - - Generate reports for each of the top ten most used bikes.
    show_bike_reports = False
    if show_bike_reports:
        for i in range(9):
            br = BikeReport(df, most_used_bikes_10.iloc[i].name)
            print(br)

    # ADDRESS THE BUSINESS QUESTIONS
    # What are the most popular bike stations for starting a ride in :
    #   1) the morning (4am-9am)?
    #   2) the afternoon (9am-3pm)?
    #   1) the morning (3pm-Midnight)?
    # TODO [COMPLETE]: Define a function that returns the popular morning/afternoon/evening bike stations given a start string and stop string of military time.
    print('# - - - DETERMINING POPULAR BIKE STATIONS BY TIME OF DAY - - - #')

    popular_morning_stations =   popular_stations(df, "0400", "0900",top_n=10)
    popular_afternoon_stations = popular_stations(df, "0900", "1500",top_n=10)
    popular_evening_stations =   popular_stations(df, "1500", "2359",top_n=10)



    if show_barchart:
        print('# - - - GENERATING BAR CHART OF POPULAR STATION RENTAL VOLUME - - - #')

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

    popstations = list()
    popstations.append(list(popular_morning_stations.TERMINAL_NUMBER.values))
    popstations.append(list(popular_afternoon_stations.TERMINAL_NUMBER.values))
    popstations.append(list(popular_evening_stations.TERMINAL_NUMBER.values))
    popstations = [item for sublist in popstations for item in sublist] #thanks stack overflow
    popstations_df = station_locations[station_locations['TERMINAL_NUMBER'].isin(popstations)]
    plot_geoms(title='Highest Volume Bike Stations')
    for s in popstations:
        #sx = s['LATITUDE']
        slat = station_locations[station_locations['TERMINAL_NUMBER']==s]['LATITUDE'].values[0]
        slong = station_locations[station_locations['TERMINAL_NUMBER']==s]['LONGITUDE'].values[0]
        #print(slat,slong)
        sname = station_locations[station_locations['TERMINAL_NUMBER']==s]['ADDRESS'].values[0]
        plt.scatter(slong,slat,marker='o',label = sname)
    #plt.legend()
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    plt.show(block=False)

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------


    # Now build a dictionary for each station where the keys are the time(by hour)
    # and the values are the counts of rides for that hour for that station. 
    # Each station's dictionary will all be stored in a 'super dictionary'

    if show_barchart:
        print('# - - - PLOTTING POPULAR STATIONS BY TIME OF DAY - - - #')

        station_time_hist2_pop_morn_stations = station_super_dict(df, popular_morning_stations)
        station_time_hist2_pop_aft_stations = station_super_dict(df, popular_afternoon_stations)
        station_time_hist2_pop_eve_stations = station_super_dict(df, popular_evening_stations)
        
        # These barcharts need some serious devine intervention...   :/
        plot_popstations(popular_morning_stations, 'Morning')
        plot_popstations(popular_afternoon_stations, 'Afternoon')
        plot_popstations(popular_evening_stations, 'Evening')

    # - - - - 
    # Statistical Analysis: 
    #   Are the bike stations that are "close" to Metro rail stations used more
    #   in terms of bikes checked out over the year? 

    print('# - - - DETERMINING DISTANCE FROM EACH RAIL STATIONS BIKE STATIONS - - - #')

    # we need a distance formula for WTG coords. Enter geopy.distance FTW!
    # source: https://janakiev.com/blog/gps-points-distance-python/
    # for every rail station, find the bike stations that are less than 200m away. 
    bikestation_prox_railstation_df, distances_dict, pltimg = bikestations_near_railstations(max_distance =200, showplot=True)

    # The "bikestation_prox_railstation_df" effectively contains a filtered copy of the "station_locations" dataframe describing all bike stations. 
    # We can look at the median, mean, and IQR for each of these bike stations over (initially) the last year. 
    '''
    In:     len(station_locations)                                                                                                                                                                                                                              
    Out:    578    

     - Of the complete set of bike stations, how many are near a rail station? 
    
    In:     len(bikestation_prox_railstation)                                                                                                                                                                                                                              
    Out:    54
    
     - What is the difference between these two groups in terms of utilization over a year? 
    '''
    # lets look at the primary DF and filter by bike stations that have a rail station nearby (given by bikestation_prox_railstation_df)

    print('# - - - FILTERING MAIN DATAFRAME FOR BIKE STATIONS WITHIN 200m OF RAIL STATIONS - - - #')
    df_filtered_for_proximate_railstations = df[df['TERMINAL_NUMBER'].isin(bikestation_prox_railstation_df['TERMINAL_NUMBER'])] 
    df_time_filtered2019 = df_filtered_for_proximate_railstations[df_filtered_for_proximate_railstations['Start date'].between(dt.date(2018,10,31),dt.date(2019,12,31),inclusive=True)]                                            
    
    
    '''
    HYPOTHESIS TESTING CHECKPOINT: 
    We have two samples: bike stations near a rail station and bike stations that are not. 
    For each group, we want to get a mean of the sums of bike checkouts over the course of a day. 
    mean(sum(bike checkouts in a day) for day in data range)
    '''

    
    # of all bike stations(terminals), they are either "close to rail station" or not
    all_terminal_numbers = set(df.TERMINAL_NUMBER)
    terminals_near_rail = set(df_time_filtered2019.TERMINAL_NUMBER)
    terminals_not_near_rail = all_terminal_numbers - terminals_near_rail

    '''
    TUESDAY NIGHT:
    Lets avoid the "sum of bikes checked out per day" and instead focus on "sum of bikes checked out per station group"
    which gives us the total bike checkouts for each of the two groups over a one-year time span. 
    Now, since the sample sizes are drastically different (~10x different), we can divide by sample size and get an average 
    representing transaction count per station for each group. The question here: is the average transaction count per 
    bike station greater for those stations near Metro Rail (subway) stations or those with no rail station nearby? 
    '''
    print('# - - - DETERMIMING RATIO OF RENTAL VOLUME BETWEEN "NEAR RAIL" AND "NOT NEAR RAIL" BIKE STATIONS - - - #')

    transaction_total_not_near_rail = df[df['TERMINAL_NUMBER'].isin(terminals_not_near_rail)].size
    total_stations_not_near_rail = len(terminals_not_near_rail)

    transaction_total_near_rail = df[df['TERMINAL_NUMBER'].isin(terminals_near_rail)].size
    total_stations_near_rail = len(terminals_near_rail)

    # Ratio: (bike rentals near a rail station) to (bike rentals not near a rail station)
    station_group_ratio = transaction_total_near_rail / transaction_total_not_near_rail
    # >>> 0.268351
    # Which would be unremarkable if there were also 0.26 as many bike stations near rail stations as not. BUT...!
    # when we divide by sample size for each group we get 
    station_groups_ratio_per_station=(transaction_total_near_rail/total_stations_near_rail) / (transaction_total_not_near_rail/total_stations_not_near_rail) 
    # >>> 2.62781
    

    fig = plt.figure()
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)
    rental_count_by_station_cat = (transaction_total_near_rail,transaction_total_not_near_rail)
    rental_count_per_station_count_per_station_cat = (transaction_total_near_rail/total_stations_near_rail,transaction_total_not_near_rail/total_stations_not_near_rail)
    tick_loc = (1,2)

    ax1.bar(tick_loc, rental_count_by_station_cat)
    ax1.set_xticks(ticks=tick_loc)
    ax1.set_xticklabels(('Near Rail','Not Near Rail'))
    ax1.set_title('Rental Count by Station Category')

    ax2.bar(tick_loc, rental_count_per_station_count_per_station_cat)
    ax2.set_xticks(ticks=tick_loc)
    ax2.set_xticklabels(('Near Rail','Not Near Rail'))
    ax2.set_title('Rental Count Per Station by Station Category')

    plt.show(block=False)
    
    
    print('# - - - PLOTTING THE METRO STATION MAP AND 2019 BIKE STATIONS CLOSE TO RAIL  - - - #')

    # show the bike stations that are close (within 200m) to a rail station
    plot_geoms(lines=True, metrostations=True,bikestations=False)
    x = df_time_filtered2019.LONGITUDE.values
    y = df_time_filtered2019.LATITUDE.values
    plt.scatter(x,y,color='r',marker ="D", label="Bike Stations Near Rail")
    plt.legend()
    plt.show(block=False) 

    # show the utilization of each of the "near rail" bike stations over time
    # This plot shows the seasonal cycle throug the 9 years of data, highlighting the dramatic drop in bikeshare rentals during the winter. 
    
    print('# - - - DETERMINING THE WEEKLY VOLUME OF "NEAR RAIL" BIKE STATIONS ACROSS ALL OF DATASET (2010-2019) - - - #')

    stations_near_rail_df = df[df['TERMINAL_NUMBER'].isin(terminals_near_rail)] 
    weekly_sum_of_rentals_by_station_df = pd.DataFrame(index = [f'{yr}-{wknum}' for yr in range(2010,2020) for wknum in range(1,54) ],
    columns=[str(x) for x in sorted(list(terminals_near_rail))],data=0)
    
    for station in sorted(list(terminals_near_rail)):
        
        station_df = stations_near_rail_df[stations_near_rail_df['TERMINAL_NUMBER'] == station].copy().sort_values(by='Start date')
        station_df['Start date ordinal'] = station_df['Start date'].apply(lambda x: x.toordinal())
        grpby_dt = station_df.groupby('Start date ordinal')
        print(f'Aggregating daily usage for Station {station}')
        
        for daynum,group_df in grpby_dt:
            weeknum = dt.date.isocalendar(dt.date.fromordinal(daynum))[1] 
            yr =dt.date.isocalendar(dt.date.fromordinal(daynum))[0]
            index_for_df = f'{yr}-{weeknum}'
            weekly_sum_of_rentals_by_station_df[str(station)].loc[index_for_df]+=group_df.size
    
    # Since there are so many lines on top of each other, lets look at just a few that are close to each other. 
    # There are two stations near each other. Lets see how their bike rental activity compares over time. 
    print('# - - - COMPARING RENTAL VOLUME OF BIKE STATIONS IN CLOSE PROXIMITY OVER ALL OF DATASET TIME RANGE - - - #')
    
    station_terminal_pair1 = ['31650','31208']
    station_terminal_pair2 = ['31254','31291']
    station_terminal_pair3 = ['31124','31105']
    
    def compare_bikestations(station_terminal_pair, wk_start=0):
        '''station_terminal_pair: two station terminal numbers to compare visually
        wk - week number from 0 to 529'''
        station1 = station_locations[station_locations['TERMINAL_NUMBER']==int(station_terminal_pair[0])]
        station2 = station_locations[station_locations['TERMINAL_NUMBER']==int(station_terminal_pair[1])]
        station1_name = station_locations[station_locations['TERMINAL_NUMBER']==int(station_terminal_pair[0])].ADDRESS.values[0]
        station2_name = station_locations[station_locations['TERMINAL_NUMBER']==int(station_terminal_pair[1])].ADDRESS.values[0]

        # plot the geometry data for metrolines and metro stations with only two "close proximity" bike stations to compare rental volume
        plot_geoms(lines=True, metrostations=True, bikestations=False)   
        plt.scatter(station1.LONGITUDE, station1.LATITUDE,color='r',marker='o', label=station1.ADDRESS.values)
        plt.scatter(station2.LONGITUDE, station2.LATITUDE,color='b',marker='o', label=station2.ADDRESS.values)
        plt.legend()
        plt.show(block=False)
        
        fig,ax = plt.subplots()
        ax = weekly_sum_of_rentals_by_station_df[station_terminal_pair][wk_start::].plot() 
        ax.legend((station1_name,station2_name))
        plt.title('Comparing Rental Volume of Two Nearby Bike Stations')
        #ax.set_xticklabels((weekly_sum_of_rentals_by_station_df.index.values[0:-1:13]))   
        ax.set_xlabel('YEAR - #Week')
        ax.set_ylabel('Weekly Ride Count per Station')
        plt.show(block=False)
    
    compare_bikestations(station_terminal_pair1,wk_start=250)
    compare_bikestations(station_terminal_pair2,wk_start=250)
    compare_bikestations(station_terminal_pair3,wk_start=250)





    # - - - End of program
    print('...done \n')