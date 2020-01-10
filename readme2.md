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

![Bike station distribution across DC][fig1]

[fig1]:plots/bikestation_distribution.png "Plot name"

And infact we do see something of a concentration of bike rental stations in the downtown and high traffic areas of DC. But there are plenty of bike stations that are not located downtown, and (presumably) not in as heavily populated or high traffic areas. So it might be worth taking a look at where the most popular bike stations are in terms of rental volume. We can segment this further by looking at each station's rental volume in the morning, afternoon, and evening. 

![Top ten bike stations by time of day][fig2]

[fig2]:plots/top_ten_stations_by_time_of_day.png

![Popular Morning Stations for Starting a Ride][fig3]

[fig3]:plots/Figure_6.png



The immediately obvious trend we see is the volume of bike rentals across all of these stations seems to coincide with commuter rush hour times of 0800 (8am) and 1800 (6pm). Also, it seems the station with the highest volume of bike rentals by far is the one at Columbus Circle / Union Station. And this makes sense as Union station is a major transportation hub in DC - there is a large number of commuters that come in from outside of DC through that train station. But these commuters - and others who live within DC - still need to move through the city to reach their places of work. 

Lets see where these stations are. 
![Locations of high volume bike rental stations][fig4]

[fig4]:plots/higestvolumebikestations.png

It seems most are located just outside of the center of downtown. 

Another interesting thing to see is where the rented bikes start and where they endup. In this plot, a line is simply drawn from the station a bike was checked out to the station it was checked back into. Lets look just at the bikes checked out in the morning (4am-9am). 

![Spark plot][fig5]

[fig5]:plots/Figure_10.png

This makes it pretty easy to tell that many of the bikes checked out in the morning are generally migrating towards the downtown area. Especially from Union Station. 

Bike share is one way to get to the places of work. Another way is the metro subway station. It would be worth looking at the bike stations that are near Metro Rail stations and seeing their bike rental volume compared to bike stations that are not as "close" to Metro Rail stations. A higher volume of bike stations that are "near Metro rail" might indicate that bike rental customers commonly use bikes to connect to transit. For clarity, "volume of bike rentals" consideres only the stations and times where/when bikes rentals are initiated - not when they are returned to a bike dock. 
Let's take the GIS data that describes the Metro Rail Lines and Stations, and superimpose the bike stations. I can also identify and flag the bike stations that are within 200 meters of a Metro Rail station. 

![Bike station proximity to rail][fig6]

[fig6]:plots/bikestations_nearrail_and_notnearrail.png

![Closeup of bike stations near rail stations][fig7]

[fig7]: plots/bikestation_close_to_railstation.png

![ plot of only bike stations near rail][fig72]

[fig72]:plots/bikesnearrail2.png

If we collect the total number of bike rentals across our dataset of 25 million+ rows, and count those that are checked out at a bike station with a rail station within 200 meters against those that are checked out at bike stations farter than 200 meters from a rail station. Of course, there are fewer bike stations in close proximity to the rail stations - by about 9.8 times as many not near a rail station. 

Out of the 572 bike stations in the dataset...

> 519 _Bike Stations Not Near Rail_ = 91% of all bike stations
 
> 53 _Bike Stations Near Rail_ = 9% of all bike stations


So the "_Bike Stations Near Rail_" category should account for roughly one tenth of the total rides over the 9.5 years of data. But, looking at the total volume for each group, we see a very different story. 

Out of the 280 million bike rentals over the life of the dataset...

> 222.3M _Rental Volume Not Near Rail_ = 79% of Total Volume

> 59.7M _Rental Volume Near Rail_ = 21% of Total Volume

This really makes me want to divide the total volume of each group by its sample size to get a feel for how much more volume per station the "near rail" group does compared to the "not near rail" group. 

![rental count by category][fig8]

[fig8]:plots/rental_count_by_category.png

It seems the rental volume per station for each category tells a very different story about the bike rental volume. We could possibly generalize a conclusion from this that the bike stations that operate near a Metro Rail station tend to produce much higher bike rental volume than those stations that are farther away. The ratio here is about 2.63x for bike stations near a Metro Rail station on a per-station basis. 

## Bikeshare Rental Volume with Adjacent Bike Stations

