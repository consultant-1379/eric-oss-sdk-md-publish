FROM armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release/sles:4.1.0-31 as base_image
ARG CBO_REPO_URL=https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/4.1.0-31
#Install Java 8
RUN zypper ar -C -G -f $CBO_REPO_URL?ssl_verify=no \
    COMMON_BASE_OS_SLES_REPO \
    && zypper --non-interactive in python3 python3-pip curl\
    && zypper clean --all \
    && zypper rr COMMON_BASE_OS_SLES_REPO
RUN pip install pyyaml
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY msdevops_metrics /msdevops_metrics/

COPY vastage.py .
COPY fem1sjobs.txt .
COPY fem2sjobs.txt .

from base_image as vastage
ENTRYPOINT ["/usr/bin/python3", "vastage.py"]
