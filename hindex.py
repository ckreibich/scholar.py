#! /usr/bin/env python
import json

def hindex(maxyear, yearlist, minyear=1980):
    hindex = 0

    # Calculate citation number for a given year
    paper = []
    for line in yearlist.split('\n'):
        citation = 0
        tab = json.loads(line)
        for year in tab.keys():
            if len(year) > 1 and int(year) >= minyear and int(year) <= maxyear:
                citation += tab[year]
        paper.append(citation)

    # Calculate h-index
    rank = 0
    for cite in sorted(paper, reverse=True):
        rank += 1
        if cite >= rank:
            hindex += 1
    return hindex


infile = '{"1920":30, "2010": 10, "2012": 15}\n{"2010": 8}\n{"2010": 5}\n{"2010": 3, "2012": 1}\n{"2010": 3}'

h = hindex(2010, infile)
print('H-index:        ' + str(h))

for date in range(2000, 2019):
    h = hindex(date, infile)
    print('H-index [' + str(date) + ']: ' + str(h))
