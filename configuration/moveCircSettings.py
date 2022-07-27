#### this is a basic python script
#### that lets you move different types of settings between FOLIO environments.
#### the primary way this would likely be used would be to support configuring circulation rules on a development environment
#### and then moving them to another environment for testing.
####
#### Known issues / areas for improvement
#### 1. Material type isn't included, but could easily be added.
#### 2. The token has to be put into the script when it runs; that's obviously not great and needs to be improved. 
#### 3. It would be nice to have a better way to ask for what pieces you want to move instead of one by one.
####
#### Erin Nettifee, 6-16-2022



import requests
import json
import sys


# declare okapi environments that can be used. If you want to use this in your local environments, you should 
# add appropriate variables here and through the next sections.
snapshotEnvironment = "https://folio-snapshot-okapi.dev.folio.org"
snapshot2Environment = "https://folio-snapshot-2-okapi.dev.folio.org"

# declare tenant names
snapshotTenant = "diku"
snapshot2Tenant = 'diku'

# declare tokens
snapshotToken = ""
snapshot2Token = ""

### provide a list of API calls to be used in GETs and POSTs, with limits to ensure all policies are fetched.

apiValues = {'loanPolicies': '/loan-policy-storage/loan-policies?limit=100', 'fixedDueDateSchedules': '/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=100',
            'patronNoticePolicies': '/patron-notice-policy-storage/patron-notice-policies?limit=100', 'requestPolicies': '/request-policy-storage/request-policies?limit=100'}

## the fine APIs are listed separately because I need to loop through them a bit differently to remove
## the metadata object

fineApiValues = { 'overdueFinePolicies': '/overdue-fines-policies', 'lostItemFeePolicies' : '/lost-item-fees-policies'}

## listed separately - they might not have to be, but I think it's a bit clearer at least for now

locationApiValues = { 'locinsts': '/location-units/institutions?limit=100', 'loccamps': '/location-units/campuses?limit=100', 'loclibs': '/location-units/libraries?limit=100', 'locations': '/locations?limit=1000'}

## PUT values, to use in forming API calls if a particular config already exists on the moveToEnv

apiPutValues = {'loanPolicies': '/loan-policy-storage/loan-policies/', 'fixedDueDateSchedules': '/fixed-due-date-schedule-storage/fixed-due-date-schedules/',
                'patronNoticePolicies': '/patron-notice-policy-storage/patron-notice-policies/', 'requestPolicies': '/request-policy-storage/request-policies/',
                'locinsts': '/location-units/institutions/', 'loccamps': '/location-units/campuses/', 'loclibs': '/location-units/libraries/', 'locations': '/locations/',
                'overdueFinePolicies': '/overdue-fines-policies/', 'lostItemFeePolicies': '/lost-item-fees-policies/'}

# This supports checking for errors with the POST request and trying again with PUT
# the APIs present errors in different ways, depending on the module

error_phrases = ["errors", "ERROR", "duplicate key"]

# headers for Snapshot
# you would add headers here for your own institution's instance if needed

snapshotPostHeaders={
    'x-okapi-tenant': snapshotTenant,
    'x-okapi-token': snapshotToken,
    'Content-Type': 'application/json'
    }
snapshot2PostHeaders={
    'x-okapi-tenant' : snapshot2Tenant,
    'x-okapi-token' : snapshot2Token,
    'Content-Type' : 'application/json'
    }


# ask to specify environment we are moving from and environment we are moving to

moveFrom = input("Which environment are we moving configs from? (snapshot, snapshot2): ")

if moveFrom == 'snapshot':
    fetchHeaders = snapshotFetchHeaders
    moveFromEnv = snapshotEnvironment
elif moveFrom == 'snapshot2':
    fetchHeaders = snapshot2FetchHeaders
    moveFromEnv = snapshot2Environment
else:
    print ("unrecognized move from environment")
    sys.exit()
    
moveTo = input("Which environment are we moving to? (snapshot, snapshot2): ")
if moveFrom == moveTo:
    print ("Can't be the same thing!")
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

movePatronGroups = input("Move patron groups? (Y/N) ")
moveServicePoints = input("Move service points? (Y/N) ")
moveLocations = input("Move location tree? (Y/N) ")
moveLoanTypes = input("Move Loan Types? (Y/N) ")
moveLoanRequestNotice = input("Move Loan, Request, and Notice Policies? (Y/N) ")
moveOverdueLostPolicies = input("Move Overdue and Lost Policies? (Y/N) ")
moveNoticeTemplates = input("Move notice templates? (Y/N) ")
moveCircRules = input("Move circulation rules? (Y/N)")


# move Patron Groups

