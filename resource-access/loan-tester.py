## 6-15-2022 
## This script is a very basic tool to allow you to provide FOLIO with a sequence of settings UUIDs 
## which FOLIO then sends back and tells you what circulation policies would be applied. 
## It will be of most use to schools that are setting up their rules and want to run their scenarios 
## and see what would happen.
##
## Known issues:
## 1. Haven't yet added overdue or lost item policies to the API calls - there was a known issue with 
## permissions and the associated APIs, but it was only backported to Lotus (CIRC-1453) and the environment I built this
## on was still on Kiwi.
## 2. Better output handling - right now, it just dumps the rows into a text file, and you have to get it into
## Excel and use text to columns to get it to a reviewable format.
## 

import requests
import csv
import sys

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

# api calls
# this is where we specify the values we use in constructing API calls later on in the script
# there is a permissions issue with the test environment and the overdue and lost item policies API,
# so that is commented out until it can be resolved.

apiValues = {'loanPolicyId': '/circulation/rules/loan-policy?',
             'noticePolicyId': '/circulation/rules/notice-policy?', 'requestPolicyId': '/circulation/rules/request-policy?'}

policyNameApis = {'loanPolicyId': '/loan-policy-storage/loan-policies/',
                  'noticePolicyId': '/patron-notice-policy-storage/patron-notice-policies/', 'requestPolicyId': '/request-policy-storage/request-policies/'}

# there's a permission error here in Kiwi - let's just remove these for now and come back to it after I figure that out.
#
# '/circulation/rules/overdue-fine-policy?', '/circulation/rules/lost-item-policy?'}


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
    # provides a simple counter to know the script is still running
    print(count)
    
    # first thing is to pull the UUIDs; you'll need these to look up the friendly names, and to
    # correctly form the API call to see what policy comes back
    patron_type_id, loan_type_id, item_type_id, location_id = row["patron_type_id"], row["loan_type_id"],  row["item_type_id"], row["location_id"]

    # pull patron_type_id friendly name
    for i in patronGroupsJson['usergroups']:
        if i['id'] == patron_type_id:
            patronGroupFriendlyName = i['group']
            friendlyResults['patron_group'] = patronGroupFriendlyName

    # pull loan type friendly name
    for i in loanTypesJson['loantypes']:
        if i['id'] == loan_type_id:
            loanTypeFriendlyName = i['name']
            friendlyResults['loan_type'] = loanTypeFriendlyName

    # pull material type friendly name (API refers to it as item_type_id) 
    for i in materialTypesJson['mtypes']:
        if i['id'] == item_type_id:
            materialTypeFriendlyName = i['name']
            friendlyResults['material_type'] = materialTypeFriendlyName

    # pull location friendly name
    for i in locationsJson['locations']:
        if i['id'] == location_id:
            locationFriendlyName = i['name']
            friendlyResults['location'] = locationFriendlyName

    # now, you'll use the UUID values to query the APIs, get the results back, and then form
    # the full row in friendlyResults with the friendly names

    for each in apiValues:
        url = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, apiValues.get(each), 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
        postEach = requests.get(url, headers=postHeaders)
        postEachVar = postEach.json()
        if each == 'loanPolicyId':
            for i in loanPoliciesJson['loanPolicies']:
                if i['id'] == postEachVar['loanPolicyId']:
                    friendlyResults['loanPolicy'] = i['name']
        if each == 'noticePolicyId':
            for i in noticePoliciesJson['patronNoticePolicies']:
                if i['id'] == postEachVar['noticePolicyId']:
                    friendlyResults['noticePolicy'] = i['name']
        if each == 'requestPolicyId':
            for i in requestPoliciesJson['requestPolicies']:
                if i['id'] == postEachVar['requestPolicyId']:
                   friendlyResults['requestPolicies'] = i['name']
                   
        # Can't test these until I resolve the permissions issue, but still setting up framework for now.
        
        # if each == 'overdueFinePolicyId':
        #     for i in overduePoliciesJson['overdueFinePolicies']:
        #         if i['id'] == postEachVar['overdueFinePolicyId']:
        #             friendlyResults['overdueFinePolicies'] = i['name']       
        # if each == 'lostItemFeePolicyId':
        #     for i in lostItemPoliciesJson['lostItemFeesPolicies']:
        #         if i['id'] == postEachVar['lostItemFeePolicyId']:
        #             friendlyResults['lostItemPolicy'] = i['name']
                    
        

    # write finalized row to a text document - this needs to be better, but at a minimum you can
    # take the output and use Excel text-to-columns to make it reviewable

    with open('test-string.txt', 'a') as test_string_file:
        test_string_file.write(str(friendlyResults.values()) + '\n')
    



# close the initial file of scenarios
initialFile.close()
