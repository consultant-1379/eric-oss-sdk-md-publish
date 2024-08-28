import json,sys,os
from msdevops_metrics.sonar_gerrit.sonar_data import SonarData
from msdevops_metrics.sonar_gerrit.gerrit_data import GerritData
from msdevops_metrics.dora_metrics.push import ElasticPush


def main_function():
        elastic_push = ElasticPush()
        sonar = SonarData()
        gerrit = GerritData()
        es = elastic_push.establish_connection_eck()
        input_path=os.getcwd()
        data_sonar_gerrit = elastic_push.read_json('input.json','msdevops_metrics/sonar_gerrit')

        for key, value in data_sonar_gerrit.items():
            pipelineName = key
            gerritName = value['gerritFullname']
            sonarProjectKey = value['sonarprojectKey']
            sonarLink = value['sonarLink']
            teamName = elastic_push.get_teamName(pipelineName)
            if sonarProjectKey == "":
                dic1 = sonar.sonar_except_attributes(pipelineName,teamName)
            else:
                TimeStamp = sonar.fetch_sonarTimestamp(sonarLink, sonarProjectKey)
                dic1 = sonar.fetch_sonarAttributes(sonarLink, sonarProjectKey, pipelineName, TimeStamp,teamName)
            branch = "master"
            gerritName = value['gerritFullname']
            if gerritName == "":
                dic2 =gerrit.gerrit_except_attributes(gerritName)
            else:
                changes=gerrit.fetch_gerritAttributes(gerritName)
                review_time = gerrit.get_review_time(changes)
                dic2 = gerrit.get_time_diff(changes,pipelineName,review_time,branch)
            dic2.update(dic1)
            json_object = json.dumps(dic2, default=str)
            elastic_push.publish_data(es, pipelineName,json_object, "sonarqube-gerrit-data" )


