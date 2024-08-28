from cmath import log
from distutils.command.build import build
from itertools import count
import logging, sys, json, os, operator, requests, time
from unittest import skip
from pydoc import doc
from re import S
from urllib import response
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
LOG = logging.getLogger(__name__)
class vastagemetrics:
    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        self.username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
        self.password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
    def establish_connection_eck(self):
        ''' This function is to establish a cinnection with Elasticsearch DB '''
        try:
            tls_elk = Elasticsearch(['https://elastic.hahn130.rnd.gic.ericsson.se:443'],
                                    http_auth=('elastic', '4lTX6kU6vURX89S0RsGK7066'), verify_certs=False)
            self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        return tls_elk
    def get_teamName(self, pipelineName):
        try:
            microserviceName = pipelineName.split("_")[0]
            response = requests.get(
                'https://pdu-oss-tools1.seli.wh.rnd.internal.ericsson.com/team-inventory/api/teams').json()
            for i in range(len(response)):
                team_name = response[i]['name']
                ms_name = response[i]['microservice']
                if ms_name is not None:
                    if microserviceName in ms_name.lower():
                        return team_name
            return "NULL"
        except requests.ConnectionError as error:
            self.LOG.info("Connection error at Team inventory URL")
    def push_metrics(self,  tls_elk, docket_content, id):
        ''' This  function is to push metrics into the index of ElasticSearch DB '''
        try:
            tls_elk.index(index='va_stage_data', id=id, ignore=400, body=docket_content, doc_type="_doc")
            LOG.info(f"Data pushed to index successfully")
        except timeout as tout:
            raise timeout from tout
        except Exception as e:
            raise Exception from e
    def fetch_api_url(self, job_name, j):
        ''' This function is to fetch url of the API from which the metrics have to be retreived '''
        url = []
        if j == '1':
            fem_api_url = 'https://fem1s11-eiffel216.eiffel.gic.ericsson.se:8443/jenkins/job/' + job_name + '/api/json?fetchAllbuildDetails=True'
        else:
            fem_api_url = 'https://fem2s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins/job/' + job_name + '/api/json?fetchAllbuildDetails=True'
        try:
            response_API = requests.get(fem_api_url, auth=(self.username, self.password))
            data2 = response_API.text
            try:
                parse_json = json.loads(data2)
                if len(parse_json['builds']) > 0:
                    for itr in parse_json['builds']:
                        fem_api_url = itr['url'] + 'wfapi/describe'
                        url.append(fem_api_url)
            except json.decoder.JSONDecodeError:
                LOG.info(f"Skipped at the build of :", url)
                LOG.debug(f"{url}")
            return url
        except requests.ConnectionError:
            LOG.info("Connection error")
        except json.decoder.JSONDecodeError:
            LOG.debug("parsing not done")
    def va_stage_metrics(self, url, count, tls_elk):
        ''' This function retreives the required Vulnerability Analysis stage metrics and inducted into a dictionary. 
            This dicstionary is pushed into the ElasticSearch DB '''
        for har_pav in url:
            count = count + 1
            if count == 51:
                break
            try:
                response_API3 = requests.get(har_pav, auth=(self.username, self.password))
                data3 = response_API3.text
                try:
                    parse_json3 = json.loads(data3)
                    try:
                        if (parse_json3['stages'][14]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][14]['status'] == 'FAILED') and (
                                parse_json3['stages'][13]['status'] != 'FAILED'):
                            print('precedent stage to VA is failed')
                            stage = parse_json3['stages'][14]['name']
                            stage_status = parse_json3['stages'][14]['status']
                            start_time = parse_json3['stages'][14]['startTimeMillis']
                            build_id = parse_json3['id']
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
                            _id = job + str(count)
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            id = job
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                self.LOG.info("IOError")
                        elif (parse_json3['stages'][15]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][15]['status'] == 'FAILED') and (
                                parse_json3['stages'][14]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][15]['name']
                            stage_status = parse_json3['stages'][15]['status']
                            start_time = parse_json3['startTimeMillis']
                            end_time = parse_json3['endTimeMillis']
                            build_id = parse_json3['id']
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
                            _id = job + str(count)
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                self.LOG.info("IOError")
                        elif (parse_json3['stages'][13]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][13]['status'] == 'FAILED') and (
                                parse_json3['stages'][12]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][13]['name']
                            stage_status = parse_json3['stages'][13]['status']
                            start_time = parse_json3['startTimeMillis']
                            build_id = parse_json3['id']
                            _id = count
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
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "build_Id": build_id,
                                "Id": _id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                self.LOG.info("IOError")
                        elif (parse_json3['stages'][17]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][17]['status'] == 'FAILED') and (
                                parse_json3['stages'][16]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][17]['name']
                            stage_status = parse_json3['stages'][17]['status']
                            start_time = parse_json3['startTimeMillis']
                            _id = count
                            build_id = parse_json3['id']
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
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                raise IOError from ie
                        elif (parse_json3['stages'][19]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][19]['status'] == 'FAILED') and (
                                parse_json3['stages'][18]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][19]['name']
                            stage_status = parse_json3['stages'][19]['status']
                            start_time = parse_json3['startTimeMillis']
                            _id = count
                            build_id = parse_json3['id']
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
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                raise IOError from ie
                        elif (parse_json3['stages'][16]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][16]['status'] == 'FAILED') and (
                                parse_json3['stages'][15]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][16]['name']
                            stage_status = parse_json3['stages'][16]['status']
                            start_time = parse_json3['startTimeMillis']
                            _id = count
                            build_id = parse_json3['id']
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
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                raise IOError from ie
                        elif (parse_json3['stages'][18]['name'] == 'Vulnerability Analysis') and (
                                parse_json3['stages'][18]['status'] == 'FAILED') and (
                                parse_json3['stages'][17]['status'] != 'FAILED'):
                            stage = parse_json3['stages'][18]['name']
                            stage_status = parse_json3['stages'][18]['status']
                            start_time = parse_json3['startTimeMillis']
                            _id = count
                            build_id = parse_json3['id']
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
                            dictionary = {
                                "stage_Name": stage,
                                "stage_Status": stage_status,
                                "pipeline.name": job,
                                "start_Time": start_time,
                                "Id": _id,
                                "build_id": build_id,
                                "team.name": team_name
                            }
                            json_object = json.dumps(dictionary, indent=4, sort_keys=True, default=str)
                            print(json_object)
                            with open("added_ms_info.json", "w") as outfile:
                                json.dump(json_object, outfile)
                            try:
                                with open("va_stage_info", "w") as json_file:
                                    json_file.write(json_object)
                                with open("va_stage_info", "r", encoding="utf-8") as data:
                                    docket_content = data.read()
                                index_name = job + '-' + str(_id)
                                self.push_metrics( tls_elk, docket_content, index_name)
                                LOG.info("VA Stage Info has been pushed to ELK successfully")
                            except IOError as ie:
                                raise IOError from ie
                    except IndexError:
                        LOG.info("Index error")
                except json.decoder.JSONDecodeError:
                    LOG.info("JSON Error")
            except json.decoder.JSONDecodeError:
                LOG.info("JSON Error")