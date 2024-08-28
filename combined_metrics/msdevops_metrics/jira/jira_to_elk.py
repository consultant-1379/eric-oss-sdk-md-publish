#!/usr/bin/python
import sys
import json
import os
import requests
import logging
from pprint import pprint
from elasticsearch import Elasticsearch
from requests.auth import HTTPBasicAuth
from msdevops_metrics.dora_metrics.push import ElasticPush

index="merged-ms_jobs_eiffel216_2"

logging.basicConfig(level=logging.DEBUG)


def jira_list(item,data):

    logging.info(f"#######################")
    total_num_issues=data['total']
    logging.info(f"{total_num_issues}")
    jira_number=(data['issues'][item]['key'])
    #jira_fields=(data['issues'][item]['fields']['customfield_32858'])
    jira_status=(data['issues'][item]['fields']['status'])
    jira_created=(data['issues'][item]['fields']['created'])
    #jira_resolution=(data['issues'][item]['resolution'])
    jira_assignee=(data['issues'][item]['fields']['assignee'])
    
    #This is to get the team name alone from the jira api customfield_32858, there were some exception due to null value for team name
    team_name=""
    if team_name is not None:
        try:
            team_name=(data['issues'][item]['fields']['customfield_32858']['value'])
            logging.info(f"{team_name}")
        except TypeError:
            logging.info(f"Team name is none or null")
        except UnboundLocalError:
            logging.info(f"Team name is none or null unboud")
    else:
        logging.info(f"Team name is none or null")    

    logging.info(f"{jira_number}")
    logging.info(f"{team_name}")
    logging.info(f"{jira_status}")
    logging.info(f"{jira_created}")
    logging.info(f"{jira_assignee}")
    #logging.info(f"{jira_type}")
    dictionary = {
        "key": jira_number,
        "team.name":team_name,
        "status":jira_status,
        "created":jira_created,
        "assignee":jira_assignee,
        #"jira_issue_type":jira_type
    }
    logging.info(f"*******************")
    json_object = json.dumps(dictionary)
    with open("jira-data.json", "w") as outfile:
        outfile.write(json_object)
    filename="jira-data.json"
    with open(filename) as f:
        logging.info(f"File which is sent to ES is " +filename)
        docket_content = f.read()
    # Send the data into es
    elastic_push = ElasticPush()
    es=elastic_push.establish_connection_eck()
    try:
        logging.info(f"Sending data")    
        elastic_push.publish_data(es,jira_number,docket_content,index)
        logging.info(f"Data pushed to {index} index successfully")
    except Exception as ex:
        logging.error(f"Error in indexing data")
        logging.info((str(ex)))



def main_function():
    print("Main function is called")
    functional_user_username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
    functional_user_password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
    print(functional_user_username)
    logging.info(f"Main function")    
    issue_type = ["Bug", "TR"]
    for jira in issue_type:
        try:
            # Following is to get all the status ticket
            auth=HTTPBasicAuth(functional_user_username, functional_user_password)
            #response_list = requests.get('https://jira-oss.seli.wh.rnd.internal.ericsson.com/rest/api/2/search?jql=project%20%3D%20%22IDUN%22%20AND%20issuetype%20%3D%20{0}&fields=id,key,customfield_32858,resolutiondate,created,status,assignee,issuetype&maxResults=1000'.format(jira))
            #Below is to get all status tickets except closed and done.
            response_list = requests.get('https://jira-oss.seli.wh.rnd.internal.ericsson.com/rest/api/2/search?jql=project%20%3D%20%22IDUN%22%20AND%20issuetype%20%3D%20{0}%20AND%20%22status%22%20!=Closed%20AND%20status%20!=Done&fields=id,key,customfield_32858,resolutiondate,created,assignee,status&maxResults=1000'.format(jira),auth=HTTPBasicAuth(functional_user_username, functional_user_password))
            data=response_list.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Not able to fetch data from jira")
            raise SystemExit(e)        

        total_num_issues=data['total']
        number=1
        try:
            while number < total_num_issues:
                logging.info(f"Jira type " +jira)
                jira_list(number,data)
                number += 1
        except IndexError:
            logging.info(f"Done")
