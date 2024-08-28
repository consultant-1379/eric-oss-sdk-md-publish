
from cmath import log
from itertools import count
import logging,sys,json,os,operator,requests,time
from pydoc import doc
from re import S
from urllib import response
from msdevops_metrics.dora_metrics.push import ElasticPush
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError,ConnectionTimeout as timeout

LOG=logging.getLogger(__name__)

class JenkinsBuildMetrics:
    
    def __init__(self):
            logging.basicConfig()
            self.LOG = logging.getLogger(__name__)
            self.LOG.setLevel(logging.DEBUG)
            self.username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
            self.password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)

    def get_teamName(self,pipelineName):
        try:
            if "_Publish" in pipelineName:
                pipelineName = pipelineName.replace("_Publish", "")
            elif "_Release" in pipelineName:
                pipelineName = pipelineName.replace("_Release", "")

            response = requests.get('https://pdu-oss-tools1.seli.wh.rnd.internal.ericsson.com/team-inventory/api/teams').json()

            for i in range(len(response)):
                team_name = response[i]['name']
                ms_name = response[i]['microservice']
                if ms_name is not None:
                    if pipelineName in ms_name.lower() :
                        return team_name

            return "NULL"
        except requests.ConnectionError as error:
            self.LOG.info("Connection error at Team inventory URL")

    def fetch_api_url(self,job_name,j):

        ''' This function is to fetch url of the API from which the metrics have to be retreived '''

        url = []
        if j == '1':
            fem_api_url='https://fem1s11-eiffel216.eiffel.gic.ericsson.se:8443/jenkins/job/'+job_name+'/api/json?fetchAllbuildDetails=True'
        elif j == '2':
            fem_api_url='https://fem2s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins/job/'+job_name+'/api/json?fetchAllbuildDetails=True'
        elif j == '8':
            fem_api_url='https://fem8s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins/job/'+job_name+'/api/json?fetchAllbuildDetails=True'
        else:
            LOG.info("Unable to set Fem URL!")
        try:
            response_API = requests.get(fem_api_url,auth=(self.username, self.password))
            data2 = response_API.text
            try:
                parse_json = json.loads(data2)
                if len(parse_json['builds']) > 0 :
                    for itr in parse_json['builds']:
                        fem_api_url=itr['url']+'wfapi/describe'
                        url.append(fem_api_url)
            except json.decoder.JSONDecodeError:
                LOG.info("JSON error at the fem")
                
            return url
        except requests.ConnectionError:
            LOG.info("Connection error")
        except json.decoder.JSONDecodeError:
            LOG.debug("parsing not done")

    def build_metrics(self,url,count):

        ''' This function retreives the required build metrics and inducted into a dictionary. 
            This dicstionary is pushed into the ElasticSearch DB '''

        build_id_list=[]
        for index,har_pav in enumerate(url):
            count=count+1
            if count == 51:
                break           
            try:
                response_API3=requests.get(har_pav, auth=(self.username, self.password))
                data3=response_API3.text
                try:
                    parse_json3 = json.loads(data3)
                    tmp_job = parse_json3['_links']['self']['href']
                    tmp_job_str = tmp_job.split("/")
                    if tmp_job_str[2] == 'view':
                        job = tmp_job_str[5]
                        team_name = self.get_teamName(job)
                    elif tmp_job_str[2] == 'user':
                        job = tmp_job_str[8]
                        team_name = self.get_teamName(job)
                    else:
                        job = tmp_job_str[3]
                        team_name = self.get_teamName(job)
                    build_id = parse_json3['id']
                    job_status = parse_json3['status']
                    start_time = parse_json3['startTimeMillis']
                    _id=count               
                    dictionary = {
                                "BuildId":build_id,
                                "JobStatus":job_status,
                                "pipeline.name":job,
                                "StartTime":start_time,
                                "Id":_id,
                                "team.name":team_name
                                }
                    if index == 0:
                        build_id_list.append(job+'-'+str(build_id))                
                    json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                    try:                    
                        with open("jenkins-data.json", "w") as json_file:
                            json_file.write(json_object)
                        with open("jenkins-data.json", "r", encoding="utf-8") as data:
                            docket_content = data.read()
                        index_name=job+'-'+str(_id)                        
                        elastic_push = ElasticPush()
                        es=elastic_push.establish_connection_eck()
                        elastic_push.publish_data(es,index_name,docket_content,'merged-jenkins-final')
                        LOG.info("Build metrics are being pushed to Elasticsearch DB")
                    except IOError as ie:
                        self.LOG("IO Error at the jenkins-data.json")
                except json.decoder.JSONDecodeError:
                        self.LOG("JSON Error occured")
                LOG.info("Build metrics are pushed to Elasticsearch DB")    
            except json.decoder.JSONDecodeError:
                        self.LOG("JSON Error occured")

