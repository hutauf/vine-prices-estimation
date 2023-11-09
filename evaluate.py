#/usr/env/bin python3
# coding: utf-8

import sys
import os
import numpy
import numpy as np
from datetime import datetime
import xlsxwriter
import json
if "plot" in sys.argv:
    from matplotlib import pyplot as plt
    import matplotlib.dates as mdates

from tqdm import tqdm

def tonumber(i):
    if "+" in i or "-" in i:
        return ""
    try:
        n = float(i[1:-1])
    except:
        return ""
    return n


def formatted(csv_data, mintime=0):
    """ Tranlaste KeepaTime to timestamp and save as ((timestamp1, value1), ... (timestampN, valueN))."""
    if not csv_data:
        return tuple()
    timestamps = [(t + 21564000)*60 for t in csv_data[0::2]]
    values = csv_data[1::2]
    i = 0
    if mintime:
        for i, timestamp in enumerate(timestamps):
            if timestamp > mintime:
                break
        i = (i - 1) if i else 0
    return list(zip(timestamps[i:], values[i:]))

def only_timestamp_to_unix(keepa_timestamp):
    return (keepa_timestamp + 21564000)*60

def try_interpolation(x_data_in, y_data_in, x):
    x_data = []
    y_data = []
    for i in range(len(y_data_in)):
        if y_data_in[i] != -0.01:
            x_data.append(x_data_in[i])
            y_data.append(y_data_in[i])
    
    if len(x_data) == 0:
        return -0.01
    elif len(x_data) == 1:
        return y_data[0]

    # Ensure x is within the bounds of x_data
    x = np.clip(x, x_data[0], x_data[-1])

    # Find the index where x should be inserted to maintain the sorted order
    index = np.searchsorted(x_data, x)

    if index == 0:
        return y_data[0]
    elif index == len(x_data):
        return y_data[-1]
    else:
        x0, x1 = x_data[index - 1], x_data[index]
        y0, y1 = y_data[index - 1], y_data[index]
        return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

random_high_value = 1000000

