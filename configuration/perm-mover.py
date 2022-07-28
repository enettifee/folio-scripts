# -*- coding: utf-8 -*-
## 
## this is a simple script that lets you move library-created permission sets
## from one environment to another
##
## the output is a text file that saves the name of the set and the response from the final API call (either POST or PUT)

import requests
import json
import sys
from datetime import datetime

# declare okapi environments that can be used 
#
# if you are repurposing this for your institution, add appropriate variables here and into the next sections.
# 
# for testing purposes, it can be really helpful to keep the Snapshot variables in place.
snapshotEnvironment = "https://folio-snapshot-okapi.dev.folio.org"
snapshot2Environment = "https://folio-snapshot-2-okapi.dev.folio.org"

# declare tenant names
snapshotTenant = "diku"
snapshot2Tenant = 'diku'

# declare tokens
snapshotToken = ""
snapshot2Token = ""

# support checking whether a request fails on POST, if it does
# we will try a PUT to move updates over.
error_phrases = ["errors", "ERROR", "duplicate key"]

# headers for Snapshot
# we should provide both GET and POST headers, but it doesn't hurt anything to just use
# this set for both.

snapshotPostHeaders = {
    'x-okapi-tenant': snapshotTenant,
    'x-okapi-token': snapshotToken,
    'Content-Type': 'application/json'
}
snapshot2PostHeaders = {
    'x-okapi-tenant': snapshot2Tenant,
    'x-okapi-token': snapshot2Token,
    'Content-Type': 'application/json'
}

# ask to specify environment we are moving from and environment we are moving to

moveFrom = input("Which environment are we moving permission sets from? (snapshot, snapshot2) ")

if moveFrom == 'snapshot':
    fetchHeaders = snapshotPostHeaders
    moveFromEnv = snapshotEnvironment
elif moveFrom == 'snapshot2':
    fetchHeaders = snapshot2PostHeaders
    moveFromEnv = snapshot2Environment
else:
    print("unrecognized move from environment")
    sys.exit()

moveTo = input("Which environment are we moving permission sets to? (snapshot, snapshot2) ")
if moveFrom == moveTo:
    print("Can't be the same thing!")
    sys.exit()

if moveTo == 'snapshot':
    moveToEnv = snapshotEnvironment
    postHeaders = snapshotPostHeaders
elif moveTo == 'snapshot2':
    moveToEnv = snapshot2Environment
    postHeaders = snapshot2PostHeaders
else:
    print("Unrecognized move to environment")
    sys.exit()

# initialize a script start time to use in the output filename
startTime = datetime.now()

# initialize a Python dictionary to capture output
friendlyResults = {}

# fetch permission sets
# adding mutable == true to the GET URL fetches only the permission sets the library created in Settings > Users > Permission Sets
# you don't need to move the other permissions over.

urlGet = '{}{}'.format(moveFromEnv, "/perms/permissions?length=10000&query=(mutable==true)")
urlPost = '{}{}'.format(moveToEnv, "/perms/permissions")  # create variable for the POST URL

# fetch permission sets, change them to JSON, and then just get the actual permission records
# from the array of JSON returned to you
responsePermSets = requests.request("GET", urlGet, headers=fetchHeaders)
responseJson = responsePermSets.json()
responsePermSets = responseJson['permissions']

for a in responsePermSets:
    # remove a bunch of stuff that causes errors with the POST call; I'm sure there's a better way to do this
    del (a['metadata'])
    del (a['grantedTo'])
    del (a['childOf'])
    del (a['dummy'])
    del (a['deprecated'])
    print("sending perm set %s " % a['displayName'])
    payload = json.dumps(a)
    r = requests.post(urlPost, data=payload, headers=postHeaders)  # try a POST for your permission
    permName = a['displayName']
    friendlyResults[permName] = r.text  # save the API response in the friendlyResults file for later output
    if any(x in r.text for x in
           error_phrases):  # if the POST appears to have failed, try a PUT request and save the output
        permName = a['displayName']
        print("Sending %s as PUT request" % permName)
        urlPut = '{}{}{}'.format(moveToEnv, '/perms/permissions/', a['id'])
        rPut = requests.put(urlPut, data=payload, headers=postHeaders)
        friendlyResults[permName] = rPut.text

# write API output to a text file for review
with open("friendlyOutput-%s.txt" % startTime.strftime("%d-%m-%Y-%H%M%S"), 'a') as test_string_file:
    test_string_file.write(json.dumps(friendlyResults, indent=""))
