"""
Basic python script to authenticate to a FOLIO
instance and produce a CSV file with information
about items currently on reserve for a defined time period.
"""

import json
import requests
import configparser

# read in configuration files

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')
print(envConfig.sections())

folioenv = input("Which environment are we retrieving course information from? ")
fetchserver = envConfig[folioenv]['okapi_url']
print(fetchserver)

fetchHeaders = {
    'x-okapi-tenant': envConfig[folioenv]['tenant_id'],
    'x-okapi-token': envConfig[folioenv]['password']
}


# retrieve the current terms
termsurl = '{}{}'.format(fetchserver, '/coursereserves/terms')
terms = requests.get(termsurl, headers=fetchHeaders)
termsjson = terms.json()

# ask which term they want to get course lists for

whichterm = input("Which term should we fetch reserves for? ")
for i in termsjson['terms']:
    if i['name'] == whichterm:
        termId = i['id']


# fetch the courselistings for the term
# courselistingsurl = '{}{}'.format(fetchserver, '/coursereserves/courselistings?')
courselistingsurl = "https://folio-snapshot-okapi.dev.folio.org/coursereserves/courselistings?query=(termId=cd1eb7ed-2704-4b6a-9037-d7f1a5351f6b)"
courselistings = requests.get(courselistingsurl, headers=fetchHeaders)
print(courselistings.text)
