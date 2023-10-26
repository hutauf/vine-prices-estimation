import sys
if not sys.argv[1:]:
  print("usage: python download_data.py path_to_orderhistory.csv")
  exit()

import pandas
import os, time
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

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

fname = sys.argv[1]
d = pandas.read_csv(fname)
d_filtered = d[d["Unit Price"] == 0.]
asins = sorted(list(d_filtered["ASIN"]))
print("found %s potential Vine-Orders with price=0"%(len(asins)))
print("starting download now")

for asin in tqdm(asins):
    time.sleep(1) # just to get some idle time and confuse the bot-protection
    print(asin)
    outname = "keepa_%s.txt"%asin
    if os.path.exists(outname):
        print("download already done")
        continue
    url = "https://keepa.com/#!product/3-%s"%asin
    source_code = download_page(url)
    open(outname, "w", encoding="utf-8").write(source_code)

print("done downloading data from keepa")
