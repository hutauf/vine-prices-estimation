# vine-prices-estimation
Check prices for vine purchases on keepa. I assume you are using Windows and have Chrome installed.

# step 1
Go to https://www.amazon.de/hz/privacy-central/data-requests/preview.html and request your order data. (Meine Bestellungen)

# step 2
Download and unzip the data provided by Amazon. Check the Retail.OrderHistory-folders and look for the csv file that contains your Vine orders. Copy the path to this csv file.

# step 3
Install python, then 
´pip install -r requirements.txt´

# step 4
Run download_data.py <path_to_csv>

You can run ´python download_data.py --help´ to see possible filter options and reduce the amount of data being downloaded. Already downloaded keepa-pages will be skipped. Please make sure you have the permission from keepa to scrape their webpage before using this code.

The program will connect to keepa using selenium and download price information for your orders with value = 0€. It takes around 1 hour for 200 orders. For each item, a text file will be stored with the source code of the html page as well as the product price history in json file format.

# step 5
Run evaluate.py to show some stats and export an Excel sheet.

If you run ´python evaluate.py plot´ (needs matplotlib installed), it will create keepa-typical plots with your time of purchase for each ASIN.

