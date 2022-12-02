"""
Basic python script to authenticate to a FOLIO instance and produce a CSV file with information
about items currently on reserve for a defined reserves term.
"""

import json
import requests
import configparser
import csv
from datetime import datetime


# read in configuration files
envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')
print(envConfig.sections())

folioenv = input("Which environment are we retrieving course information from? ")
fetchserver = envConfig[folioenv]['okapi_url']

fetchHeaders = {
    'x-okapi-tenant': envConfig[folioenv]['tenant_id'],
    'x-okapi-token': envConfig[folioenv]['password']
}

# retrieve the current course terms from the FOLIO instance
termsurl = '{}{}'.format(fetchserver, '/coursereserves/terms?limit=100')
terms = requests.get(termsurl, headers=fetchHeaders)
termsjson = terms.json()

# ask which term they want to get course lists for
whichterm = input("Which term should we fetch reserves for? ")
for i in termsjson['terms']:
    if i['name'] == whichterm:
        termId = i['id']

# fetch the courses with the courselisting object for the specified term
coursesurl = '{}{}{}{}'.format(fetchserver, '/coursereserves/courses?limit=10000&query=(courseListing.termId=', termId, ')' )
courses = requests.get(coursesurl, headers=fetchHeaders)
coursesvalue = courses.json()
coursesjson = coursesvalue["courses"]

# fetch the reserves with the courseListingId for the specified term
reservesurl = '{}{}{}{}'.format(fetchserver, '/coursereserves/reserves?expand=*?limit=10000&query=(courseListing.termId=', termId, ')' )
reserves = requests.get(reservesurl, headers=fetchHeaders)
reservesvalue = reserves.json()
reservesjson = reservesvalue["reserves"]

# loop through each reserve object returned and print information about the reserve and the associated course

reservesInfoTest = {}
reservesInfoTestList = []

# use datetime to produce a random filename - I'm sure there are better ways to do this.
filetime = datetime.now()

# each item in reservejson represents an item on reserve for the specified term.
# here, we initialize a dictionary file to store information about the reserve, pull out
# specific information, and store it in that dictionary file. 
# 
# then, we dump the contents of that dictionary file into the CSV that is ultimately produced by the script.

for each in reservesjson:
    reservesInfoTest = {}
    reservesInfoTest["id"] = each["id"]
    reservesInfoTest["itemBarcode"] = each["copiedItem"]["barcode"]
    reservesInfoTest["title"] = each["copiedItem"]["title"]
    reservesInfoTest["courseListingId"] = each["courseListingId"]
    for course in coursesjson:
        if course["courseListingId"] == reservesInfoTest["courseListingId"]:
            reservesInfoTest["courseName"] = course["name"]
            reservesInfoTest["departmentName"] = course["departmentObject"]["name"]
            break
        else:
            reservesInfoTest["courseName"] = "not found"
    reservesInfoTestList.append(reservesInfoTest)


    with open("friendlyOutput-%s.csv" % filetime.strftime("%d-%m-%Y-%H%M%S"), 'a', newline='') as output_file:
        test_file = csv.writer(output_file)
        test_file.writerow(reservesInfoTest.values())

print(reservesInfoTestList)
