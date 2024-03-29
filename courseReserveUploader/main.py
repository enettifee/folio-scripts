# -*- coding: utf-8 -*-
"""
Basic course reserve updater that can take a CSV list of barcodes and upload them to a course all at once.

Written January 2023.
"""

import json
import requests
import configparser
import csv

# basic function to ask for environment you are uploading to
def singleenvironment(configNames):
    environmentname = input("Which environment are we uploading reserves to? ")
    if environmentname in configNames:
        return environmentname
    else:
        sys.exit("can't recognize environment name!")

# read in configuration files for configparser
envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')
print(envConfig.sections())

# call function to ask for environment to upload courses to

uploadenvironment = ff.singleenvironment(envConfig.sections())

# set environment headers

uploadurl = envConfig[uploadenvironment]['okapi_url']

fetchHeaders = {
    'x-okapi-tenant': envConfig[uploadenvironment]['tenant_id'],
    'x-okapi-token': envConfig[uploadenvironment]['password']
}
postHeaders = {
    'x-okapi-tenant': envConfig[uploadenvironment]['tenant_id'],
    'x-okapi-token': envConfig[uploadenvironment]['password'],
    'Content-Type': 'application/json'
}

"""
Creating a reserve is a POST call to the API

/coursereserves/reserves

with JSON that looks like this:

{
  "courseListingId": -insert course listing id-,
  "copiedItem": {
      "barcode": -insert item barcode-
      }
}

There is no bulk upload API for course reserves, so the structure here is basically
1) construct the API URL;
2) get the course listing UUID;
3) open the file of barcodes;
4) iterate through the list of barcodes to construct the payload
5) send the API call to FOLIO

Note that the course listing UUID is not what appears in the URL when you view the course - it is stored in the underlying JSON of the course record,
which can be viewed through Chrome developer tools.

"""

# use the 'format' command to build the upload URL
uploadReserveUrl = '{}{}'.format(uploadurl, "/coursereserves/reserves")

# ask for the course listing via input and store it in a variable
courseListingIdForLoad = input("Please provide the UUID for the course listing we are adding items to ")

# ask for the file of barcodes
# this assumes a comma separated list with no newline characters, e.g
# barcode1,barcode2,barcode3,barcode4...

initialFile = open('test.csv', newline='', encoding='utf-8-sig')
barcode_file = csv.reader(initialFile, dialect='excel')

# now, make the payload for the API call and send it.
for each in barcode_file:
    payload = {} # initialize a Python dictionary to store the payload
    copiedItem = {} # initialize a Python dictionary for the barcode object
    for barcode in each: # the object out of the barcode file is a list; this iterates through the list to get each barcode
        payload['courseListingId'] = courseListingIdForLoad
        copiedItem['barcode'] = barcode
        payload['copiedItem'] = copiedItem
        requestPayload = json.dumps(payload) # change from python dictionary to JSON
        sendReserve = requests.post(uploadReserveUrl, headers=postHeaders, data=requestPayload)

print("script complete!")
