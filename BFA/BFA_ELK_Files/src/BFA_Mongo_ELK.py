from datetime import datetime, timedelta
import logging,sys,json,os,operator,requests,time
from unittest import skip
import statistics
import pymongo
import bson
import json
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError,ConnectionTimeout as timeout
from elasticsearch.exceptions import TransportError as TransportError
from Hashmap import Hashmap

LOG=logging.getLogger(__name__)


class mongoDB_ELK:

    def __init__(self):
            logging.basicConfig()
            self.LOG = logging.getLogger(__name__)
            self.LOG.setLevel(logging.DEBUG)      
      
    def establish_connection_eck(self):

        ''' This function is to establish a cinnection with Elasticsearch DB '''

        try:
            tls_elk = Elasticsearch(['https://elastic.hahn130.rnd.gic.ericsson.se:443'],http_auth=('elastic','4lTX6kU6vURX89S0RsGK7066'), verify_certs=False)
            self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return tls_elk
        
    def push_metrics(self,tls_elk, docket_content,id, index_name):

        ''' This  function is to push metrics into the index of ElasticSearch DB '''
        
        try:
            tls_elk.index(index=index_name, id=id, ignore=400, body=docket_content, doc_type = "_doc")
            self.LOG.info(f"Data pushed to index successfully")
        except timeout as tout:
            raise timeout from tout
        except TransportError:
            self.LOG.info("Non - OK Status")
        except Exception as e:
            raise Exception from e        

    def connect_mongo_server(self):

        ''' This function is to establish a connection with Mongo DB Server '''

        try:
            Client_Mongo_new=MongoClient('mongodb://ossmsci:Bn1cr9Nq8E06aIC@pduoss-idun-ci-mongo-1598-p.seli.gic.ericsson.se:27017/pduoss-idun-ci')
            self.LOG.info("Mongo DB connection established")
        except pymongo.errors.ConnectionFailure as e:
            self.LOG.info("Couldn't connect to Mongo DB Server")
        return Client_Mongo_new

    def access_database(self):

        ''' This function is to access statistics in the Database-pduoss-idun-ci '''

        try:
            Client_Mongo_new=MongoClient('mongodb://ossmsci:Bn1cr9Nq8E06aIC@pduoss-idun-ci-mongo-1598-p.seli.gic.ericsson.se:27017/pduoss-idun-ci')
            db=Client_Mongo_new["pduoss-idun-ci"]
        except pymongo.errors.ConnectionFailure as e:
            self.LOG.info("Couldn't connect to Mongo DB Server")
        except pymongo.errors.ExecutionTimeout :
            self.LOG.info("Database operation is timed out. $maxTimeMS  is exceeded")
        return db
    
    def get_teamName(self,pipelineName):
        try:
            microserviceName = pipelineName.split("_")[0]
            response = requests.get('https://pdu-oss-tools1.seli.wh.rnd.internal.ericsson.com/team-inventory/api/teams').json()
            for i in range(len(response)):
                team_name='NULL'
                ms_name = response[i]['microservice']
                if ms_name is not None:
                    team_name = response[i]['name']
                    if microserviceName in ms_name.lower() :
                        return team_name
            return "NULL"
        except requests.ConnectionError as error:
            raise requests.ConnectionError from error

    def yesterdayDate(self):
        yesterday = (datetime.today()-timedelta(days=1)).strftime('%Y-%m-%d')
        return yesterday

    def fetch_db_data(self,tls_elk):
        try:
            Client_Mongo_new=MongoClient('mongodb://ossmsci:Bn1cr9Nq8E06aIC@pduoss-idun-ci-mongo-1598-p.seli.gic.ericsson.se:27017/pduoss-idun-ci')
            db=Client_Mongo_new["pduoss-idun-ci"]
            statistics=db["statistics"]
            m=Hashmap(10000)
            yesterday = self.yesterdayDate()+"T23:30:00.000Z"
            startTime = datetime.strptime(yesterday, "%Y-%m-%dT%H:%M:%S.%fZ")
            statQuery = {"result": "FAILURE",
                        "startingTime": {"$gt": startTime}}
            key='failureCauses'
            faildb = db["failureCauses"]
            for mrd in statistics.find(statQuery):
                _id=str(mrd['_id'])
                project_name = mrd['projectName']
                pipelineSuffixes = ["_PreCodeReview","_precodereview","_Publish","_publish","_Release","_release","RPT-RC"]
                if any(keyword in project_name for keyword in pipelineSuffixes):
                    print("pipeline name : ", project_name)
                    microserviceName = project_name.split("_")[0]
                    team_name=m.get_val(microserviceName)
                    if team_name== "No record found" :
                        team_name = self.get_teamName(project_name)
                        m.set_val(microserviceName,team_name)
                    buildNumber=mrd['buildNumber']
                    displayName=mrd['displayName']
                    fem=mrd['master']
                    url = f"https://{fem}:8443/jenkins/job/{project_name}/{buildNumber}/"
                    slaveHostName=mrd['slaveHostName']
                    startingTime=mrd['startingTime']
                    startingTime=str(startingTime).split('.')[0]
                    d = datetime.strptime(str(startingTime), '%Y-%m-%d %H:%M:%S')
                    millisec = d.timestamp()*1000
                    time=int(millisec)
                    duration=mrd['duration']
                    timeZoneOffset=mrd['timeZoneOffset']
                    triggerCauses=mrd['triggerCauses']
                    upstreamCause=mrd['upstreamCause']
                    result=mrd['result']
                    failureCauseName = ""
                    if "failureCauses" in mrd:
                        failureCause = str(mrd['failureCauses'][0]["failureCause"])
                        statID = failureCause.split(", ")[1].split("'")[1]
                        failQery = {"_id": bson.ObjectId(statID)}
                        fail = faildb.find(failQery)
                        for fdata in fail:
                            failureCauseName = fdata["name"]
                    else:
                            failureCauseName = "Non-classified failures"
                    id=_id
                    dictionary={
                            "-id":_id,
                            "project_name":project_name,
                            "team.name":team_name,
                            "buildNumber":buildNumber,
                            "displayName":displayName,
                            "fem":fem,
                            "url":url,
                            "slaveHostName":slaveHostName,
                            "time":time,
                            "duration":duration,
                            "timeZoneOffset":timeZoneOffset,
                            "triggerCauses":triggerCauses,
                            "upstreamCause":upstreamCause,
                            "result":result,
                            "failureCauses":failureCauseName
                        }
                    docket_content = json.dumps(dictionary, indent=4, default=str)
                    self.LOG.info(f"{dictionary} \n")
                    try :
                        if project_name.__contains__("_Publish") or project_name.__contains__("_publish") or project_name.__contains__("_Release") or project_name.__contains__("_release"):
                            self.push_metrics(tls_elk,docket_content, id,'rigel-mongodb-bfa-failurecauses')
                            self.push_metrics(tls_elk,docket_content, id,'mongodb-bfa-publish-failurecauses')
                            self.LOG.info("Failure causes are pushed to Elasticsearch DB")
                        else:
                            self.push_metrics(tls_elk,docket_content, id,'rigel-mongodb-bfa-failurecauses')
                    except TransportError:
                        self.LOG.info("Non - OK Status")
        except ElasticConnectionError:
            self.LOG.info("Elasticsearch connection error")
        except TimeoutError:
            self.LOG.info("Elastic search connection timeout error")

