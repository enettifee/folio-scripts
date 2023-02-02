"""
A basic script to renew loans. Developed and tested on Nolana.
Attempts to retrieve a defined number of open loans - hardcoded to 1,000 - and
then renew them. 

Outputs a CSV file in the script directory with
user barcode, title, item barcode, response message

This is continuing iteration - goal is to get to a script that can take input to get a list of loans
and then renew that list.

@enettifee Jan 2023 - Feb 2023.

"""

import json
import requests
import configparser
import csv

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
fetchLoansUrl = '{}{}'.format(fetchserver, '/circulation/loans?limit=1000&query=(status.name = "Open")')
renewUrl = '{}{}'.format(fetchserver, '/circulation/renew-by-id')

"""
First, fetch the list of existing loans.
"""

loanRequests = requests.get(fetchLoansUrl, headers=headers)
loans = loanRequests.json()
loansDictionary = loans['loans']
renewResponses = {}

for count, each in enumerate(loansDictionary, start=1):
    print(each['item']['title'])
    renewDictionary = {}
    renewDictionary['userId'] = each['userId']
    renewDictionary['itemId'] = each['itemId']
    renewLoanBody = json.dumps(renewDictionary)
    print(f"Attempting renew {count} item title {each['item']['title']}")
    renewLoan = requests.post(renewUrl, data=renewLoanBody, headers=headers)
    renewLoanJson = renewLoan.json()
    if "failed" in renewLoan.text:
        renewFailed = []
        renewFailed.extend([each['borrower']['barcode'],each['item']['title'], each['item']['barcode'], "500 server side error"])
        renewResponses[count] = renewFailed
    elif "renewed" in renewLoan.text:
        renewSucceeded = []
        renewSucceeded.extend([each['borrower']['barcode'],each['item']['title'], each['item']['barcode'], "Item was renewed"])
        renewResponses[count] = renewSucceeded
    else:
        renewFailedErrors = []
        renewFailedErrors.extend([each['borrower']['barcode'],each['item']['title'], each['item']['barcode'], renewLoanJson['errors'][0]['message']])
        renewResponses[count] = renewFailedErrors

output_file = "renewal_report.csv"

with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['User barcode', 'Title', 'Barcode', 'Message'])
    for each in renewResponses:
        writer.writerow(renewResponses[each])
