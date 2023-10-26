import re, os
def tonumber(i):
    if "+" in i or "-" in i:
        return ""
    try:
        n = float(i[1:-1])
    except:
        return ""
    return n
    
db = {}
all_count = 0
for f in os.listdir(os.getcwd()):
    if not "keepa" in f:
        continue
    content = open(f, "r", encoding="utf-8").read()
    name = content.split("<title>")[-1].split("</title>")[0]
    prices = [j for j in [tonumber(i) for i in re.findall("€[^<]*\<", content)] if j]
    all_count += 1
    if len(prices) == 0:
        print("no price for", name)
        continue
    minprice = numpy.min(prices)
    meanprice = numpy.mean(prices)
    maxprice = numpy.max(prices)
    
    db[f] = [name, minprice, meanprice, maxprice]

print("found prices for %s of %s orders"%(len(db), all_count))

all_min = [db[f][1] for f in db]
all_mean = [db[f][2] for f in db]
all_max = [db[f][3] for f in db]
print("Sum of minimum price reported by keepa:")
print(sum(all_min), "€")

print("Sum of average price")
print(sum(all_mean), "€")

print("Sum of maximum price")
print(sum(all_max), "€")


