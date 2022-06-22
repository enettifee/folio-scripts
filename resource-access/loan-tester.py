## This is a very basic tool to allow you to provide FOLIO with a CSV file of settings UUIDs 
## which FOLIO then sends back and tells you what circulation policies would be applied. 
##
## It will be of most use to schools that are setting up their rules and want to run their scenarios 
## and see what would happen.
##
## Your input file should be in CSV format like so:
##
## patron_type_id,loan_type_id,item_type_id,location_id
## patrontypeUUID,loantypeUUID,itemtypeUUID,locationUUID
## ...
## ...
## ...
##
## "item_type" in this script is referring to what appears as "material type" in the UI - the API calls it
## item type, I think that is tech debt from very early project decisions.

import requests
import csv
import sys
from datetime import datetime

## Set up variables for use in the script
## If you are repurposing this for another institution, you'll want to add the 
## appropriate okapi URLs, tenant names, tokens, etc. and make sure
## that the appropriate points throughout the script have your variables.

# okapi environments that can be used
snapshotEnvironment = "https://folio-snapshot-okapi.dev.folio.org"
snapshot2Environment = "https://folio-snapshot-2-okapi.dev.folio.org"

# tenant names
snapshotTenant = "diku"
snapshot2Tenant = "diku"

# headers for use with forming API calls

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

## Now you can start asking for input from the person running the script
## They need to specify the name of the server they want to test on
##
## Again, if you are tweaking for another environment, you need to make appropriate
## updates here.

environment = input("What server do you want to test on? (snapshot, snapshot2)  ")

if environment == 'snapshot':
    testServer = snapshotEnvironment
    postHeaders = snapshotPostHeaders
    snapshotToken = input("provide the token for snapshot ")
elif environment == 'snapshot2':
    testServer = snapshot2Environment
    postHeaders = snapshot2PostHeaders
    snapshotToken = input("provide the token for snapshot 2 ")
else:
    print("Server environment not recognized.")
    sys.exit()

# Print start time for script - 
startTime = datetime.now()
print("Script starting at: %s" % startTime)

# fetch settings files to query in the script; makes things faster

# fetch patron groups
patronGroupsUrl = '{}{}'.format(testServer, '/groups?limit=1000')
patronGroupsRequest = requests.get(patronGroupsUrl, headers=postHeaders)
patronGroupsJson = patronGroupsRequest.json()

# fetch loan types
loanTypesUrl = '{}{}'.format(testServer, '/loan-types?limit=1000')
loanTypesRequest = requests.get(loanTypesUrl, headers=postHeaders)
loanTypesJson = loanTypesRequest.json()

# fetch material types
materialTypesUrl = '{}{}'.format(testServer, '/material-types?limit=1000')
materialTypesRequest = requests.get(materialTypesUrl, headers=postHeaders)
materialTypesJson = materialTypesRequest.json()

# fetch locations
locationsUrl = '{}{}'.format(testServer, '/locations?limit=1500')
locationsRequest = requests.get(locationsUrl, headers=postHeaders)
locationsJson = locationsRequest.json()

# fetch loan policies
loanPoliciesUrl = '{}{}'.format(testServer, '/loan-policy-storage/loan-policies?limit=500')
loanPoliciesRequest = requests.get(loanPoliciesUrl, headers=postHeaders)
loanPoliciesJson = loanPoliciesRequest.json()

# fetch notice policies
noticePoliciesUrl = '{}{}'.format(testServer, '/patron-notice-policy-storage/patron-notice-policies?limit=100')
noticePoliciesRequest = requests.get(noticePoliciesUrl, headers=postHeaders)
noticePoliciesJson = noticePoliciesRequest.json()

# fetch request policies
requestPoliciesUrl = '{}{}'.format(testServer, '/request-policy-storage/request-policies?limit=50')
requestPoliciesRequest = requests.get(requestPoliciesUrl, headers=postHeaders)
requestPoliciesJson = requestPoliciesRequest.json()

# fetch overdue policies
overduePoliciesUrl = '{}{}'.format(testServer, '/overdue-fines-policies?limit=100')
overduePoliciesRequest = requests.get(overduePoliciesUrl, headers=postHeaders)
overduePoliciesJson = overduePoliciesRequest.json()

# fetch lost item policies
lostItemPoliciesUrl = '{}{}'.format(testServer, '/lost-item-fees-policies?limit=100')
lostItemPoliciesRequest = requests.get(lostItemPoliciesUrl, headers=postHeaders)
lostItemPoliciesJson = lostItemPoliciesRequest.json()

# open the file with test information - assumes name of file is loan_tester.csv but that's easy to change
# 
# encoding = 'utf-8-sig' tells Python to compensate for Excel encoding
# first row should have four values - patron_type_id,	item_type_id,	loan_type_id,	location_id
# then you put in the values for each loan scenario as a row in the file
#
# values are specified in UUIDs, but output will be in friendly name.
# the API calls the material type id the "item type id" - tech debt artifact from early FOLIO, I think

initialFile = open('loan_tester.csv', newline='', encoding='utf-8-sig')

# create a python dictionary to store the results with friendly names that you want to put into a file
friendlyResults = {}

# turn your file of patron/loan/material type/location into python dictionary that can be
# used to query the APIs

testLoanScenarios = csv.DictReader(initialFile, dialect='excel')

for count, row in enumerate(testLoanScenarios):
    # provides a simple counter and output to know the script is still running
    print(count, row)
    
    # first thing is to pull the UUIDs; you'll need these to look up the friendly names, and to
    # correctly form the API call to see what policy comes back
    patron_type_id, loan_type_id, item_type_id, location_id = row["patron_type_id"], row["loan_type_id"],  row["item_type_id"], row["location_id"]

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

    # pull location friendly name - using location code since a lot of our location names have commas in them
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


    # now, you'll use the UUID values to query the APIs, get the results back, and then form
    # the full row in friendlyResults with the friendly names
    
    # first, let's make the URLs
    
    urlLoanPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/loan-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlRequestPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/request-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlNoticePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/notice-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlOverduePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/overdue-fine-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
    urlLostItemPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/lost-item-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)

    # now, check all of the policies.
    # 
    # you could make one giant loop for this, but I found that it seemed like I got a bit of a performance improvement by 
    # doing individual loops through the smaller chunks of data / discrete sections

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

    with open("friendlyOutput-%s.csv" % startTime.strftime("%d-%m-%Y-%H%M%S"), 'a', newline='') as output_file:
         test_file = csv.writer(output_file)
         test_file.writerow(friendlyResults.values())

# when the tester is finally done, give some basic time information so you 
# know how long it took        
endTime = datetime.now()
print("Script started at %s and ended at %s" % (startTime, endTime))

# close the initial file of scenarios
initialFile.close()
