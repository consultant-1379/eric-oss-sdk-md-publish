import logging,json, os, requests, yaml
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError, ConnectionTimeout as timeout
from yaml.loader import SafeLoader


class HelmData:

    def __init__(self):
        logging.basicConfig()
        self.LOG = logging.getLogger(__name__)
        self.LOG.setLevel(logging.DEBUG)
        self.username = "mmtadm"#os.environ.get('FUNCTIONAL_USER_USERNAME', None)
        self.password = "Er4mrqvBybp7F6MWtCtGn9Fg"#os.environ.get('FUNCTIONAL_USER_PASSWORD', None)


    def git_clone(self,gerritrepo):
        if self.password and self.username:
            #url_string = r"git clone https://{}:{}@gerrit-gamma.gic.ericsson.se/a/{}".format(self.username, self.password, gerritrepo)
            #os.system(url_string)
            lower_case_username = self.username.lower()
            os.system(f"git clone https://{lower_case_username}:{self.password}@gerrit-gamma.gic.ericsson.se/a/{gerritrepo}")
            #Repo.clone_from("https://{self.username}:{self.password}@gerrit-gamma.gic.ericsson.se/a/{gerritrepo}",gerritrepo)
            #dload.git_clone("https://{self.username}:{self.password}@gerrit-gamma.gic.ericsson.se/a/{gerritrepo}")
            #dload.git_clone("https://{self.username}:{self.password}@gerrit-gamma.gic.ericsson.se/a/{gerritrepo}")

    @staticmethod
    def find(name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)
    
    @staticmethod
    def read_yaml(yaml_path):
        try:
            with open(yaml_path) as f:
                return yaml.load(f, Loader=SafeLoader)
        except IOError as ie:
            raise IOError from ie

    @staticmethod
    def product_version(chart_path):
        read_data = open(chart_path, 'r')
        Lines = read_data.readlines()
        data = ""
        for line in Lines:
            if (line.__contains__("{{") != True or line.__contains__("}}") != True):
                data = data + line
                data = data + '\n'
        version_list = list(yaml.load_all(data, Loader=SafeLoader))[2]["releases"]
        return version_list
        for version in version_list:
            print(version["name"])
            try:
                print(version["version"])
            except:
                print("No Version Found")