if movePatronGroups == 'Y':
    urlGet = '{}{}'.format(moveFromEnv, "/groups?limit=1000") # create variable for the GET URL
    urlPost = '{}{}'.format(moveToEnv, "/groups") # create variable for the POST URL
    responseVarPatronGroups = requests.request("GET", urlGet, headers=fetchHeaders)
    responseJson = responseVarPatronGroups.json()
    responseResults = responseJson["usergroups"]
    for b in responseResults:
        b.popitem()
    for c in responseResults:
        print("Sending patron group %s" % c['group'])
        payload = json.dumps(c)
        r=requests.post(urlPost, data=payload, headers=postHeaders)
        # if your object already exists, the API will give an error. This next loop checks for an identified
        # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
        # it sends the request again as a PUT
        if any(x in r.text for x in error_phrases):
            print("Resending patron group as PUT %s" % c['group'])
            urlPut = '{}{}{}'.format(moveToEnv, '/groups/', c['id'])
            rPut = requests.put(urlPut, data=payload, headers=postHeaders)
            print(rPut.text)

# move Service Points

if moveServicePoints == 'Y':
    for d in servicePointApiValues:
        urlGet = '{}{}'.format(moveFromEnv, '/service-points?limit=100') # create variable for the GET URL
        urlPost = '{}{}'.format(moveToEnv, '/service-points?limit=100') # create variable for the POST URL
        responseServicePoints = requests.request("GET", urlGet, headers=fetchHeaders)
        responseVar = responseServicePoints.json()
        responseResults = responseVar[d]
        for f in responseResults:
            f.popitem()
            payload = json.dumps(f)
            print("Sending %s" % f['name'])
            r=requests.post(urlPost, data=payload, headers=postHeaders)
            # if your object already exists, the API will give an error. This next loop checks for an identified
            # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
            # it sends the request again as a PUT
            if any(x in r.text for x in error_phrases):
                print("Resending servicepoint as PUT %s" % f['name'])
                urlPut = '{}{}{}'.format(moveToEnv, '/service-points/', f['id'])
                rPut = requests.put(urlPut, data=payload, headers=postHeaders)

        
# move Locations (this will move the full location tree - institution, campus, library and locations)

if moveLocations == 'Y':
    for g in locationApiValues:
        urlGet = '{}{}'.format(moveFromEnv, locationApiValues.get(g)) # create variable for the GET URL
        urlPost = '{}{}'.format(moveToEnv, locationApiValues.get(g)) # create variable for the POST URL
        responseVar = requests.request("GET", urlGet, headers=fetchHeaders)
        responseJson = responseVar.json()
        responseResults = responseJson[g]
        for f in responseResults:
            f.popitem()
        for h in responseResults:
            payload = json.dumps(h)
            print("Sending %s" % h['name'])
            r=requests.post(urlPost, data=payload, headers=postHeaders)
            # if your object already exists, the API will give an error. This next loop checks for an identified
            # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
            # it sends the request again but as a PUT
            if any(x in r.text for x in error_phrases):
                 print("Sending again as PUT request %s" % h['name'])
                 urlPut = '{}{}{}'.format(moveToEnv, apiPutValues.get(g), h['id'])
                 rPut = requests.put(urlPut, data=payload, headers=postHeaders)

# move loan types

if moveLoanTypes == 'Y':
    urlGet = '{}{}'.format(moveFromEnv, '/loan-types?limit=500') # create variable for the GET URL
    urlPost = '{}{}'.format(moveToEnv, '/loan-types?limit=500') # create variable for the POST URL
    responseVar = requests.request("GET", urlGet, headers=fetchHeaders)
    responseJson = responseVar.json()
    responseResults = responseJson["loantypes"]
    for g in responseResults:
        g.popitem()
    for h in responseResults:
        print("sending loantype: %s" % h["name"])
        payload = json.dumps(h)
        r=requests.post(urlPost, data=payload, headers=postHeaders)
        # if the loan type already exists on moveToEnv, the post will throw an error. in this case,
        # the script checks for the existence of an error phrase (which varies by API) and, if found,
        # resends the request as a PUT
        if any(x in r.text for x in error_phrases):
            print("re-trying as PUT: %s" % h["name"])
            urlPut = '{}{}{}'.format(moveToEnv, '/loan-types/', h['id'])
            rPut = requests.put(urlPut, data=payload, headers=postHeaders)

# move loan, request, and notice policies

