#added team_name attribute to the dictionary
import json
import logging as LOG
from operator import index
import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from msdevops_metrics.dora_metrics.push import ElasticPush
import requests

class GerritPatchset:

    def __init__(self):
            LOG.basicConfig()
            self.LOG = LOG.getLogger(__name__)
            self.LOG.setLevel(LOG.DEBUG)
            self.username = 'MMTADM'#os.environ.get('FUNCTIONAL_USER_USERNAME', None)
            self.password = 'Er4mrqvBybp7F6MWtCtGn9Fg'#os.environ.get('FUNCTIONAL_USER_PASSWORD', None)

    def job_names(self):
        return {
            "name": None,
            
        }

    def establish_connection(self):

        try:
            elk = Elasticsearch(['https://elastic.hahn130.rnd.gic.ericsson.se:443'],http_auth=('elastic','4lTX6kU6vURX89S0RsGK7066'), verify_certs=False)
            self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            self.LOG.error(EE)
        return elk   

    def push_metrics(self,elk, docket_content,id, index_name):

        ''' This  function is to push metrics into the index of ElasticSearch DB '''
        
        try:
            elk.index(index='patchset-uploader',id=id,ignore=400, body=docket_content, doc_type = "_doc")
            LOG.info(f"Data pushed to index successfully")
        except Exception as e:
            print(e)

    def get_teamName(self,pipelineName):
        try:
            microserviceName = pipelineName.split("_")[0]
            response = requests.get('https://pdu-oss-tools1.seli.wh.rnd.internal.ericsson.com/team-inventory/api/teams').json()

            for i in range(len(response)):
                team_name = response[i]['name']
                ms_name = response[i]['microservice']
                if ms_name is not None:
                    if microserviceName in ms_name.lower() :
                        return team_name

            return "NULL"
        except requests.ConnectionError as error:
            self.LOG.info("Connection error at Team inventory URL")

    def microservice_names(self,fem):
       
        list=[]
        try:
            response= requests.get(
                fem+'/api/json?tree=jobs[name,lastBuild[number,duration,timestamp,result,changeSet[items[msg,author[fullName]]]]]',
                auth=(self.username, self.password)).json()
            response = response['jobs']
            for job in response:
                dict= job['name']
                if (("Admin" in job['name'])==False) and ("Publish" in job['name'] or "Release" in job['name']):
                    list.append(dict)
                    print(list)
            return list
        except KeyError as keyerr:
            self.LOG.error(f"There are no Job's in this {fem}")
        except requests.exceptions.HTTPError as errh:
            self.LOG.error(errh)
        except requests.exceptions.RequestException as err:
            self.LOG.error(err)

    def metrics(self,job_names,elk,es):
        for ms_name in job_names:
            response = requests.get('https://fem2s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins/job/'+ms_name+'/lastSuccessfulBuild/api/json',auth=(self.username, self.password))
            if response.status_code == 404:
                response = requests.get('https://fem1s11-eiffel216.eiffel.gic.ericsson.se:8443/jenkins/job/'+ms_name+'/lastSuccessfulBuild/api/json',auth=(self.username, self.password))
            data=response.text
            try:
                parse_json = json.loads(data)
                ms = parse_json['fullDisplayName']
                ms = ms.split(' ')[0]
                team_name = self.get_teamName(ms)
                patchset1 = (parse_json['actions'][0]['causes'][0]['shortDescription'])
                patchset2 = patchset1.split(': ')[1]
                patchset3 = patchset2.split(' ')[0]
                patchset4 = patchset3.split('/')
                date = parse_json['timestamp']
                if patchset4[3].isnumeric():
                    for i in range(10,40):
                        try:
                            if parse_json['actions'][5]['parameters'][i]['name'] == "GERRIT_PATCHSET_UPLOADER_NAME":
                                patchset_owner = parse_json['actions'][5]['parameters'][i]['value']
                                dictionary = {
                                        "pipeline.name" : ms,
                                        "Gerrit_Patchset_URL" : patchset3,
                                        "Patchset_Owner" : patchset_owner,
                                        "date" : date,
                                        "team.name":team_name
                                        }
                                json_object = json.dumps(dictionary, indent=4, default=str)
                                #self.push_metrics(elk, json_object ,id, index)
                                elk.publish_data(es,dictionary["pipeline.name"] , json_object, "patchset-uploader")
                        except IndexError:
                            self.LOG.error('Ref #Updated Patchset')
                        except KeyError:
                            self.LOG.error('Ref Updated Patchset')
                else:
                    dictionary = {
                                    "pipeline.name" : ms,
                                    "Gerrit_Patchset_URL" : "N/A",
                                    "Patchset_Owner" : "N/A"
                                    }        
            except json.decoder.JSONDecodeError:
                self.LOG.error("JSON Error")
            except KeyError:
                self.LOG.error('Ref Updated Patchset')
            except IndexError:
                self.LOG.error('Ref Updated Patchset')

    def main(self):
        functional_user_username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
        functional_user_password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
        gp = GerritPatchset()
        fem_list=[]
        fem_list.append("https://fem1s11-eiffel216.eiffel.gic.ericsson.se:8443/jenkins")
        fem_list.append("https://fem2s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins")
        for fem_name in fem_list:
            elk=ElasticPush()
            es = elk.establish_connection_eck()
            job_name=gp.microservice_names(fem_name)
            metrics=gp.metrics(job_name,elk,es)