if __name__ == "__main__":

    if "plot" in sys.argv:
        os.makedirs("plots", exist_ok=True)
        skipplot=False

    #load asin information as basis for calculation:
    asindb = json.load(open("data/asininformation.json", "r", encoding="utf-8"))

    db = {}
    all_count = len(asindb)
    datafiles = os.listdir("data")
    for asin in tqdm(asindb):
        buydate, name = asindb[asin]
        date_obj = datetime.strptime(buydate, "%Y-%m-%d")
        unix_timestamp = date_obj.timestamp()
        asinfiles = [i for i in datafiles if asin in i and i.startswith("keepa_dataProduct")]
        prices = []
        timed_price = -0.01
        if "plot" in sys.argv:
            if os.path.exists("plots/plot_%s.png"%asin):
                skipplot=True
            else:
                skipplot=False
                fig, ax = plt.subplots(1)

        for asinfile in asinfiles:
            content = json.load(open(os.path.join("data", asinfile), "r", encoding="utf-8"))
            #name = content.split("<title>")[-1].split("</title>")[0] # name is now extracted directly from amazon
            #prices += [j for j in [tonumber(i) for i in re.findall("€[^<]*\<", content)] if j]
            if not "csv" in content:
                print("issues with csv from %s"%asin)
                continue
            
            lastupdatetimestamp = only_timestamp_to_unix(content["lastUpdate"])

            restructured = formatted(content["csv"][0])
            timestamps, values = zip(*restructured)
            timestamps = list(timestamps) + [lastupdatetimestamp]
            values = list(values) + [values[-1]]
            values = numpy.array(values).astype("float")/100.
            if "plot" in sys.argv and not skipplot:
                tnew = []
                vnew = []
                for i in range(len(timestamps)):
                    tnew.append(timestamps[i])
                    vnew.append(values[i])
                    if i!=len(timestamps)-1:
                        tnew.append(timestamps[i+1])
                        vnew.append(values[i])
                vnew = numpy.array(vnew).astype("float")
                vnew[vnew<0] = numpy.nan
                tnew = [datetime.utcfromtimestamp(ts) for ts in tnew]
                plt.plot(tnew, vnew, label="amazon")

            prices += [i for i in list(values) if i>0]
            #look for a price at buy time:
            time_idx = numpy.searchsorted(timestamps, unix_timestamp)
            if time_idx == 0 or time_idx == len(timestamps):
                #nothing found
                if time_idx == 0:
                    time_idx = numpy.searchsorted(timestamps, unix_timestamp + 3600*24) #assume the order wasn't done at 0:00 but 23:59:59..
                    if time_idx!=0:
                        timed_price = values[time_idx-1]
            else:
                timed_price = values[time_idx-1]

            if timed_price == -0.01: #still nothing found:
                timed_price = try_interpolation(timestamps, values, unix_timestamp)

            #also check marketplace price:
            restructured = formatted(content["csv"][1])
            timestamps, values = zip(*restructured)
            timestamps = list(timestamps) + [lastupdatetimestamp]
            values = list(values) + [values[-1]]
            values = numpy.array(values).astype("float")/100.
            if "plot" in sys.argv and not skipplot:
                tnew = []
                vnew = []
                for i in range(len(timestamps)):
                    tnew.append(timestamps[i])
                    vnew.append(values[i])
                    if i!=len(timestamps)-1:
                        tnew.append(timestamps[i+1])
                        vnew.append(values[i])
                vnew = numpy.array(vnew).astype("float")
                vnew[vnew<0] = numpy.nan
                tnew = [datetime.utcfromtimestamp(ts) for ts in tnew]
                plt.plot(tnew, vnew, label="marketplace")
            #look for a price at buy time:
            time_idx = numpy.searchsorted(timestamps, unix_timestamp)
            if time_idx == 0 or time_idx == len(timestamps):
                #nothing found
                if time_idx == 0:
                    time_idx = numpy.searchsorted(timestamps, unix_timestamp + 3600*24) #assume the order wasn't done at 0:00 but 23:59:59..
                    if time_idx!=0:
                        timed_price = values[time_idx-1] if timed_price==-0.01 else numpy.min([timed_price, values[time_idx-1]])
            else:
                timed_price = values[time_idx-1] if timed_price==-0.01 else numpy.min([timed_price, values[time_idx-1]])

            if timed_price == -0.01: #still nothing found:
                timed_price = try_interpolation(timestamps, values, unix_timestamp)

            prices += [i for i in list(values) if i>0]

        if "plot" in sys.argv and not skipplot:
            plt.axvline(datetime.utcfromtimestamp(unix_timestamp), color="k", label="buy time")
            plt.legend(loc=0)

            # Format the x-axis with a DateFormatter
            date_format = mdates.DateFormatter('%Y-%m-%d')
            ax.xaxis.set_major_formatter(date_format)

            # Optionally, rotate the x-axis labels for better readability
            plt.xticks(rotation=45)

            plt.xlabel("date")
            plt.ylabel("price [Euro]")
            plt.tight_layout()
            plt.savefig("plots/plot_%s.png"%asin)
            plt.close("all")

        if len(prices) == 0:
            print("no price for", name)
            prices = [random_high_value]
        
        minprice = numpy.min(prices)
        meanprice = numpy.mean(prices)
        maxprice = numpy.max(prices)
        
        db[asin] = [buydate, name, asin, minprice, meanprice, maxprice, timed_price]

    print("found prices for %s of %s orders"%(len([i for i in db if db[i][-1] != random_high_value]), all_count))

    all_min = [db[f][3] for f in db if db[f][3]!=random_high_value]
    all_mean = [db[f][4] for f in db if db[f][4]!=random_high_value]
    all_max = [db[f][5] for f in db if db[f][5]!=random_high_value]
    #all_timed = [db[f][6] for f in db if db[f][6]!=random_high_value]

    print("Sum of minimum price reported by keepa:")
    print(sum(all_min), "€")

    print("Sum of average price")
    print(sum(all_mean), "€")

    print("Sum of maximum price")
    print(sum(all_max), "€")

    print("writing out report")

    # Assuming your dictionary looks like this:
    dictionary = db

    # Create a new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook('output.xlsx')
    worksheet = workbook.add_worksheet()

    # Write the headers.
    headers = ['Date', 'Name', 'ASIN', 'Minimum Price', 'Mean Price', 'Max Price', 'Price at Order', 'Condition', 'Value']
    worksheet.add_table('A4:I{}'.format(len(dictionary) + 100), {'columns': [{"header": header} for header in headers]})

    
    #for i, header in enumerate(headers):
    #    worksheet.write(3, i, header)

    # Write the data from the dictionary to the Excel file.
    for row, (key, values) in enumerate(dictionary.items(), start=4):
        for col, value in enumerate(values):
            worksheet.write(row, col, value if value not in [-1] else -0.01)
        # Set the condition to "unknown" by default.
        worksheet.write(row, len(values), "unknown")
        # Set the value formula.
        worksheet.write_formula(row, len(values) + 1,
                                '=IF(OR(H{}="unknown", H{}="brand new"), IF(G{}<0, D{}, G{}), IF(H{}="in use", $B$1*IF(G{}<0, D{}, G{}), 0))'.format(row + 1, row + 1, row + 1, row + 1, row + 1, row + 1, row + 1, row + 1, row + 1))

    # Write the summary formulas in the header section.
    worksheet.write_formula('D1', '=SUM(D4:D{})'.format(len(dictionary) + 100))
    worksheet.write_formula('E1', '=SUM(E4:E{})'.format(len(dictionary) + 100))
    worksheet.write_formula('F1', '=SUM(F4:F{})'.format(len(dictionary) + 100))
    worksheet.write_formula('G1', '=SUM(G4:G{})'.format(len(dictionary) + 100))
    worksheet.write_formula('I1', '=SUM(I4:I{})'.format(len(dictionary) + 100))
    worksheet.write('C1', 'Sums =')
    worksheet.write('A1', 'use factor =')
    worksheet.write('B1', 0.5)
    
    worksheet.set_column(1, 1, 20)  # Width of columns B:D set to 30.
    worksheet.set_column(2, 2, 15)  # Width of columns B:D set to 30.
    worksheet.set_column(0, 0, 11)  # Width of columns B:D set to 30.
    possible_values = ["unknown", "in use", "trashed", "defect", "returned", "brand new", "consumed"]
    worksheet.data_validation('G5:G{}'.format(len(dictionary) + 100), {'validate': 'list',
                                  'source': possible_values})

    # Close the workbook.
    workbook.close()
