# vine-prices-estimation
check prices for vine purchases on keepa

# step 1
Go to https://www.amazon.de/hz/privacy-central/data-requests/preview.html and request your order data. (Meine Bestellungen)

# step 2
Download and unzip the data provided by Amazon. Check the Retail.OrderHistory-folders and look for the csv file that contains your Vine orders. Copy the path to this csv file.

# step 3
Install python, then pip install those modules: selenium, pandas, tqdm.

# step 4
Run download_data.py

This will connect to keepa using selenium and download price information for your orders with value = 0€. It takes around 1 hour for 200 orders. For each item, a text file will be stored with the source code of the html page.

# step 5
Run evaluate.py to show some stats.
