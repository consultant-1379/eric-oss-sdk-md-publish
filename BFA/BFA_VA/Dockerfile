FROM armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release/sles:4.1.0-31
ARG CBO_REPO_URL=https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/4.1.0-31
#Install Java 8
RUN zypper ar -C -G -f $CBO_REPO_URL?ssl_verify=no \
    COMMON_BASE_OS_SLES_REPO \
    && zypper --non-interactive in python3 python3-pip curl\
    && zypper clean --all \
    && zypper rr COMMON_BASE_OS_SLES_REPO
RUN pip install pyyaml
RUN pip install pymongo
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/vaCauses.py .
COPY src/main.py .
COPY src/Hashmap.py .
#Run python script
ENTRYPOINT ["/usr/bin/python3", "main.py"]
