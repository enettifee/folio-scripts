#! /bin/python3 

## This is a very basic tool to allow you to provide FOLIO with a CSV file of settings UUIDs 
## which FOLIO then sends back and tells you what circulation policies would be applied.
##
## HOW TO RUN THE SCRIPT
##
## The script takes two command line arguments:
## 1. The name of the server from the config.ini file
## 2. The name of the input file, including path if relevant.
##
## E.g., if the name of my server in the config file is 'snapshot' and my filename is 'faculty_loan_tester.csv' then
## I would run this at the command line as
##
## ./loanTester.py snapshot faculty_loan_tester.csv
##
## FOLIO RELEASES: 
## Script should work with FOLIO releases for Lotus and later.
##
## INPUT FILE FORMAT:
##
## Your input file should be in CSV format like so:
##
## patron_type_id,loan_type_id,item_type_id,location_id, status_name
## patrontypeUUID,loantypeUUID,itemtypeUUID,locationUUID, item status
## ...
## ...
## ...
##
## "item_type" in this script is referring to what appears as "material type" in the UI - the API calls it
## item type, I think that is tech debt from very early project decisions.
##
## Note that the script includes item status in the input file even though item status is not referenced in 
## circulation rules. If you don't have access to item status in your input file, you might want to remove 
## those references. 
##
## USER PERMISSIONS
##
## You must run this as a user who has the following specific permissions:
##
## circulation.rules.loan-policy.get
## circulation.rules.overdue-fine-policy.get
## circulation.rules.lost-item-policy.get
## circulation.rules.request-policy.get
## circulation.rules.notice-policy.get
##
## These permissions are hidden by default, so you will need administrator access to assign these permissions to a user.

import requests
import csv
import sys
from datetime import datetime
import folioFunctions as ff
import configparser
import argparse

"""
Use config parser to open config-template.ini and read in
applicable configuration values to use with all of the requesting calls.
"""

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')


"""
next, we call a function to ask which server we are testing on
(this only runs on one FOLIO server)
"""

parser = argparse.ArgumentParser()
parser.add_argument('servername', type=str)
parser.add_argument('filename', type=str)
argsServer = parser.parse_args()
whichServer = argsServer.servername
inputFilename = argsServer.filename
print(inputFilename)

## whichServer = ff.asksingleenvironment()

"""
We know which server, so pull the relevant values from the config INI file.
"""

testServer = envConfig[whichServer]['okapi_url']

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
capture the start time of the script and print it on screen;
this is really helpful for being able to monitor what is going 
on. 

We will also use the start time as part of the filename for the
output file; this can be helpful when running this script a lot
in a short amount of time.
"""

# Print start time for script - 
startTime = datetime.now()
print("Script starting at: %s" % startTime)

# fetch settings files to query in the script; makes things faster
# fetch patron groups

patronGroupsJson = ff.fetchpatrongroups(testServer, fetchHeaders)

# fetch loan types
loanTypesJson = ff.fetchloantypes(testServer, fetchHeaders)

# fetch material types
materialTypesJson = ff.fetchmaterialtypes(testServer, fetchHeaders)

# fetch locations
locationsJson = ff.fetchlocations(testServer, fetchHeaders)

# fetch libraries
librariesJson = ff.fetchlibraries(testServer, fetchHeaders)

# fetch loan policies
loanPoliciesJson = ff.fetchloanpolicies(testServer, fetchHeaders)

# fetch notice policies
noticePoliciesJson = ff.fetchnoticepolicies(testServer, fetchHeaders)

# fetch request policies
requestPoliciesJson = ff.fetchrequestpolicies(testServer, fetchHeaders)

# fetch overdue policies
overduePoliciesJson = ff.fetchoverduepolicies(testServer, fetchHeaders)

# fetch lost item policies
lostItemPoliciesJson = ff.fetchlostpolicies(testServer, fetchHeaders)

"""
Open the file with your loan testing information (name 'loan_tester.csv' by default) and
then load it into a python CSV Dictionary object called "testLoanScenarios."

The encoding = 'utf-8-sig' tells Python to compensate for Excel encoding when parsing
the CSV.

"""

initialFile = open(inputFilename, newline='', encoding='utf-8-sig')
testLoanScenarios = csv.DictReader(initialFile, dialect='excel')


"""
Next, you create a Python dictionary called "friendlyResults" where the test loop code
will store the results - this then gets outputted into the CSV file that is the output of
the script.
"""

friendlyResults = {}

"""
finally, here comes the actual loop to run through and test your loan scenarios.

