import logging,sys,json,os,operator,requests,time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError,ConnectionTimeout as timeout
from datetime import datetime, timedelta
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from json.decoder import JSONDecodeError
import re
LOG=logging.getLogger(__name__)

class Gerritcommits:
    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        self.username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
        self.password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
   
    '''
    This function returns null values 
    :return:dict
    '''
    def gerrit_except_attributes(self):
            dictionary = {
                  "projectname":0,
	              "pipeline.name":"0",
                  "name":"0",
                  "change_id":"0",
                  "submitted":"0"
                }
            return dictionary
    '''
    This function fetch gerrit attributes using API
    :return: gerrit api response
    '''
    def fetch_gerritAttributes(self,projectName):
        try:
            project = format(projectName)
            params = 'branch:master+status:merged&o=DETAILED_ACCOUNTS'
            user_name = self.username.lower()
            auth = HTTPBasicAuth(user_name, self.password)
            rest = GerritRestAPI(url='https://gerrit-gamma.gic.ericsson.se/', auth=auth)
            changes = rest.get('/changes/?q=' + project + '+' + params)
            return changes
        except requests.ConnectionError as er:
            self.LOG.error(er)
        except requests.exceptions.RequestException as err:
            self.LOG.error(err) 
    '''
    This function fetch all commits deatils from each repo
    :return: commits details as dictionary
    :return: all the change id's
    '''
    def commits_by_user(self,change,pipelineName):
        try:
            for values in change:
                if len(values['change_id']) > 0 :
                    project = values['project']
                    change_id = values['change_id']
                    name = values['owner']['name']
                    submitted = values['submitted']
                    reponame = pipelineName
                    d = datetime.strptime(submitted, '%Y-%m-%d %H:%M:%S.%f000')
                    millisec = d.timestamp()*1000
                    mil=int(millisec)
                    dictionary = {
                    "projectname":project,
                    "pipeline.name":pipelineName,
                    "name":name,
                    "change_id":change_id,
                    "submitted":mil,
                    }
                    json_object = json.dumps(dictionary, indent=4, default=str)
                    return json_object,change_id
        except (KeyError,IndexError) as e:
            dictionary = {
                    "projectname":"0",
                    "pipeline.name":"0",
                    "name":"0",
                    "change_id":"0",
                    "submitted":"0",
            }
            json_object = json.dumps(dictionary, indent=4, default=str)
            return json_object,0
        


