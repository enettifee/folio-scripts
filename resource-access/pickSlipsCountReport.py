# A very basic script that queries the pick-slip API with a list of service point IDs
# and returns the number of pick slips for each service point
#
# Erin Nettifee, 12-13-2022

import requests
import configparser

"""
If you wanted to run this from a command line like
> pickSlipReport.py snapshot

Instead of 
import configparser

You would add
import argparse

and these lines:
parser = argparse.ArgumentParser()
parser.add_argument('servername', type=str)
argsServer = parser.parse_args()
whichServer = argsServer.servername
print(whichServer)
"""

"""
Use config parser to open config-template.ini and read in
applicable configuration values to use with all of the requesting calls.
"""

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')

"""
Ask for the environment name
"""
whichServer = input("What server are we querying for pickslips? ")

"""
We assume that the provided servername corresponds to the name listed
in config-template.ini.

Once we know the right server, we pull the relevant info from config-template.ini
and use it to construct the variables for the API call.
"""

okapiServer = envConfig[whichServer]['okapi_url']

fetchHeaders = {
    'x-okapi-tenant': envConfig[whichServer]['tenant_id'],
    'x-okapi-token': envConfig[whichServer]['password']
}
postHeaders = {
    'x-okapi-tenant': envConfig[whichServer]['tenant_id'],
    'x-okapi-token': envConfig[whichServer]['password'],
    'Content-Type': 'application/json'
}

"""
Next, let's query for the service points on the server.
We grab the UUIDs and name and save them in a list.
"""

getServicePointsUrl = '{}{}'.format(okapiServer, "/service-points")
servicePointsRequest = requests.get(getServicePointsUrl, headers=fetchHeaders)
servicePointsJson = servicePointsRequest.json()

servicePointsInfo = []

for a in servicePointsJson["servicepoints"]:
    servicePoint = {}
    servicePoint["name"] = a["name"]
    servicePoint["id"] = a["id"]
    servicePointsInfo.append(servicePoint)

"""
Finally, for each service point, we:
1. Call for the pick slips associated to that service point;
2. Save the pick slips response as JSON;
3. Construct a python dictionary of the service point UUID, service point name, and the number of slips;
4. Save the dictionary to a Python list object 'pickSlipsCombinedList'.

Then we print the list to the screen.
"""

pickSlipsCombinedList = []

for each in servicePointsInfo:
    pickSlipReport = {}
    getPickSlipsUrl = '{}{}{}'.format(okapiServer, "/circulation/pick-slips/", each["id"])
    pickSlipsRequest = requests.get(getPickSlipsUrl, headers=fetchHeaders)
    pickSlipsRequestJson = pickSlipsRequest.json()
    pickSlipReport["servicePointId"] = each["id"]
    pickSlipReport["servicePointName"] = each["name"]
    pickSlipReport["numberOfSlips"] = pickSlipsRequestJson["totalRecords"]
    pickSlipsCombinedList.append(pickSlipReport)

print(pickSlipsCombinedList)
