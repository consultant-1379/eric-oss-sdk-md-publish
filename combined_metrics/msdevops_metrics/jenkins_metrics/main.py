import os
from msdevops_metrics.jenkins_metrics.jenkins_bld import JenkinsBuildMetrics
import json
import logging

logging.basicConfig(level=logging.DEBUG)
LOG=logging.getLogger(__name__)

def main_function():
    jbe = JenkinsBuildMetrics()

    print("connection established")
    temp =['1','2','8']
    try:
        for j in temp:
            Jobs_file='fem'+j+'sjobs.txt'
            try:
                with open(os.path.join(os.getcwd(),"msdevops_metrics/jenkins_metrics", Jobs_file), "r", encoding="utf-8") as file1:
                    Lines = file1.readlines()
                    for line in Lines:
                        try:
                            count=0
                            api_url=jbe.fetch_api_url("{}".format(line.strip()), j)
                        except json.JSONDecodeError:
                            LOG.info(f"Json error at url :", api_url)
                        jbe.build_metrics(api_url,count)
            except FileNotFoundError:
                LOG.error("Fem jobs file is not found")
    except IOError as ie:
        raise IOError from ie