Focusing now on just those stations located near a rail station, we might ask what happens when a bike station pops up near another. Over time, new stations have been placed around DC as the service has grown. Seeing the bike rental volume over time with two adjacent stations might be interesting. Did one station take bike rental volume from the other? 

I was able to find three such pairs of stations that are located near a Metro Rail station. In fact, there were several such pairs, which raises more questions. But we will focus on exploring the rental volume of the pairs over time. 

![adjacent stations rental volume PAIR 1][figpair1]

[figpair1]: plots/comparing_nearby_stations_volume1.png

![adjacent stations rental volume PAIR 1 map][figpair1map]

[figpair1map]: plots/comparing_nearby_stations_volume1map.png


![adjacent stations rental volume PAIR 2][figpair2]

[figpair2]: plots/comparing_nearby_stations_volume2.png

![adjacent stations rental volume PAIR 2 map][figpair2map]

[figpair2map]: plots/comparing_nearby_stations_volume2map.png


![adjacent stations rental volume PAIR 3][figpair3]

[figpair3]: plots/comparing_nearby_stations_volume3.png

![adjacent stations rental volume PAIR 3 map][figpair3map]

[figpair3map]: plots/comparing_nearby_stations_volume3map.png

Just from looking at these three samples we can learn a few things. First, there is a clear cyclic pattern in rental volume over the year. This makes more sense when we remember that winters in Washington DC can be quite cold, and the snow can make it quite dangerous to engage in bikeshare. Second, for each of these samples, which were drawn at random, we have in each case that when a new bike rental station is brought up near an existing one, it will eventually out perform the older one. 

In the first case, the new bike rental station easily out performed the old one within one year, and even appears to have kept pace with the trending growth of the older one. 

In case two, the preexisting bike station at 15th and K St. has been on a slight decline over the last four to six years. When the new bike station came online in mid 2010 it quickly stole rental volume share from the older one. The new station even had quite a spike in bike rental volume in the summer of its second full year of operation. 

In case three, we see accelerating growth of the new station at 14th and Irving St, whereas the old station at the intersection of 14th and Harvard St had been on a decline for two or three years when the new station was brought online. Once the new station was operational, it seems to have out performed on bike rental volume from the very beginning of its operation while the old station seems to have forfiet much of its rental volume share and has been costing along the last three years. 

## What we can learn from this EDA 
We've learned that there are a very large number of bike rentals occuring around peak rush hour times, that the most popular Capital Bikeshare rental stations are largely located just outside the periphery of downtown DC. We have also learned that the bike stations that are located near Metro Rail stations tend to produce a higher rental volume per station than those located farther away from rail stations. This is reasonable indication that the Capital Bikeshare service plays a significant role in connecting the commutes of those who work in the city. We have also learned that bike stations that are established near preexisting stations (where both are within 200m of a Metro Rail station) eventually out perform the preexisting station. It is reasonable to surmise that those responsible for planning the locations of new bike stations are aware of diminishing returns of prior stations and the opportunities for establishing new ones nearby. 

### Further Analysis
While not strictly a rigourous statistical hypothesis test, the rental volume proportions of bike stations located near and "not near" a metro rail station as well as the peak usage times seem to indicate that many of the bikeshare customers use the service for connecting their commute to/from their place of work.  A more rigorous statistical hypothesis test could compare the normalized rental volume per station category ("near" or "not near" rail stations). This normalization constant is the total capacity of each bike station. The trick is that this capacity has changed as the Captial Bikeshare service has planned and executed it's strategy on load balancing. With the data describing changes to capacity for each bike station over time, a rate of utilization can be parameterized and volume means by station per week aggregated for the "near rail" and "not near rail" categories. This normalization would allow for means of both categories to form a normal distribution. A hypothesis test using a two sample z test would yeild a zscore that can be translated to a p-value and compared to a significance threashold (likely 0.05). Based on the proportions of transaction totals above, it might be expected that the "near rail" bike stations would support an alternative hypothesis that this category out performs the "not near rail" bike station category. 

Additionally, it would be worth collecting data for the top five or so most popular electric scooter companies and analyzing the relationship (impact and market share growth) between the bikeshare and scooter transportation modes. 
