FROM armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release/sles:4.1.0-31 as base_image
ARG CBO_REPO_URL=https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/4.1.0-31
#Install Java 8
RUN zypper ar -C -G -f $CBO_REPO_URL?ssl_verify=no \
    COMMON_BASE_OS_SLES_REPO \
    && zypper --non-interactive in python3 python3-pip git-core curl\
    && zypper clean --all \
    && zypper rr COMMON_BASE_OS_SLES_REPO

RUN pip install pyyaml

#RUN apt-get update && \
#    apt-get upgrade -y && \
#    apt-get install -y git

COPY requirements.txt .
RUN pip install -r requirements.txt


COPY msdevops_metrics /msdevops_metrics/
COPY sonar_gerrit_calling.py .
COPY dora_metrics_calling.py .
COPY jira.py .
COPY drcheck.py .
COPY gerritmetrics.py .
COPY jenkinsmetrics.py .
COPY helmversion.py .
COPY gerrit_patchset.py .
COPY RPT_retention.py .


from base_image as sonar_gerrit
ENTRYPOINT ["/usr/bin/python3", "sonar_gerrit_calling.py"]

from base_image as dora_metrics
ENTRYPOINT ["/usr/bin/python3", "dora_metrics_calling.py"]

from base_image as jira
ENTRYPOINT ["/usr/bin/python3", "jira.py"]

from base_image as drcheck
ENTRYPOINT ["/usr/bin/python3", "drcheck.py"]

from base_image as gerritmetrics
ENTRYPOINT ["/usr/bin/python3", "gerritmetrics.py"]

from base_image as jenkinsmetrics
ENTRYPOINT ["/usr/bin/python3", "jenkinsmetrics.py"]

from base_image as helm_version_data
ENTRYPOINT ["/usr/bin/python3", "helmversion.py"]

from base_image as gerrit_patchset_upload
ENTRYPOINT ["/usr/bin/python3", "gerrit_patchset.py"]

from base_image as rpt-retention
ENTRYPOINT ["/usr/bin/python3", "RPT_retention.py"]
