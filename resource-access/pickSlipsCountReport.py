# A very basic script that queries the pick-slip API with a list of service point IDs
# and returns the number of pick slips for each service point
#
# Erin Nettifee, 12-13-2022

import requests
import configparser

"""
If you wanted to run this from a command line like

pickSlipReport.py snapshot

You would need to include

import argparse
"""

"""
Use config parser to open config-template.ini and read in
applicable configuration values to use with all of the requesting calls.
"""

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')

"""
If you wanted to use the command line, you would use this:

parser = argparse.ArgumentParser()
parser.add_argument('servername', type=str)
argsServer = parser.parse_args()
whichServer = argsServer.servername
print(whichServer)
"""

"""
Ask for the environment name
"""

whichServer = input("What server are we querying for pickslips? ")

"""
Now that we know which server, pull the relevant info for the request call.
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
First, let's query for the service points on the server.
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
Next, let's call for the pick slips for each servicepoint.
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
