from datetime import datetime, timedelta
from unittest import skip
import pymongo,requests
import json,logging
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError,ConnectionTimeout as timeout
from elasticsearch.exceptions import TransportError as TransportError
from Hashmap import Hashmap

LOG=logging.getLogger(__name__)
class vaCauses:
    def __init__(self):
            logging.basicConfig()
            self.LOG = logging.getLogger(__name__)
            self.LOG.setLevel(logging.DEBUG)
    def establish_connection(self):
        ''' This function is to establish a connection with Elasticsearch DB '''
        try:
            es = Elasticsearch('http://es.hahn051.rnd.gic.ericsson.se:80')
            self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return es
        
    def establish_connection_eck(self):

        ''' This function is to establish a cinnection with Elasticsearch DB '''

        try:
            tls_elk = Elasticsearch(['https://elastic.hahn130.rnd.gic.ericsson.se:443'],http_auth=('elastic','4lTX6kU6vURX89S0RsGK7066'), verify_certs=False)
            self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return tls_elk
        
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
            
    def push_metrics(self,es,tls_elk, docket_content,id):
        ''' This  function is to push metrics into the index of ElasticSearch DB '''
        
        try:
            es.index(index='rigel-mongodb-va-failurecause',id=id,ignore=400, body=docket_content, doc_type = "_doc")
            tls_elk.index(index='rigel-mongodb-va-failurecause',id=id,ignore=400, body=docket_content, doc_type = "_doc")
            LOG.info(f"Data pushed to index successfully")
        except timeout as tout:
            raise timeout from tout
        except TransportError:
            self.LOG.info("Non - OK Status")
        except Exception as e:
            raise Exception from e 
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
    def fetch_va_causes(self,es,tls_elk):
        try:
            es=Elasticsearch('http://es.hahn051.rnd.gic.ericsson.se:80')
            Client_Mongo_new=MongoClient('mongodb://ossmsci:Bn1cr9Nq8E06aIC@pduoss-idun-ci-mongo-1598-p.seli.gic.ericsson.se:27017/pduoss-idun-ci')
            db=Client_Mongo_new["pduoss-idun-ci"]
            statistics=db["statistics"]
            mrd= statistics.find()
            count=0
            m=Hashmap(10000)
            key='failureCauses'
            for mrd in statistics.find():
                if key in mrd :
                    _id=mrd['_id']
                    project_name = mrd['projectName']
                    if project_name.__contains__("_PreCodeReview") or project_name.__contains__("_precodereview") or project_name.__contains__("_Publish") or project_name.__contains__("_publish") or  project_name.__contains__("_Release") or project_name.__contains__("_release") :
                         microserviceName = project_name.split("_")[0]
                         team_name=m.get_val(microserviceName)
                         if team_name== "No record found" :
                             team_name = self.get_teamName(project_name)
                             m.set_val(microserviceName,team_name)
                         buildNumber=mrd['buildNumber']
                         displayName=mrd['displayName']
                         fem=mrd['master']
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
                         list=[".*Artifact doesn't exist or not indexed/cached in Xray.*",
                             ".*Bad Credentials.*",
                             ".*Failure in Stage Vulnerability Analysis.*",
                             ".*Failure in Stage Kubeaudit.*",
                             ".*Failure in Stage Kubehunter.*",
                             ".*Failure in Stage Anchore-Grype.*",
                             ".*Failure in Stage Trivy.*",
                             ".*Failure in Stage Vulnerability Analysis.*",
                             ".*unable to update vulnerability database.*",
                             ".*Failure in Stage Kubsec.*",
                             ".*unable to use DockerDaemon source: pull failed: Error response from daemon: unauthorized: The client does not have permission for manifest.*",
                             ".*no space left on device.*",
                             ".*UNAUTHORIZED: The client does not have permission for manifest.*"
                             ]
                         for i in range(15):
                             try:
                                 if mrd['failureCauses'][i] in mrd['failureCauses']:
                                     failureCauses = mrd['failureCauses'][i]['indications'][0]['pattern']
                                     if failureCauses != 'null':
                                         if failureCauses in list:
                                             id=str(_id)+str(i)
                                             dictionary={
                                                 "-id":str(_id)+str(i),
                                                 "pipeline.name":project_name,
                                                 "team.name":team_name,
                                                 "buildNumber":buildNumber,
                                                 "displayName":displayName,
                                                 "fem":fem,
                                                 "slaveHostName":slaveHostName,
                                                 "time":time,
                                                 "duration":duration,
                                                 "timeZoneOffset":timeZoneOffset,
                                                 "triggerCauses":triggerCauses,
                                                 "upstreamCause":upstreamCause,
                                                 "result":result,
                                                 "failureCauses":failureCauses
                                             }
                                             count=count+1
                                             docket_content = json.dumps(dictionary, indent=4, default=str)
                                             try :
                                                 self.push_metrics(es,tls_elk,docket_content, id)
                                                 self.LOG.info("Failure causes are pushed to Elasticsearch DB")
                                             except TransportError:
                                                 self.LOG.info("Non - OK Status")
                             except IndexError as e:
                                 self.LOG.info("Failure causes index is not found")
        except ElasticConnectionError:
            self.LOG.info("Elasticsearch connection error")
        except TimeoutError:
            self.LOG.info("Elastic search connection timeout error") 
