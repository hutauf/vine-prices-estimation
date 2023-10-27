#/usr/env/bin python3
# coding: utf-8

import re
import os
import numpy
import xlsxwriter
import pandas
import json
from tqdm import tqdm

def tonumber(i):
    if "+" in i or "-" in i:
        return ""
    try:
        n = float(i[1:-1])
    except:
        return ""
    return n

random_high_value = 1000000

if __name__ == "__main__":

    #load asin information as basis for calculation:
    asindb = json.load(open("data/asininformation.json", "r", encoding="utf-8"))

    db = {}
    all_count = len(asindb)
    datafiles = os.listdir("data")
    for asin in tqdm(asindb):
        buydate, name = asindb[asin]
        asinfiles = [i for i in datafiles if asin in i]
        prices = []
        for asinfile in asinfiles:
            content = open(os.path.join("data", asinfile), "r", encoding="utf-8").read()
            #name = content.split("<title>")[-1].split("</title>")[0] # name is now extracted directly from amazon
            prices += [j for j in [tonumber(i) for i in re.findall("€[^<]*\<", content)] if j]

        if len(prices) == 0:
            print("no price for", name)
            prices = [random_high_value]
        
        minprice = numpy.min(prices)
        meanprice = numpy.mean(prices)
        maxprice = numpy.max(prices)
        
        db[asin] = [buydate, name, asin, minprice, meanprice, maxprice]

    print("found prices for %s of %s orders"%(len([i for i in db if db[i][-1] != random_high_value]), all_count))

    all_min = [db[f][3] for f in db if db[f][3]!=random_high_value]
    all_mean = [db[f][4] for f in db if db[f][4]!=random_high_value]
    all_max = [db[f][5] for f in db if db[f][5]!=random_high_value]
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
    headers = ['Date', 'Name', 'ASIN', 'Minimum Price', 'Mean Price', 'Max Price', 'Condition', 'Value']
    worksheet.add_table('A4:H{}'.format(len(dictionary) + 100), {'columns': [{"header": header} for header in headers]})

    
    #for i, header in enumerate(headers):
    #    worksheet.write(3, i, header)

    # Write the data from the dictionary to the Excel file.
    for row, (key, values) in enumerate(dictionary.items(), start=4):
        for col, value in enumerate(values):
            worksheet.write(row, col, value)
        # Set the condition to "unknown" by default.
        worksheet.write(row, len(values), "unknown")
        # Set the value formula.
        worksheet.write_formula(row, len(values) + 1,
                                '=IF(OR(G{}="unknown", G{}="brand new"), D{}, IF(G{}="in use", $B$1*D{}, 0))'.format(row + 1, row + 1, row + 1, row + 1, row + 1))

    # Write the summary formulas in the header section.
    worksheet.write_formula('D1', '=SUM(D4:D{})'.format(len(dictionary) + 100))
    worksheet.write_formula('E1', '=SUM(E4:E{})'.format(len(dictionary) + 100))
    worksheet.write_formula('F1', '=SUM(F4:F{})'.format(len(dictionary) + 100))
    worksheet.write_formula('H1', '=SUM(H4:H{})'.format(len(dictionary) + 100))
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
