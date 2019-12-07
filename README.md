# Galvanize Capstone 1: EDA: Capital BikeShare Open Data 

The [Capital Bikeshare](https://capitalbikeshare.com) company rents bikes to its member customers and casual users in most metro areas of Washington DC. These bikes are equiped with basic tracking devices and accumulate a fair amount of data per ride. In this EDA excercise, we will perform some fairly basic statistical analyses focused on the assets (bikes) and the infrastructure (stations) central to the Capital Bikeshare business model, and make some well-informed and data-driven recommendations to the company. 


## About the Data
Each quarter, the company publishes updated datasets to [their website](https://capitalbikeshare.com/system-data), as CSV files for each month in the latest quarter. Data is available as far back as 2010, though for this analysis we will focus on the last two years. Even this relatively small subset of the data consists of around 6.5M rows of transaction data. While this may be quite small compared to 'big data', it is of adequate sample size for basic EDA and determining statistical trends. The data has no missing values or NaNs, as the transaction data are automatically collected and preformatted. The only modification to the data has been to remove test transactions and engineering runs by the Capital Bikeshare staff. Below is the list of seven columns/features of each transaction occurance (row) as well as breif descriptions.

**Data Features**
- Duration – Duration of trip
- Start Date – Includes start date and time
- End Date – Includes end date and time
- Start Station – Includes starting station name and number
- End Station – Includes ending station name and number
- Bike Number – Includes ID number of bike used for the trip
- Member Type – Indicates whether user was a "registered" member (Annual Member, 30-Day Member or Day Key Member) or a "casual" rider (Single Trip, 24-Hour Pass 3-Day Pass or 5-Day Pass)

Additionally, a new feature column was made during the EDA to transform the 'Start date' data type as a datetime() object. This allowed segmentation of transactions during various times of the day - categorized as 'morning', 'afternoon', and 'evening' rides. 