#/usr/env/bin python3
# coding: utf-8

import pandas
import os
import time
import json
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import argparse
from datetime import datetime, date

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'. Expected format: YYYY-MM-DD.".format(s)
        raise argparse.ArgumentTypeError(msg)

def serialize_datetime(obj): 
    if isinstance(obj, date):
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

def download_page(url):
    driver = webdriver.Chrome()

    # Load the webpage
    driver.get(url)
    #wait 3 seconds.. not sure if time.sleep would also work, but this works:    
    delay = 3
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'some_nonexisting_id')))
    except TimeoutException:
        pass
    
    # Get the source code
    source_code = driver.page_source
    dataProduct = driver.execute_script("return dataProduct;")

    # Close the driver
    driver.quit()

    return source_code, dataProduct

def download_exists(asin):
    for entry in existing_downloads:
        if entry.endswith("json") and asin in entry:
            try:
                return datetime.fromtimestamp(float(entry.split("_")[-1].split(".")[0])).strftime("%Y-%m-%d %H:%M:%S")
            except:
                return "unknown date"


def dump_db(db):
    json.dump(db, open("data/asininformation.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=serialize_datetime)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download order data.')
    parser.add_argument('file', help='Path to the CSV file with order data.', nargs='+')
    parser.add_argument('--start_date', type=valid_date, default='1970-01-01', help='The start date - format YYYY-MM-DD. Default is 1970-01-01.')
    parser.add_argument('--end_date', type=valid_date, default='2100-01-01', help='The end date - format YYYY-MM-DD. Default is 2100-01-01.')

    args = parser.parse_args()

    #load and filter pandas data:
    alld = None
    total_purchasess = 0
    for f in args.file:
        print("working on input file", f)
        amazonorderhistory = False
        if f.endswith("csv"):
            d = pandas.read_csv(f)
            #check if it's an export from amazon order history plugin:
            if "description" in d.columns:
                amazonorderhistory = True
                d.rename(columns={'order id': 'Order ID'}, inplace=True)
                d.rename(columns={'order date': 'Order Date'}, inplace=True)
                d.rename(columns={'description': 'Product Name'}, inplace=True)
                d.rename(columns={'price': 'Unit Price'}, inplace=True)
                d['Unit Price'] = d['Unit Price'].str.replace('€', '').str.replace(',', '.')

        elif f.endswith("json"):
            d = pandas.read_json(f, orient='records')
        else:
            raise Exception("only csv and json supported yet")
        total_purchases = d.shape[0]
        total_purchasess += total_purchases
        if not amazonorderhistory:
            d = d[d['Order Status'] != 'Cancelled']
        d["Unit Price"] = pandas.to_numeric(d["Unit Price"], errors='coerce')
        d = d[d["Unit Price"] == 0.]
        try:
            d['Order Date'] = pandas.to_datetime(d['Order Date'], format='ISO8601').dt.date
        except:
            d['Order Date'] = pandas.to_datetime(d['Order Date']).dt.date
        d = d[(d['Order Date'] >= args.start_date) & (d['Order Date'] <= args.end_date)]

        if alld is None:
            alld = d
        else:
            #append it:
            alld = pandas.concat([alld, d], ignore_index=True)
        
        print(f"found {d.shape[0]} orders in {f}")

    print(f"found {alld.shape[0]} of {total_purchasess} total purchases in order history that might be potential Vine orders")
    print("starting download now")

    os.makedirs("data", exist_ok=True)
    existing_downloads = os.listdir("data")
    order_ids_used = []
    db = {}
    with tqdm(alld.iterrows(), total=alld.shape[0]) as tbar:
        for index, row in tbar:
            asin = row['ASIN']
            product_name = row['Product Name']
            order_date = row['Order Date']
            order_id = row["Order ID"]
            if order_id in order_ids_used:
                continue # make sure to not use an order ID twice
            order_ids_used.append(order_id)
            db[asin] = [order_date, product_name]
            dump_db(db)
            tbar.set_description(f"Processing: {asin}")
            
            if (time_of_download := download_exists(asin)):
                tqdm.write(f" *I* download keepa information for {asin} already done on {time_of_download}")
                continue
            url = f"https://keepa.com/#!product/3-{asin}"
            source_code, dataProduct = download_page(url)
            outname = f"data/keepa_{asin}_{time.time()}.txt"
            open(outname, "w", encoding="utf-8").write(source_code)
            json.dump(dataProduct, open(f"data/keepa_dataProduct_{asin}_{time.time()}.json", "w", encoding="utf-8"), ensure_ascii=False)
            tqdm.write(f" *I* download of keepa information for {asin} successful")
            time.sleep(1) # just to get some idle time and confuse the bot-protection

    print("done downloading data from keepa")
