from msdevops_metrics.va_stage_fetch.va_stage_fetch import vastagemetrics
import logging
import os
logging.basicConfig(level=logging.DEBUG)
LOG=logging.getLogger(__name__)
def main_function():
    va = vastagemetrics()
    tls_elk=va.establish_connection_eck()
    temp =['1','2']
    try:
        for j in temp:
            Jobs_file='fem'+j+'sjobs.txt'
            try:
                with open(os.path.join(os.getcwd(), Jobs_file), "r", encoding="utf-8") as file1:
                    Lines = file1.readlines()
                    for line in Lines:
                        try:
                            count=0
                            api_url=va.fetch_api_url("{}".format(line.strip()), j)
                        except json.JSONDecodeError:
                            LOG.info(f"Json error at url :", api_url)
                        va.va_stage_metrics(api_url,count,tls_elk)
            except FileNotFoundError:
                LOG.error("Fem jobs file is not found")
    except IOError as ie:
        raise IOError from ie 
