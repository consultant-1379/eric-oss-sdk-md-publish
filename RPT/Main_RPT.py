'''Updating duration to missed Index in RPT'''
import logging
import pandas
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout
from elasticsearch.helpers import scan
import json


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
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return es

    # This function gives missed dates into a list
    def missedDates(self, old, new):
        a = pandas.date_range(start=old, end=new, freq='D')
        replace = str(a).replace("\n", "").replace(" ", "").replace("'", "").replace("DatetimeIndex([", "")
        missedDates = replace.replace("],dtype=datetime64[ns],freq=D)", "").split(",")
        return missedDates

    # This function converts time into milliseconds
    def milliseconds(self, time):
        sp = time.split("T")[1].replace("Z", "").replace(".", ":").split(":")
        milliSeconds = ((int(sp[0])*3600000)+(int(sp[1])*60000)+(int(sp[2])*1000)+(int(sp[3])))
        return milliSeconds

    # This function gives count of missed dates
    def days_between(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    # This function used to fetch data from Elastic Search using query
    def duration_query(self, env_name, statusName):
        query = {"query": {"bool": {"must": [{"match": {"old.0.status": statusName}},
                                             {"match": {"old.0.name": env_name}}]}}}
        return query

    def env_query(self, envName):
        query = {"query": {"bool": {"must": [{"match": {"old.0.name": envName}}]}}}
        return query

    def query(self, statusName):
        query = {"query": {"bool": {"must": [{"match": {"old.0.status": statusName}}]}}}
        return query

    # This funtion used to fetch  data from previous index
    def missedDocQuery(self, oldModifiedOn, oldName, oldStatus):
        query = {"query": {"bool": {"must": [
                {"match": {"res.0.status": oldStatus}},
                {"match": {"res.0.name": oldName}},
                {"match": {"res.0.modifiedOn": oldModifiedOn}}]}}}
        return query

    # This funtion push time duration to missed index
    def updateMissedDate(self, id, missedDocDuration, status, missedIndexDoc):
        es = RPT.establish_connection(self)
        if(status == "Standby"):
            body = {"script": {"inline": "ctx._source.standby_duration=params.standby_duration",
                                         "params": {"standby_duration": missedDocDuration}}}
        elif(status == "Available"):
            body = {"script": {"inline": "ctx._source.available_duration=params.available_duration",
                                         "params": {"available_duration": missedDocDuration}}}
        elif(status == "Refreshing"):
            body = {"script": {"inline": "ctx._source.refreshing_duration=params.refreshing_duration",
                                         "params": {"refreshing_duration": missedDocDuration}}}
        elif(status == "Quarantine"):
            body = {"script": {"inline": "ctx._source.quarantine_duration=params.quarantine_duration",
                                         "params": {"quarantine_duration": missedDocDuration}}}
        elif(status == "Reserved"):
            body = {"script": {"inline": "ctx._source.reserved_duration=params.reserved_duration",
                                         "params": {"reserved_duration": missedDocDuration}}}
        response = es.update(index=missedIndexDoc, id=id, body=body, ignore=400)
        print('missed date response:', response)

    # This function used to update current index documents with allocated duration
    def update(self, status, duration, id, index):
        es = RPT.establish_connection(self)
        if(status == "Standby"):
            body = {"script": {"inline": "ctx._source.standby_duration=params.standby_duration",
                                         "params": {"standby_duration": duration}}}
        elif(status == "Available"):
            body = {"script": {"inline": "ctx._source.available_duration=params.available_duration",
                                         "params": {"available_duration": duration}}}
        elif(status == "Refreshing"):
            body = {"script": {"inline": "ctx._source.refreshing_duration=params.refreshing_duration",
                                         "params": {"refreshing_duration": duration}}}
        elif(status == "Quarantine"):
            body = {"script": {"inline": "ctx._source.quarantine_duration=params.quarantine_duration",
                                         "params": {"quarantine_duration": duration}}}
        elif(status == "Reserved"):
            body = {"script": {"inline": "ctx._source.reserved_duration=params.reserved_duration",
                                         "params": {"reserved_duration": duration}}}
        response = es.update(index=index, id=id, body=body, ignore=400)
        print("response:", response, "\n")

    def addingEnvDocuments(self):
        es = self.establish_connection()
        index = "express-logs-"+self.yesterday_date()
        limit = es.indices.put_settings(index=index, body={"index.mapping.total_fields.limit": 100000})
        print("limit increase:", limit)
        env_names = ["kohn010_EO_DEPLOY", "kohn011_EO_DEPLOY", "kohn012_EO_DEPLOY",
                     "kohn013_EO_DEPLOY", "kohn014_EO_DEPLOY", "kohn016_EO_DEPLOY",
                     "kohn017_EO_DEPLOY", "kohn018_EO_DEPLOY", "kohn019_EO_DEPLOY",
                     "kohn020_EO_DEPLOY", "kohn021_EO_DEPLOY", "kohn022_EO_DEPLOY",
                     "kohn023_EO_DEPLOY"]
        missed_envDoc = []
        status_list = ["Reserved", "Available", "Quarantine", "Refreshing", "Standby"]
        for i in env_names:
            count = 0
            for dobj in scan(es, query=self.env_query(i), index=index):
                count = count+1
            if(count == 0):
                missed_envDoc.append(i)
        yesterday = (datetime.today()-timedelta(days=2)).strftime('%Y.%m.%d')
        pre_index = "express-logs-"+yesterday
        for i in missed_envDoc:
            time = 0
            id = ""
            record = None
            for j in status_list:
                for dobj in scan(es, query=self.duration_query(i, j), index=pre_index):
                    if(self.milliseconds(dobj["_source"]["@timestamp"]) > time):
                        time = self.milliseconds(dobj["_source"]["@timestamp"])
                        id = dobj["_id"]
                        record = dobj
            if record is not None:
                res_time = index.split("-")[2].replace(".", "-")+"T00:00:00.000Z"
                record["_source"]["res"]["0"]["modifiedOn"] = res_time
                id = str(record["_id"])+"-env-regulus"
                res = record["_source"]["res"]
                last_time = index.split("-")[2].replace(".", "-")+"T23:59:59.999Z"
                name = record["_source"]["res"]["0"]["name"]
                last_status = record["_source"]["res"]["0"]["status"]
                last_pools = record["_source"]["res"]["0"]["pools"]
                duration = 86400000
                status = record["_source"]["res"]["0"]["status"]
                if(status == "Reserved"):
                    status_duration = "reserved_duration"
                elif(status == "Available"):
                    status_duration = "available_duration"
                elif(status == "Quarantine"):
                    status_duration = "quarantine_duration"
                elif(status == "Refreshing"):
                    status_duration = "refreshing_duration"
                else:
                    status_duration = "standby_duration"
                dic = {
                    "old": res,
                    "res": {"0": {
                        "name": name,
                        "status": last_status,
                        "pools": last_pools,
                        "modifiedOn": last_time}},
                    "@timestamp": last_time,
                    status_duration: duration
                }
                try:
                    json_object = json.dumps(dic, default=str)
                    response = es.index(index=index, id=id, ignore=400, body=json_object)
                    print(response)
                except timeout as tout:
                    raise timeout from tout
                except Exception as e:
                    print(e)
                print("env name : ", i)
                print("id :", id, "\n\n")

    def addingDuration(self):
        es = self.establish_connection()
        index = "express-logs-"+self.yesterday_date()
        limit = es.indices.put_settings(index=index, body={"index.mapping.total_fields.limit": 100000})
        print("limit increase:", limit)
        status_list = ["Reserved", "Available", "Quarantine", "Refreshing", "Standby"]
        env_names = ["kohn010_EO_DEPLOY", "kohn011_EO_DEPLOY", "kohn012_EO_DEPLOY",
                     "kohn013_EO_DEPLOY", "kohn014_EO_DEPLOY", "kohn016_EO_DEPLOY",
                     "kohn017_EO_DEPLOY", "kohn018_EO_DEPLOY", "kohn019_EO_DEPLOY",
                     "kohn020_EO_DEPLOY", "kohn021_EO_DEPLOY", "kohn022_EO_DEPLOY",
                     "kohn023_EO_DEPLOY"]
        for i in env_names:
            time = 0
            id = ""
            record = None
            for j in status_list:
                for dobj in scan(es, query=self.duration_query(i, j), index=index):
                    if(self.milliseconds(dobj["_source"]["@timestamp"]) > time):
                        time = self.milliseconds(dobj["_source"]["@timestamp"])
                        id = dobj["_id"]
                        record = dobj
            if record is not None:
                id = str(record["_id"])+"-regulus"
                res = record["_source"]["res"]
                last_time = str(record["_source"]["@timestamp"]).split("T")[0]+"T23:59:59.999Z"
                name = record["_source"]["res"]["0"]["name"]
                last_status = record["_source"]["res"]["0"]["status"]
                last_pools = record["_source"]["res"]["0"]["pools"]
                duration = 86400000 - self.milliseconds(record["_source"]["res"]["0"]["modifiedOn"])
                status = record["_source"]["res"]["0"]["status"]
                if(status == "Reserved"):
                    status_duration = "reserved_duration"
                elif(status == "Available"):
                    status_duration = "available_duration"
                elif(status == "Quarantine"):
                    status_duration = "quarantine_duration"
                elif(status == "Refreshing"):
                    status_duration = "refreshing_duration"
                else:
                    status_duration = "standby_duration"
                dic = {
                    "old": res,
                    "res": {"0": {
                        "name": name,
                        "status": last_status,
                        "pools": last_pools,
                        "modifiedOn": last_time}},
                    "@timestamp": last_time,
                    status_duration: duration
                }
                try:
                    json_object = json.dumps(dic, default=str)
                    response = es.index(index=index, id=id, ignore=400, body=json_object)
                    print(response)
                except timeout as tout:
                    raise timeout from tout
                except Exception as e:
                    print(e)
                print("nenv name : ", i)
                print("id :", id, "\n\n")

    def firstDocDuration(self):
        es = self.establish_connection()
        index = "express-logs-"+self.yesterday_date()
        limit = es.indices.put_settings(index=index, body={"index.mapping.total_fields.limit": 100000})
        print("limit increase:", limit)
        status_list = ["Reserved", "Available", "Quarantine", "Refreshing", "Standby"]
        env_names = ["kohn010_EO_DEPLOY", "kohn011_EO_DEPLOY","kohn012_EO_DEPLOY","kohn013_EO_DEPLOY",
                     "kohn014_EO_DEPLOY","kohn016_EO_DEPLOY","kohn017_EO_DEPLOY",
                     "kohn018_EO_DEPLOY","kohn019_EO_DEPLOY","kohn020_EO_DEPLOY","kohn021_EO_DEPLOY",
                     "kohn022_EO_DEPLOY","kohn023_EO_DEPLOY"]
        for i in env_names:
            time = 86400000
            id = ""
            record = None
            for j in status_list:
                for dobj in scan(es, query=self.duration_query(i,j), index=index):
                    if(self.milliseconds(dobj["_source"]["@timestamp"]) < time):
                        time = self.milliseconds(dobj["_source"]["@timestamp"])
                        id=dobj["_id"]
                        record = dobj
            if record is not None:
                old_date = str(record["_source"]["old"]["0"]["modifiedOn"]).split("T")[0]
                res_date = str(record["_source"]["res"]["0"]["modifiedOn"]).split("T")[0]
                if old_date == res_date :
                    print("id : ", id)
                    print("env : ", i)
                    print(record["_source"]["@timestamp"],"\n\n")
                    id = str(record["_id"])+"-regulus"
                    old = record["_source"]["old"]
                    start_time = str(record["_source"]["@timestamp"]).split("T")[0]+"T00:00:00.000Z"
                    end_time = record["_source"]["old"]["0"]["modifiedOn"]
                    name = record["_source"]["old"]["0"]["name"]
                    first_status = record["_source"]["old"]["0"]["status"]
                    first_pools = record["_source"]["old"]["0"]["pools"]
                    duration = self.milliseconds(record["_source"]["old"]["0"]["modifiedOn"])
                    status = record["_source"]["old"]["0"]["status"]
                    if(status == "Reserved"):
                        status_duration = "reserved_duration"
                    elif(status == "Available"):
                        status_duration = "available_duration"
                    elif(status == "Quarantine"):
                        status_duration = "quarantine_duration"
                    elif(status == "Refreshing"):
                        status_duration = "refreshing_duration"
                    else:
                        status_duration = "standby_duration"
                    dic= {
                        "res":old,
                        "old":{"0":{
                            "name": name,
                            "status": first_status,
                            "pools" : first_pools,
                            "modifiedOn": start_time}},
                        "@timestamp" : end_time,
                        status_duration : duration
                    }
                    try:
                        json_object = json.dumps(dic, default=str)
                        response = es.index(index=index, id=id, ignore=400, body=json_object)
                        print(response)
                    except timeout as tout:
                        raise timeout from tout
                    except Exception as e:
                        print(e)
                    print("nenv name : ", i)
                    print("id :",id,"\n\n")

    def main_function(self):
        es = self.establish_connection()
        index = "express-logs-"+self.yesterday_date()
        limit = es.indices.put_settings(index=index, body={"index.mapping.total_fields.limit": 100000})
        print("limit increase:", limit)
        status = ["Reserved", "Available", "Quarantine", "Refreshing", "Standby"]
        for i in status:
            # Status name passed inside query function
            # Below for loop fetch all data which matches status name from yesturday index
            for dobj in scan(es, query=self.query(i), index=index):
                oldDate = dobj["_source"]["old"]["0"]['modifiedOn'].split("T")[0]
                newDate = dobj["_source"]["res"]["0"]['modifiedOn'].split("T")[0]
                # Taking count of missed dates and missed dates to get missed index data by using this values
                countOfmissedDates = self.days_between(oldDate, newDate)-1
                missedDates = self.missedDates(oldDate, newDate)
                print("missed dates : ", missedDates)
                # Taking old and res modifiction date into milliseconds using milliseconds method
                old_ms = self.milliseconds(dobj["_source"]["old"]["0"]['modifiedOn'])
                new_ms = self.milliseconds(dobj["_source"]["res"]["0"]['modifiedOn'])
                oldStatus = dobj["_source"]["old"]["0"]['status']
                # If count of missed dates value >=1 , first it will set duration in current document
                if(countOfmissedDates >= 0):
                    # Here the duration will be set for current document
                    duration = new_ms
                    self.update(oldStatus, duration, dobj["_id"], index)
                else:
                    duration = new_ms - old_ms
                    self.update(oldStatus, duration, dobj["_id"], index)


rpt = RPT()
rpt.main_function()
rpt.firstDocDuration()
rpt.addingDuration()
rpt.addingEnvDocuments()
