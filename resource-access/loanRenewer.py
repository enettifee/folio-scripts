"""
A basic script to renew loans. Uses configparser to handle authentication.
Retrieves all loans from a FOLIO environment and attempts to renew all of them at once.
Screen will output
1: Error message if there was an HTTP error, which can happen when the renewal tries to talk to the calendar
2: Error message from the JSON if the attempt to renew failed through the normal circulation checks;
3: A message "Item was renewed" if the reenewal was successful.

This is a very early version of what a better version of this could look like, but I'm putting it here
anyway in case it's useful.

-enettifee 1-31-2023
"""

import json
import requests
import configparser


# read in configuration files

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')
print(envConfig.sections())

folioenv = input("Which environment are we working with? ")

fetchserver = envConfig[folioenv]['okapi_url']
headers = {
    'x-okapi-tenant': envConfig[folioenv]['tenant_id'],
    'x-okapi-token': envConfig[folioenv]['password'],
    'content-type': "application/json"
}

"""
make some urls

renew-by-id requires itemId and userId
"""
fetchLoansUrl = '{}{}'.format(fetchserver, '/circulation/loans?limit=100000&query=(status.name = "Open")')
renewUrl = '{}{}'.format(fetchserver, '/circulation/renew-by-id')

"""
First, fetch the list of existing loans.
"""

loanRequests = requests.get(fetchLoansUrl, headers=headers)
loans = loanRequests.json()

for count, each in enumerate(loans['loans'], start=1):
    renewDictionary = {}
    renewDictionary['userId'] = each['userId']
    renewDictionary['itemId'] = each['itemId']
    renewLoanBody = json.dumps(renewDictionary)
    print(f"Attempting renew {count} item id {each['itemId']}")
    renewLoan = requests.post(renewUrl, data=renewLoanBody, headers=headers)
    if "failed" in renewLoan.text:
        print(renewLoan.text)
    elif "renewed" in renewLoan.text:
        print("item was renewed")
    else:
        renewLoanJson = renewLoan.json()
        errorMessage = renewLoanJson['errors'][0]
        print(errorMessage['message'])
