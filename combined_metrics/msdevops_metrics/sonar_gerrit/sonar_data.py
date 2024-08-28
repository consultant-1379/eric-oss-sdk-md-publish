import logging,json, os, requests
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout


class SonarData:

    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        self.username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
        self.password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)

    @staticmethod
    def sonar_except_attributes(jobName,teamName):

        '''
        This function is used to insert blank values for non sonarqube projects

        '''
        return {
            "pipeline.name": jobName,
            "team.name": teamName,
            "SonarProjectName": "0",
            "TimeStamp": "0",
            "Vulnerabilities": "0",
            "Coverage": "0",
            "Codesmells": "0",
            "Bugs": "0",
        }

    def fetch_sonarTimestamp(self, sonarLink, projectKey):

        '''
        This function will fetch sonar analysis time for a given project key

        '''
        try:
            response = requests.get(
                f'https://{self.username}:{self.password}@{sonarLink}/api/components/show?component={projectKey}').json()
            val_timeStamp = response['component']['analysisDate']
            return val_timeStamp
        except KeyError as error:
            return 0

    def fetch_sonarAttributes(self, sonarLink, projectKey, jobName, timeStamp, teamName):

        '''
        This function fetch the different sonarqube attributes from restapi with the given project key

        '''

        try:
            response = requests.get(
                f'https://{self.username}:{self.password}@{sonarLink}/api/measures/component?metricKeys=bugs%2Cvulnerabilities%2Ccode_smells%2Ccoverage&component={projectKey}').json()

            projectName = response['component']['name']
            dict = {
                "pipeline.name": jobName,
                "team.name": teamName,
                "SonarProjectName": projectName,
                "TimeStamp": str(timeStamp),
                "Vulnerabilities": "NA",
                "Coverage": "NA",
                "Codesmells": "NA",
                "Bugs": "NA",
            }

            for values in response['component']['measures']:
                if (values["metric"]=="vulnerabilities"):
                    dict["Vulnerabilities"]=values["value"]
                elif (values["metric"]=="bugs"):
                    dict["Bugs"]=values["value"]
                elif (values["metric"]=="coverage"):
                    dict["Coverage"]=values["value"]
                elif (values["metric"]=="code_smells"):
                    dict["Codesmells"]=values["value"]
            return dict
        except Exception as error:
            return {
            "pipeline.name": jobName,
            "team.name":teamName,
            "SonarProjectName": "0",
            "TimeStamp": "0",
            "Vulnerabilities": "0",
            "Coverage": "0",
            "Codesmells": "0",
            "Bugs": "0",
        }

    def read_json(self):
        try:
            with open(os.path.join(os.getcwd(), 'input.json'), "r", encoding="utf-8") as file1:
                return json.load(file1)
        except IOError as ie:
            raise IOError from ie


