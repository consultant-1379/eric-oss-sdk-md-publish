import json,sys,os,time
from msdevops_metrics.helm_version_data.helm_version import HelmData
from msdevops_metrics.dora_metrics.push import ElasticPush


def main_function():
        elastic_push = ElasticPush()
        helm = HelmData()
        es = elastic_push.establish_connection_eck()
        input_path=os.getcwd()
        data_helm_version = elastic_push.read_json('input.json','msdevops_metrics/helm_version_data')
        #os.system(f"git clone https://{helm.username}:{helm.password}@gerrit-gamma.gic.ericsson.se/a/OSS/com.ericsson.oss.eiae/eiae-helmfile")
        for key, value in data_helm_version.items():
            gerritName = value['gerritFullname']
            applicationName = key

            os.chdir(input_path) # Specifying the path where the cloned project needs to be copied
            helm.git_clone(gerritName)
            print("############## CLONED SUCCESSFULLY  ################")
            if applicationName == "eric-service-exposure-framework":
                 applicationName= "service-exposure-framework"
            chart_path = helm.find("Chart.yaml", input_path+"/"+applicationName)
            chart_data = helm.read_yaml(chart_path)
            ms_name = []
            app_name=chart_data['name']
            app_version=chart_data['version']
            product_Version="NA"
            helm.git_clone("OSS/com.ericsson.oss.eiae/eiae-helmfile")
            chart_path = helm.find("helmfile.yaml", os.getcwd())
            version_list=helm.product_version(chart_path)
            metadata_path=helm.find("metadata.yaml", os.getcwd())
            metadata_data=helm.read_yaml(metadata_path)
            try:
                for i in range(len(chart_data['dependencies'])):

                    ms_name.append(chart_data['dependencies'][i]['name']+"-"+chart_data['dependencies'][i]['version'])


                dic1={
                "microservice_name":ms_name,
                #"microservice_version":ms_version,
                "application_name":app_name,
                "application_version":app_version,
                "product_version":metadata_data["version"]
                }
            except KeyError as err:
                dic1={
                "microservice_name":"NA",
                #"microservice_version":ms_version,
                "application_name":app_name,
                "application_version":app_version,
                "product_version":metadata_data["version"]
                }
            json_object = json.dumps(dic1,default = str)
            elastic_push.publish_data(es, applicationName,json_object, "helm-versioning")
            os.system("rm -rf "+applicationName)
            print("############## DELETED SUCCESSFULLY  ################")
            print(dic1)
