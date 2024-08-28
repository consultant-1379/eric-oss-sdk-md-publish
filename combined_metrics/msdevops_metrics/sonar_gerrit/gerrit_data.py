import logging,sys,json,os,operator,requests,time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError,ConnectionTimeout as timeout
from datetime import datetime, timedelta
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from json.decoder import JSONDecodeError
from msdevops_metrics.sonar_gerrit.sonar_data import SonarData
LOG=logging.getLogger(__name__)

class GerritData:

    @staticmethod        
    def gerrit_except_attributes(projectName):
        '''
        This function is used to insert blank values for test gerrit projects which are not having master branch
        '''
        dictionary = {
            "projectname":projectName,
            "branch":"0",
            "submittedTime":"0",
            "Reviewtime":"0",
            "timedifference":"0",
        }
        return dictionary
  
        
    def fetch_gerritAttributes(self,projectName):
        '''
        This function fetch the gerrit attributes for a given project name
        '''
        try:
            sonar = SonarData()           
            project = format(projectName)
            user_name=sonar.username
            user_name=user_name.lower()
            params = 'branch:master+status:merged&o=DETAILED_ACCOUNTS'
            auth = HTTPBasicAuth(user_name, sonar.password)
            rest = GerritRestAPI(url='https://gerrit-gamma.gic.ericsson.se/', auth=auth)
            changes = rest.get('/changes/?q=' + project + '+' + params)
            return(changes)
        except requests.ConnectionError as error:
            raise requests.ConnectionError from error 

    def get_review_time(self,changes):
        reviewTime=0
        count=0
        '''each item is a Python dictionary'''
        for change1 in changes:
            if len(change1['project']) > 0 :
                fullname = change1['project']
                createdOn = change1['created']
                lastUpdated = change1['submitted']
                createdOn = createdOn.split('.')[0]
                lastUpdated = lastUpdated.split('.')[0]
                lastUpdated = datetime.strptime(lastUpdated, '%Y-%m-%d %H:%M:%S')
                createdOn = datetime.strptime(createdOn, '%Y-%m-%d %H:%M:%S')
                if(count) == 0:  
                    reviewTime = str(abs(lastUpdated - createdOn))
                    return reviewTime
                    
    def get_time_diff(self,changes,repo_name,review_time,branch):
        count=0
        time_diff=0
        time1=0
        time2=0
        try:
            for change1 in changes:
                if len(change1['change_id']) > 0 :
            # '''Parsing out the relevant information'''
                    project = change1['project']
                    #branch = change1['branch']
                    change_id = change1['change_id']
                    createdOn = change1['created']
                    lastUpdated = change1['submitted']
                    submitted = lastUpdated.split('.')[0]
                    if(count) == 0:  
                        time1=submitted    
                    if(count) == 1:
                        time2=submitted
                        time_diff = str((datetime.strptime(time1, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')))   
                    count=count+1
                    
            dictionary = {
                    "projectname":repo_name,
                    "branch":branch,
                    "submittedTime":time1,
                    "Reviewtime":review_time,
                    "timedifference":time_diff,
            }
            return dictionary
        except KeyError as err:
            return  {
            "projectname":repo_name,
            "branch":"0",
            "submittedTime":"0",
            "Reviewtime":"0",
            "timedifference":"0",
        }
    

