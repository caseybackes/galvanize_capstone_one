# Galvanize Capstone 1  
## EDA: Capitol BikeShare Open Data 



The [Capitol Bikeshare](https://Capitolbikeshare.com) transit system is a part of the DC Metro Transit system, which rents bikes to its member customers and casual users in most metro areas of Washington DC. These bikes are equiped with basic tracking devices and accumulate nine features of data per ride. In the EDA project, I will attempt to learn something interesting from this large store of data. 

![Capitol Bikeshare][fig0]

[fig0]: plots/capitolbikeshare.png "Capitol Bikeshare"

### About the Data
Each quarter, the company publishes updated datasets to [their website](https://Capitolbikeshare.com/system-data), as CSV files for each month in the latest quarter. While the actual data is stored on an AWS S3 bucket, it is available as far back as late 2010. These data amount to 26.5 million rows of bike rental data - more than enough to dig through and find something interesting. The data has no missing values or NaNs, as the transaction data are automatically collected and preformatted at time of sale. The only modification to the data has been to remove test transactions and engineering runs by the Capitol Bikeshare staff. Below is the list of the (original) nine columns/features of each transaction occurance (row) as well as breif descriptions.

**Data Features**
- Duration – Duration of trip _(type:int; units: seconds)_
- Start Date – Includes start date and time _(type:string; ex: '2018-05-01 00:00:00')_
- End Date – Includes end date and time _(type:string; ex: '2018-05-01 00:00:00')_
- Start Station – Includes starting station name and number _(type:string; ex: '3000 Connecticut Ave NW / National Zoo')_
- End Station – Includes ending station name and number _(type:string; ex: 'Maine Ave & 7th St SW')_
- Bike Number – Includes ID number of bike used for the trip _(type:string; ex: 'W22771')_
- Member Type – Indicates whether user was a "registered" member (Annual Member, 30-Day Member or Day Key Member) or a "casual" rider (Single Trip, 24-Hour Pass 3-Day Pass or 5-Day Pass) _(type:string; ex: 'Member' or 'Casual')_

**[Note]** Additionally, two new feature columns were made during the EDA. First was to transform values in the 'Start date' column into a different data type  - a datetime() object. This allowed segmentation of transactions during various times of the day - categorized as 'morning', 'afternoon', and 'evening' rides. Also, additional datasets were collected to introduce additional features to the primary dataset - specifically the latitude and longitude coordinates of the bike stations. Additional useful GIS datasets came from the OpenData.gov.dc website containing geographical boundary and street map lines - this dramatically helped visuallize the distribution of bike stations across DC. Finally, from the same source were additional GIS datasets describing the DC Metro Rail transit system. A tutorial of working with GIS data is outside the scope of this project, but the 'GEOMETRY' column from the shape files were the most helpful from the GIS datasets. Below is an example of the primary data in raw form without additional columns. 



|   |Duration  |Start date            | End date           |Start station number | Start station                             |End station number |End station                            |Bike number  |Member type       |
|---| -------- |:--------------------:| ------------------:| ------------------- |:-----------------------------------------:| -----------------:|--------------------------------------:|------------:|-----------------:|
|0  |   679    |2018-05-01 00:00:00   |2018-05-01 00:11:19 |31302                |Wisconsin Ave & Newark St NW               |31307              |3000 Connecticut Ave NW / National Zoo |W22771       |Member            |
|1  |   578    |2018-05-01 00:00:20   |2018-05-01 00:09:59 |31232                |7th & F St NW / National Portrait Gallery  |31609              |Maine Ave & 7th St SW                  |W21320       |Casual            |
|2  |   580    |2018-05-01 00:00:28   |2018-05-01 00:10:09 |31232                |7th & F St NW / National Portrait Gallery  |31609              |Maine Ave & 7th St SW                  |W20863       |Casual            |
|3  |   606    |2018-05-01 00:01:22   |2018-05-01 00:11:29 |31104                |Adams Mill & Columbia Rd NW                |31509              |New Jersey Ave & R St NW               |W00822       |Member            |
|4  |   582    |2018-05-01 00:04:52   |2018-05-01 00:14:34 |31129                |15th St & Pennsylvania Ave NW/Pershing Park|31118              |3rd & Elm St NW                        |W21846       |Member            |

### Capital Bikeshare Stations Across DC

Since the spatial information for each of the bike stations is accessbile, it would be nice to get an understanding of the spatial distribution of bike stations across DC. It would be unsurprising to find most of them concentrated near the more heavily populated areas of downtown. 

![Bike station distribution across DC][fig7]

[fig7]:plots/Figure_5.png


And infact we do see something of a concentration of bike rental stations in the downtown and high traffic areas of DC. But there are plenty of bike stations that are not located downtown, and (presumably) not in as heavily populated or high traffic areas. So it might be worth taking a look at where the most popular bike stations are in terms of rental volume per hour. Lets identify the top ten bike stations in total rental volume and then see their average performance over the course of the day.


![Popular Morning Stations for Starting a Ride][fig8]

[fig8]:plots/Figure_6.png


# Morning Commuters plot
![Where do the Morining Bike Commuters Go?][fig3]

[fig3]:plots/Figure_10.png



![Same as above plot, downsampled data set][fig5]

[fig5]:plots/Figure_16.png




### Below is actually just the most popular morning stations. 
#### You'll notice that the most popular bike station to pick up a bike is the Columbus Circle / Union Station. When people come in from the train, it seems they often pick up a bikeshare. 



## Notes to self: 
Also another bike share [data source](https://s3.amazonaws.com/tripdata/index.html) from NYC, with LAT/LONG DATA!

_(Which means less feature engineering in the inital EDA phase)_
