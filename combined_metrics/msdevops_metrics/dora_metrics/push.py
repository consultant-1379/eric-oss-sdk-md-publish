import os
import json
import logging, requests
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout


class ElasticPush:
    '''
    This class to connect to ELK and push the data
    '''

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

    def publish_data(self,es, id,docket_content, indices):
        '''
        This function publishes data to particular index
        :param es:
        :param id:
        :param docket_content:
        :param indices:
        :return:
        '''
        tls_elk=self.establish_connection_eck()
        try:
            es.index(index=indices, id=id, ignore=400 , body=docket_content,doc_type='_doc')
            tls_elk.index(index=indices, id=id, ignore=400 , body=docket_content,doc_type='_doc')
            #self.LOG.info(f"Data pushed to {indices} index successfully")
        except timeout as tout:
            raise timeout from tout
        except Exception as e:
            print(e)

    @staticmethod
    def get_teamName(pipelineName):
        try:
            #microserviceName = pipelineName.split("_")[0]
            if "_Publish" in pipelineName:
                pipelineName = pipelineName.replace("_Publish", "")
            elif "_Release" in pipelineName:
                pipelineName = pipelineName.replace("_Release", "")
            

            response = requests.get('https://pdu-oss-tools1.seli.wh.rnd.internal.ericsson.com/team-inventory/api/teams').json()
            for i in range(len(response)):
                team_name='NULL'
                ms_name = response[i]['microservice']
                if ms_name is not None:
                    team_name = response[i]['name']
                    if pipelineName in ms_name.lower() :
                        return team_name

            return "NULL"
        except requests.ConnectionError as error:
            raise requests.ConnectionError from error



    @staticmethod
    def read_data(filename,path):
        '''
        This function reads any files in JSon format
        :param filename:
        :return:
        '''
        try:
            with open(os.path.join(path, filename), "r", encoding="utf-8") as data:
                try:
                    docket_content = data.read()
                    return docket_content
                except ValueError as ve:
                    raise ValueError from ve
        except IOError as ie:
            raise IOError from ie

    @staticmethod
    def read_json(fileName,path):
        try:
            with open(os.path.join(os.getcwd(),path, fileName), "r", encoding="utf-8") as file1:
                return json.load(file1)
        except IOError as ie:
            raise IOError from ie

    def Main(self,id, response,indices):
        '''
        This is the main method where initiation starts
        :param id:
        :param response:
        :param indices:
        :return:
        '''
        es = self.establish_connection_eck()
        docket_content = json.dumps(response)
        self.publish_data(es, id, docket_content,indices)


