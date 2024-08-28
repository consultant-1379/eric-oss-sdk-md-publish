import json
from msdevops_metrics.gerrit_metrics.gerritcommits import Gerritcommits
from msdevops_metrics.dora_metrics.push import ElasticPush

def main_function():
        gerrit = Gerritcommits()
        elastic_push = ElasticPush()
        es=elastic_push.establish_connection_eck()
        data = elastic_push.read_json('latest-input.json','msdevops_metrics/gerrit_metrics')
        for key,value in data.items():
            pipelineName = key
            gerritName = value['gerritFullname']
            if gerritName == "":
                dic = gerrit.gerrit_except_attributes()
            else:
                data = gerrit.fetch_gerritAttributes(gerritName)
                if len(data) > 0:
                    response,id=gerrit.commits_by_user(data,pipelineName)
                    elastic_push.publish_data(es,id,response,'merged-gerrit-commits-by-user')

