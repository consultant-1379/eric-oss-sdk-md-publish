import requests
import json
import logging
import os
from msdevops_metrics.dora_metrics.push import ElasticPush


logging.basicConfig(level=logging.DEBUG)

functional_user_username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
functional_user_password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
'''
Below script fetches upcoming DRs planned to enforcement in next 90Days and stores in Json Format
:return:
'''
def main_function():
    try:
        data= requests.get('https://eteamproject.internal.ericsson.com/rest/api/2/search?jql=PROJECT = ADPPRG AND issuetype = "DR Check" AND "Planned Enforcement Date" >= now() AND "Planned Enforcement Date" < 90d AND (status = PLANNED OR status = "Checked (Gracefully)" OR status = CHECKED OR status = "In Progress") ORDER BY "Planned Enforcement Date", "DR Tag", "Key"',auth=(functional_user_username, functional_user_password)).json()
    
        try:
            for k in data["issues"]:
                dict = {"date": k["fields"]["customfield_31713"], "DR_Tage": k["fields"]["customfield_31712"],
                    "status": k["fields"]["status"]["name"], "DR_Checker_Tool": k["fields"]["customfield_31714"],
                    "key": k["key"]}
                elastic_push = ElasticPush()
                es=elastic_push.establish_connection_eck()
                elastic_push.publish_data(es,dict[ "DR_Tage"],dict,"merged-latest-dr-checks")
                logging.info("pushed")
        except ValueError as ve:
            raise ValueError from ve
    except IOError as ie:
        raise IOError from ie