if moveLoanRequestNotice == 'Y':
    for i in apiValues:
        urlGet = '{}{}'.format(moveFromEnv, apiValues.get(i)) # create variable for the GET URL
        urlPost = '{}{}'.format(moveToEnv, apiValues.get(i)) # create variable for the POST URL
        responseVar = requests.request("GET", urlGet, headers=fetchHeaders) # fetch settings from moveFrom environment
        responseJson = responseVar.json() # turn response into Json object so you can get rid of the keys
        responseResults = responseJson[i] 
        for j in responseResults: # remove metadata object
            j.popitem()
        for k in responseResults: # post object to moveToEnv. 
            print("Sending %s - name: %s" % (i, k["name"]))
            payload = json.dumps(k)
            r=requests.post(urlPost, data=payload, headers=postHeaders)
            # if your object already exists, the API will give an error. This next loop checks for an identified
            # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
            # it sends the request again as a PUT
            if any(x in r.text for x in error_phrases):
                print("Sending %s as PUT request - name: %s" % (i, k["name"]))
                urlPut = '{}{}{}'.format(moveToEnv, apiPutValues.get(i), k['id'])
                rPut = requests.put(urlPut, data=payload, headers=postHeaders)
            
                
# now, let's move the overdue policies and lost item policies
# you can't use popitem with these since the id is the last thing in the object for some reason,
# and you don't want the ID to be removed.

if moveOverdueLostPolicies == 'Y':
    for m in fineApiValues:
        urlGet = '{}{}'.format(moveFromEnv, fineApiValues.get(m)) # create variable for the GET URL
        urlPost = '{}{}'.format(moveToEnv, fineApiValues.get(m)) # create variable for the POST URL
        responseVar = requests.request("GET", urlGet, headers=fetchHeaders) # fetch settings from moveFrom environment
        responseJson = responseVar.json()
        responseResults = responseJson[m]
        for n in responseResults:
            del(n['metadata']) # remove metadata object
        for p in responseResults: # post object to moveToEnv
            print("Sending %s - name: %s" % (m, p["name"]))
            payload = json.dumps(p)
            r = requests.post(urlPost, data=payload, headers=postHeaders)
            # if your object already exists, the API will give an error. This next loop checks for an identified
            # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
            # it sends the request again as a PUT
            if any(x in r.text for x in error_phrases):
                print("Sending %s as PUT request - name: %s" % (m, p["name"]))
                urlPut = '{}{}{}'.format(moveToEnv, apiPutValues.get(m), p['id'])
                rPut = requests.put(urlPut, data=payload, headers=postHeaders)
                
# move  notice templates - similar to fines, the metadata is in the middle of the JSON,
# and so you need to remove it differently

if moveNoticeTemplates == 'Y':
    urlGet = '{}{}'.format(moveFromEnv, '/templates?query=active==true&limit=100') # create variable for the GET URL
    urlPost = '{}{}'.format(moveToEnv, '/templates') # create variable for the POST URL
    responseVar = requests.request("GET", urlGet, headers=fetchHeaders) # fetch templates from moveFrom environment
    responseJson = responseVar.json()
    responseResults = responseJson["templates"]
    for t in responseResults:
        del(t["metadata"])
    for v in responseResults:
        print("Sending %s" % v["name"])
        payload = json.dumps(v)
        r = requests.post(urlPost, data=payload, headers=postHeaders)
        print(r.text)
        # if your object already exists, the API will give an error. This next loop checks for an identified
        # phrase in the response to indicate error (since it varies by API) - if it finds the phrase,
        # it sends the request again as a PUT
        if any(x in r.text for x in error_phrases):
            print("Sending %s as PUT request" % v['name'])
            urlPut = '{}{}{}'.format(moveToEnv, '/templates/', v['id'])
            rPut = requests.put(urlPut, data=payload, headers=postHeaders)

        
# finally, fetch circulation rules and repost them to moveToEnv
# rules are always a PUT request because they are created when the circulation  module is initialized
# so no error checking needed like the other options

if moveCircRules == 'Y':

    circRulesApiValues = {'rulesAsText' : '/circulation/rules'}
    urlGet = '{}{}'.format(moveFromEnv, "/circulation/rules") # create variable for the GET URL
    urlPut = '{}{}'.format(moveToEnv, "/circulation/rules") # create variable for the PUT URL
    
    responseVar = requests.request("GET", urlGet, headers=fetchHeaders)
    rules = responseVar.json()
    rulesAsText = rules["rulesAsText"]
    
    rulesAsTextJson = json.dumps(rulesAsText)
    
    rulesAsTextPayload = '{ "rulesAsText" : ' + rulesAsTextJson  + '}' # construct the rules payload by adding the attribute name
    
    print("Sending circulation rules file")
    rulesPut = requests.request("PUT", urlPut, headers=postHeaders, data=rulesAsTextPayload)
