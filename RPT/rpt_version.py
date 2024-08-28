'''Updating version to Env in RPT'''
import logging
import json


from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout
from elasticsearch.helpers import scan
from packaging import version 


class RPT:

    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)

    def yesterday_date(self):
        yesterday = (datetime.today()-timedelta(days=1)).strftime('%Y.%m.%d')
        return yesterday

    def establish_connection(self):
        '''
        This function establishes connection to ELK
        :return:
        '''
        try:
            es = Elasticsearch('http://es.hahn051.rnd.gic.ericsson.se:80')
	    # self.LOG.info("connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return es
    
    # This function converts time into milliseconds
    def milliseconds(self, time):
        sp = time.split("T")[1].replace("Z", "").replace(".", ":").split(":")
        milliSeconds = ((int(sp[0])*3600000)+(int(sp[1])*60000)+(int(sp[2])*1000)+(int(sp[3])))
        return milliSeconds

    # This function used to fetch data from Elastic Search using query
    def query(self, statusName):
        query = {"query": {"bool": {"must": [{"match": {"old.0.status": statusName}}]}}}
        return query

    def main_function(self):
        es = self.establish_connection()
        index = "express-logs-"+self.yesterday_date()
        limit = es.indices.put_settings(index=index, body={"index.mapping.total_fields.limit": 100000})
        print("limit increase:", limit)
        status = ["Reserved", "Available", "Quarantine", "Standby", "Refreshing"]
        for i in status:
            for dobj in scan(es, query=self.query(i), index=index):
                old_version = dobj["_source"]["old"]["0"]["properties"]['version']
                res_version = dobj["_source"]["res"]["0"]["properties"]['version']
                '''print("old version : ", old_version)
                print('new_version : ', res_version)
                print("time : ", dobj["_source"]["@timestamp"])
                print("id :", dobj["_id"])
                print("\n\n\n")'''
                if(old_version != res_version and old_version != "N/A" and res_version != "N/A"):
                    if(version.parse(old_version) < version.parse(res_version)
                       or version.parse(old_version) > version.parse(res_version)):
                        print("old version : ", old_version)
                        print('new_version : ', res_version)
                        print("time : ", dobj["_source"]["@timestamp"])
                        print("id :", dobj["_id"])
                        print("\n\n\n")
                        doc_id = dobj["_id"]
                        try:
                            json_object = json.dumps(dobj["_source"],default = str)
                            es.index(index="rpt-versions", id=doc_id, ignore=400 , body=json_object)
                            #self.LOG.info(f"Data pushed to {indices} index successfully")
                        except timeout as tout:
                            raise timeout from tout
                        except Exception as e:
                            print(e)

rpt = RPT()
rpt.main_function()
