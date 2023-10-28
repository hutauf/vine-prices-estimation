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

    # Close the driver
    driver.quit()

    return source_code

def dump_db(db):
    json.dump(db, open("data/asininformation.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=serialize_datetime)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download order data.')
    parser.add_argument('file', help='Path to the CSV file with order data.')
    parser.add_argument('--start_date', type=valid_date, default='1970-01-01', help='The start date - format YYYY-MM-DD. Default is 1970-01-01.')
    parser.add_argument('--end_date', type=valid_date, default='2100-01-01', help='The end date - format YYYY-MM-DD. Default is 2100-01-01.')

    args = parser.parse_args()

    #load and filter pandas data:
    d = pandas.read_csv(args.file)
    total_purchases = d.shape[0]
    d = d[d['Order Status'] != 'Cancelled']
    d["Unit Price"] = pandas.to_numeric(d["Unit Price"], errors='coerce')
    d = d[d["Unit Price"] == 0.]
    try:
        d['Order Date'] = pandas.to_datetime(d['Order Date'], format='ISO8601').dt.date
    except:
        d['Order Date'] = pandas.to_datetime(d['Order Date']).dt.date
    d = d[(d['Order Date'] >= args.start_date) & (d['Order Date'] <= args.end_date)]

    print(f"found {d.shape[0]} of {total_purchases} total purchases in order history that might be potential Vine orders")
    print("starting download now")

    os.makedirs("data", exist_ok=True)
    db = {}
    with tqdm(d.iterrows(), total=d.shape[0]) as tbar:
        for index, row in tbar:
            asin = row['ASIN']
            product_name = row['Product Name']
            order_date = row['Order Date']
            db[asin] = [order_date, product_name]
            dump_db(db)
            tbar.set_description(f"Processing: {asin}")
            outname = f"data/keepa_{asin}.txt"
            if os.path.exists(outname):
                tqdm.write(f" *I* download keepa information for {asin} already done")
                continue
            url = f"https://keepa.com/#!product/3-{asin}"
            source_code = download_page(url)
            open(outname, "w", encoding="utf-8").write(source_code)
            tqdm.write(f" *I* download of keepa information for {asin} successful")
            time.sleep(1) # just to get some idle time and confuse the bot-protection

    print("done downloading data from keepa")
