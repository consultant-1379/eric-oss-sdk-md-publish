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



COPY Main_RPT.py .
COPY RetentionPolicy.py .


from base_image as rpt
ENTRYPOINT ["/usr/bin/python3", "Main_RPT.py"]

from base_image as retention_policy
ENTRYPOINT ["/usr/bin/python3", "RetentionPolicy.py"]