"""


for count, row in enumerate(testLoanScenarios):
    # provides a simple counter and output on the screen to know the script is still running
    print(count, row)
    
    # first thing is to pull the row from testLoanScenarios, and assign the UUID values to
    # the associated variables.
    #
    # if item status is not in your input file, you want to remove the part after row["location_id"]
    patron_type_id, loan_type_id, item_type_id, location_id = row["patron_type_id"], row["loan_type_id"],  row["item_type_id"], row["location_id"]

    # then, you're going to take each value, pull the human readable name, and put
    # it back in the row in place of the UUID values.

    # pull patron_type_id friendly name
    for i in patronGroupsJson['usergroups']:
        if i['id'] == patron_type_id:
            friendlyResults['patron_group'] = i['group']
    if not 'patron_group' in friendlyResults:
        friendlyResults['patron_group'] = "Patron group not found"


    # pull loan type friendly name
    for i in loanTypesJson['loantypes']:
        if i['id'] == loan_type_id:
            friendlyResults['loan_type'] = i['name']
    if not 'loan_type' in friendlyResults:
        friendlyResults['loan_type'] = "Loan type not found"
    

    # pull material type friendly name (API refers to it as item_type_id) 
    for i in materialTypesJson['mtypes']:
        if i['id'] == item_type_id:
            friendlyResults['material_type'] = i['name']
    if not 'material_type' in friendlyResults:
        friendlyResults['material_type'] = "Material type not found"

    # pull location friendly name - this is using location code since a
    # lot of Duke's location names have commas in them
    # which makes working with CSV a little too messy
    #
    # also pulling library friendly name so that it can be used in sorting/reviewing results in the
    # output file
    
    for i in locationsJson['locations']:
        if i['id'] == location_id: # once you find the location ....
            for j in librariesJson['loclibs']: # use the location to search your stored copy of the libraries Json
                if i['libraryId'] == j['id']: # to find the associated library
                    friendlyResults['library_name'] = j['name'] # and pull the name
            friendlyResults['location'] = i['code'] # finally, add the location code so that it shows up in that order in the output file.
    if not 'library_name' in friendlyResults:
        friendlyResults['libraryName'], friendlyResults['location'] = "Library not found", "Location not found"
    if not 'location' in friendlyResults:
        friendlyResults['location'] = "Location not found"

    # you're also going to add the item status, which is in the file already, as a friendly name.
    # if you're not using item status in your file, remove this line.
    
    # friendlyResults['status_name'] = item_status_name


    # now, you'll use the UUID values to query the APIs, get the results back, and then form
    # the full row in friendlyResults with the friendly names
    
    # first, let's create the URLs
    
    urlLoanPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/loan-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlRequestPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/request-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlNoticePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/notice-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlOverduePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/overdue-fine-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlLostItemPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/lost-item-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)

    # now, send a GET request to each URL - the return value will be the UUID for the circulation policy
    # that would be applied.
    # 
    # You could make one giant loop for this, but I found that it seemed like I got a bit of a performance improvement by
    # doing individual loops through the smaller chunks of data / discrete sections.

    postLoanPolicies = requests.get(urlLoanPolicy, headers=postHeaders)
    postLoanPoliciesJson = postLoanPolicies.json()
    for i in loanPoliciesJson['loanPolicies']:
        if i['id'] == postLoanPoliciesJson['loanPolicyId']:
            friendlyResults['loanPolicy'] = i['name']

    postRequestPolicies = requests.get(urlRequestPolicy, headers=postHeaders)
    postRequestPoliciesJson = postRequestPolicies.json()
    for i in requestPoliciesJson['requestPolicies']:
        if i['id'] == postRequestPoliciesJson['requestPolicyId']:
            friendlyResults['requestPolicy'] = i['name']
    
    postNoticePolicies = requests.get(urlNoticePolicy, headers=postHeaders)
    postNoticePoliciesJson = postNoticePolicies.json()
    for i in noticePoliciesJson['patronNoticePolicies']:
        if i['id'] == postNoticePoliciesJson['noticePolicyId']:
            friendlyResults['noticePolicy'] = i['name']
            
    postOverduePolicies = requests.get(urlOverduePolicy, headers=postHeaders)
    postOverduePoliciesJson = postOverduePolicies.json()
    for i in overduePoliciesJson['overdueFinePolicies']:
        if i['id'] == postOverduePoliciesJson['overdueFinePolicyId']:
            friendlyResults['overduePolicy'] = i['name']
            
    postLostItemPolicies = requests.get(urlLostItemPolicy, headers=postHeaders)
    postLostItemPoliciesJson = postLostItemPolicies.json()
    for i in lostItemPoliciesJson['lostItemFeePolicies']:
        if i['id'] == postLostItemPoliciesJson['lostItemPolicyId']:
            friendlyResults['lostItemPolicy'] = i['name']

    # Finally, take the results and add them to the row in the file where we're capturing the results.

    with open("friendlyOutput-%s.csv" % startTime.strftime("%d-%m-%Y-%H%M%S"), 'a', newline='') as output_file:
         test_file = csv.writer(output_file)
         test_file.writerow(friendlyResults.values())

# when the tester is finally done, give some basic time information so you 
# know how long it took        
endTime = datetime.now()
print("Script started at %s and ended at %s" % (startTime, endTime))

# close the initial file of scenarios
initialFile.close()

