import requests
import json
import logging
from msdevops_metrics.dora_metrics import jenkins_util as Jenkins_Util
from msdevops_metrics.dora_metrics.push import ElasticPush


class JenkinsData:
    '''
    This class contains functions to calculaate failurerate and lead time
    '''
    def __init__(self, username, password):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        self.username = username
        self.password = password
        self.time_data = []
        self.no_build = []

    @staticmethod
    def build_directory_time(build_data):
        '''
        The function is to arrange build data into directory format
        :param build_data:
        :return: directory of build data
        '''
        data = Jenkins_Util.build_directory_time()
        data['id'] = build_data['id']
        data['status'] = build_data['status']
        data['startTimeMillis'] = build_data['startTimeMillis']
        data['endTimeMillis'] = build_data['endTimeMillis']
        data['duration']=build_data["durationMillis"]
        return data

    def job_names(self,fem):
        '''
        This function fetches Publish and Release jobs names from api response
        :param fem:
        :return: jobs names will be written into a file
        '''
        list=[]
        try:
            response= requests.get(
                fem+'/api/json?tree=jobs[name,lastBuild[number,duration,timestamp,result,changeSet[items[msg,author[fullName]]]]]',
                auth=(self.username, self.password)).json()
        except requests.exceptions.HTTPError as errh:
            self.LOG.error(errh)
        except requests.exceptions.RequestException as err:
            self.LOG.error(err)

        try:
            for job in response['jobs']:
                dict= Jenkins_Util.job_names()
                dict["name"]= job['name']
                dict["last_checked"]= 0
                if (("Admin" in job['name'])==False) and ("Publish" in job['name'] or "Release" in job['name']):
                    list.append(dict)
            return list
        except KeyError as keyerr:
            self.LOG.error(f"There are no Job's in this {fem}")


    def get_last_build(self, name,fem):
        '''
        This function uses api to collect latest build number of a Job
        :param name:
        :param fem:
        :return: This will return the response of the api
        '''
        try:
            return requests.get(
                fem+'/job/{}/lastBuild/buildNumber'.format(
                    name),
                auth=(self.username, self.password))
            #last_build.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            self.LOG.error(errh)
        except requests.exceptions.RequestException as err:
            self.LOG.error(err)

    def build_response(self, job_name, build_no,fem):
        '''
        This function uses api to get one build response
        :param job_name:
        :param x:
        :param fem:
        :return: Returns api response
        '''
        try:

            return requests.get(
                fem+"/job/{}/{}/wfapi/describe".format(
                    job_name, build_no), auth=(self.username, self.password))
        except requests.exceptions.HTTPError as errh:
            self.LOG.error(errh)
        except requests.exceptions.RequestException as err:
            self.LOG.error(err)

    def build_details(self, last_build, job_name,fem):
        '''
        This functions fetches last 50 builds data of a pipeline
        :param last_build:
        :param job_name:
        :param fem:
        :return: This will return an array of build details of a job
        '''
        build_list = []
        self.LOG.info(f'Collecting data of {job_name}')
        for build_no in reversed(range(last_build.json() - 49, last_build.json() + 1)):
            if build_no > 0:
                try:
                    build_data = self.build_response(job_name, build_no,fem).json()
                except requests.exceptions.RequestException as e:
                    continue
                except ValueError as ex:
                    break
                data = self.build_directory_time(build_data)
                build_list.append(data)
        return build_list

    def job_time(self, job_names,fem):
        '''
        This function will pass the build details to main function where calculation occus
        :param job_names:
        :param fem:
        '''
        for job_name in job_names:
            job_name = job_name["name"]
            last_build = self.get_last_build(job_name,fem)
            if last_build.status_code == 404:
                self.LOG.debug(f"There is no builds in {job_name}")
                self.no_build.append(job_name)
                continue
            list_array = self.build_details(last_build, job_name,fem)
            self.LOG.info(f'Collected build details of {job_name}')
            if( len(list_array)!=0):
                print(list_array)
                #self.failureRate(list_array, job_name)
                self.leadtime(list_array, job_name)


    def failureRate(self,data, job_name):
        '''
        This is the function sends build data required for failureRate to elk
        :param data:
        :param job_name:
        '''
        id = 1
        es=ElasticPush()
        for data in reversed(data):

            dict = Jenkins_Util.failurerate()
            dict["id"]=data["id"]
            dict["pipeline.name"]=job_name
            dict["startTime"] = data["startTimeMillis"]
            dict["endTime"] = data["endTimeMillis"]
            dict["status"] = data["status"]
            id += 1
            index_name=job_name+"-"+dict["id"]
            es.Main(index_name, dict,"merged-changefailuredata")
        #self.LOG.debug(f'Failure rate data is pushed for {job_name}')
        self.LOG.info(f'Failure rate of {job_name} was pushed to {index_name}')

    def leadtime(self,data,job_name):
        '''
        This is the function sends build data required for leadtime to elk
        :param data:
        :param job_name:
        '''
        es=ElasticPush()
        id=1
        for index in data:
            dict=Jenkins_Util.leadtime()
            dict["id"]=job_name+"-"+str(id)
            dict["startTime"]=index["startTimeMillis"]
            dict["endTime"]=index["endTimeMillis"]
            dict["duration"]=index["duration"]
            dict["pipeline.name"]=job_name
            dict["team.name"]=es.get_teamName(job_name)
            id+=1
            index_name=job_name+"-"+str(id)
            print(dict)
            es.Main(index_name, dict, "merged-leadtimeforchange")
        #self.LOG.debug(f'Lead time data is pushed for {job_name}')
        self.LOG.info(f'Leadtime of {job_name} was pushed to {index_name}')
