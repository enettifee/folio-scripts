# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 11:17:51 2021

@author: en25
"""

import json
import requests
import folioFunctions as ff
import configparser

# read in configuration files

envConfig = configparser.ConfigParser()
envConfig.read('config-template.ini')
print(envConfig.sections())

# call function to ask for environment to move from and to:
moveFromEnv, moveToEnv = ff.askenvironment()

moveUrl = envConfig[moveFromEnv]['okapi_url']
moveToUrl = envConfig[moveToEnv]['okapi_url']

fetchHeaders = {
    'x-okapi-tenant': envConfig[moveFromEnv]['tenant_id'],
    'x-okapi-token': envConfig[moveFromEnv]['password']
}
postHeaders = {
    'x-okapi-tenant': envConfig[moveToEnv]['tenant_id'],
    'x-okapi-token': envConfig[moveToEnv]['password'],
    'Content-Type': 'application/json'
}

# ask which settings to move
# TODO: Add calendars

movePatronGroups = input("Move patron groups? (Y/N)")
moveServicePoints = input("Move service points and calendars (Y/N)")
moveFixedDueDates = input("Move fixed due dates (Y/N) ")
moveLocations = input("Move location tree? (Y/N)")
moveLoanTypes = input("Move Loan Types? (Y/N)")
moveLoanRequestNotice = input("Move Loan and Request Policies? (Y/N)")
moveOverdueLostPolicies = input("Move Overdue and Lost Policies? (Y/N)")
moveNotices = input("Move notices and notice templates? (Y/N) ")
moveStaffSlips = input("Move staff slips? (Y/N) ")
moveCircRules = input("Move circulation rules? (Y/N)")

# move a bunch of stuff
# TODO add calendars

if movePatronGroups == 'Y':
    ff.moveSettings("/groups?limit=1000", "/groups/", "usergroups", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveServicePoints == 'Y':
    ff.moveSettings("/service-points?limit=100", "/service-points/", "servicepoints", moveUrl, moveToUrl, fetchHeaders, postHeaders)
# if moveCalendars == 'Y':
#     ff.moveSettings("")
if moveFixedDueDates == 'Y':
    ff.moveSettings("/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=1000", "/fixed-due-date-schedule-storage/fixed-due-date-schedules/", "fixedDueDateSchedules", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveLoanTypes == 'Y':
    ff.moveSettings("/loan-types?limit=500", "/loan-types/", "loantypes", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveLocations == 'Y':
    ff.movelocations(moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveNotices == 'Y':
    ff.movecircpolicies("/templates?query=active==true&limit=100", "/templates/", "templates", moveUrl, moveToUrl, fetchHeaders, postHeaders)
    ff.movecircpolicies("/patron-notice-policy-storage/patron-notice-policies?limit=100", "/patron-notice-policy-storage/patron-notice-policies/", "patronNoticePolicies", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveLoanRequestNotice == 'Y':
    ff.movecircpolicies("/loan-policy-storage/loan-policies?limit=100", "/loan-policy-storage/loan-policies/", "loanPolicies", moveUrl, moveToUrl, fetchHeaders, postHeaders)
    ff.movecircpolicies("/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=100", "/fixed-due-date-schedule-storage/fixed-due-date-schedules/", "fixedDueDateSchedules", moveUrl, moveToUrl, fetchHeaders, postHeaders)
    ff.movecircpolicies("/request-policy-storage/request-policies?limit=100", "/request-policy-storage/request-policies/", "requestPolicies", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveOverdueLostPolicies == 'Y':
    ff.movecircpolicies("/overdue-fines-policies?limit=100", "/overdue-fines-policies/", "overdueFinePolicies", moveUrl, moveToUrl, fetchHeaders, postHeaders)
    ff.movecircpolicies("/lost-item-fees-policies?limit=100", "/lost-item-fees-policies/", "lostItemFeePolicies", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveStaffSlips == 'Y':
    ff.movecircpolicies("/staff-slips-storage/staff-slips", "/staff-slips-storage/staff-slips/", "staffSlips", moveUrl, moveToUrl, fetchHeaders, postHeaders)
if moveCircRules == 'Y':
    ff.movecircrules("/circulation/rules", "rulesAsText", moveUrl, moveToUrl, fetchHeaders, postHeaders)
