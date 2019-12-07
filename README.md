# Galvanize Capstone 1  
## EDA: Capital BikeShare Open Data 

The [Capital Bikeshare](https://capitalbikeshare.com) company rents bikes to its member customers and casual users in most metro areas of Washington DC. These bikes are equiped with basic tracking devices and accumulate a fair amount of data per ride. In this EDA excercise, we will perform some fairly basic statistical analyses focused on the assets (bikes) and the infrastructure (stations) central to the Capital Bikeshare business model, and make some well-informed and data-driven recommendations to the company. 


### About the Data
Each quarter, the company publishes updated datasets to [their website](https://capitalbikeshare.com/system-data), as CSV files for each month in the latest quarter. Data is available as far back as 2010, though for this analysis we will focus on the last two years. Even this relatively small subset of the data consists of around 6.5M rows of transaction data. While this may be quite small compared to 'big data', it is of adequate sample size for basic EDA and determining statistical trends. The data has no missing values or NaNs, as the transaction data are automatically collected and preformatted. The only modification to the data has been to remove test transactions and engineering runs by the Capital Bikeshare staff. Below is the list of the (original) nine columns/features of each transaction occurance (row) as well as breif descriptions.

**Data Features**
- Duration – Duration of trip _(type:int; units: seconds)_
- Start Date – Includes start date and time _(type:string; ex: '2018-05-01 00:00:00')_
- End Date – Includes end date and time _(type:string; ex: '2018-05-01 00:00:00')_
- Start Station – Includes starting station name and number _(type:string; ex: '3000 Connecticut Ave NW / National Zoo')_
- End Station – Includes ending station name and number _(type:string; ex: 'Maine Ave & 7th St SW')_
- Bike Number – Includes ID number of bike used for the trip _(type:string; ex: 'W22771')_
- Member Type – Indicates whether user was a "registered" member (Annual Member, 30-Day Member or Day Key Member) or a "casual" rider (Single Trip, 24-Hour Pass 3-Day Pass or 5-Day Pass) _(type:string; ex: 'Member' or 'Casual')_

**[Note]** Additionally, a new feature column was made during the EDA to transform the 'Start date' data type as a datetime() object. This allowed segmentation of transactions during various times of the day - categorized as 'morning', 'afternoon', and 'evening' rides. 


   Duration           Start date             End date  Start station number                                Start station  End station number                             End station Bike number Member type
0       679  2018-05-01 00:00:00  2018-05-01 00:11:19                 31302                 Wisconsin Ave & Newark St NW               31307  3000 Connecticut Ave NW / National Zoo      W22771      Member
1       578  2018-05-01 00:00:20  2018-05-01 00:09:59                 31232    7th & F St NW / National Portrait Gallery               31609                   Maine Ave & 7th St SW      W21320      Casual
2       580  2018-05-01 00:00:28  2018-05-01 00:10:09                 31232    7th & F St NW / National Portrait Gallery               31609                   Maine Ave & 7th St SW      W20863      Casual
3       606  2018-05-01 00:01:22  2018-05-01 00:11:29                 31104                  Adams Mill & Columbia Rd NW               31509                New Jersey Ave & R St NW      W00822      Member
4       582  2018-05-01 00:04:52  2018-05-01 00:14:34                 31129  15th St & Pennsylvania Ave NW/Pershing Park               31118                         3rd & Elm St NW      W21846      Member


|   |Duration  |Start date            | End date           |Start station number | Start station                             |End station number |End station                            |Bike number  |Member type       |
|---| -------- |:--------------------:| ------------------:| ------------------- |:-----------------------------------------:| -----------------:|--------------------------------------:|------------:|-----------------:|
|0  |   679    |2018-05-01 00:00:00   |2018-05-01 00:11:19 |31302                |Wisconsin Ave & Newark St NW               |31307              |3000 Connecticut Ave NW / National Zoo |W22771       |Member            |
|1  |   578    |2018-05-01 00:00:20   |2018-05-01 00:09:59 |31232                |7th & F St NW / National Portrait Gallery  |31609              |Maine Ave & 7th St SW                  |W21320       |Casual            |
|2  |   580    |2018-05-01 00:00:28   |2018-05-01 00:10:09 |31232                |7th & F St NW / National Portrait Gallery  |31609              |Maine Ave & 7th St SW                  |W20863       |Casual            |
|3  |   606    |2018-05-01 00:01:22   |2018-05-01 00:11:29 |31104                |Adams Mill & Columbia Rd NW                |31509              |New Jersey Ave & R St NW               |W00822       |Member            |
|4  |   582    |2018-05-01 00:04:52   |2018-05-01 00:14:34 |31129                |15th St & Pennsylvania Ave NW/Pershing Park|31118              |3rd & Elm St NW                        |W21846       |Member            |

