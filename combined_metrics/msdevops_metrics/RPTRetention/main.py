from elasticsearch import Elasticsearch
import datetime
import logging

class RPT_retention:

    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        try:
            self.es = Elasticsearch('http://es.hahn051.rnd.gic.ericsson.se:80') 
            #self.LOG.info(f"connection established successfully")
        except ElasticConnectionError as EE:
            raise ElasticConnectionError from EE
        

    def fetching_creation_date(self,index_name):
        '''
        This function is used to get the creation date of a particular index
        :param index_name: index_name it contains name of the index
        :return: creation date from the index name not from info
        '''
        date_str = index_name.split("-")[-1]  # Extract the date part of the string
        date = datetime.datetime.strptime(date_str, "%Y.%m.%d")
        return date

    def target_date_fun(self):
        '''
        This function will gives us the target date which is three months older month first date
        :return: target date
        '''
        d=datetime.datetime.now()
        current_month = d.month
        d.replace(day=1)
        target_month=(current_month - 3 - 1) % 12 + 1
        target_year = d.year + ((current_month - 3 - 1) // 12)
        date_string=str(target_year)+"-"+str(target_month)+"-01"
        target_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return target_date

    def get_all_index(self):
        '''
        This is the main function, it fetches all the index names creation date and compare that with target date if
        it matches we will delete that index
        :return: NA
        '''
        indices = self.es.indices.get(index='*')
        target_date = self.target_date_fun()
        self.LOG.info(f"target date as per RPT retension policy is {target_date}")
        # Loop through the indices and print the index name and information
        index_deleted=False
        for index_name, index_info in indices.items():
            if index_name.find("express-logs")==0 or index_name.find("express-logs-staging")==0:
                creation_date = self.fetching_creation_date(index_name)
                if creation_date < target_date:
                    index_deleted=True
                    self.LOG.info(f"Deleting the index {index_name} created on {creation_date}")
                    self.es.indices.delete(index=index_name)

        if index_deleted==False:
            self.LOG.info("No index was deleted")
          


