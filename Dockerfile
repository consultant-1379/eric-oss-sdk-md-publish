#
# COPYRIGHT Ericsson 2021
#
#
#
# The copyright to the computer program(s) herein is the property of
#
# Ericsson Inc. The programs may be used and/or copied only with written
#
# permission from Ericsson Inc. or in accordance with the terms and
#
# conditions stipulated in the agreement/contract under which the
#
# program(s) have been supplied.
#

ARG CBOS_VERSION=3.44.0-9
FROM armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release/sles:${CBOS_VERSION}

ARG CBOS_VERSION
ARG CBO_REPO_URL=https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/${CBOS_VERSION}

RUN zypper ar -C -G -f $CBO_REPO_URL?ssl_verify=no \
    COMMON_BASE_OS_SLES_REPO \
    && zypper install -l -y java-11-openjdk-headless \
    && zypper clean --all \
    && zypper rr COMMON_BASE_OS_SLES_REPO

ARG USER_ID=40514
RUN echo "$USER_ID:!::0:::::" >>/etc/shadow

ARG USER_NAME="eric-oss-sdk-md-publish"
RUN echo "$USER_ID:x:$USER_ID:0:An Identity for $USER_NAME:/nonexistent:/bin/false" >>/etc/passwd

ARG JAR_FILE
ADD target/${JAR_FILE} eric-oss-sdk-md-publish-app.jar
COPY src/main/resources/jmx/* /jmx/
RUN chmod 600 /jmx/jmxremote.password
RUN chown $USER_ID /jmx/jmxremote.password

USER $USER_ID


CMD ["/bin/sh", "-c", "java ${JAVA_OPTS} -Dcom.sun.management.jmxremote=true \
    -Dcom.sun.management.jmxremote.port=1099 -Dcom.sun.management.jmxremote.authenticate=true \
    -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.rmi.port=1099 \
    -Dcom.sun.management.jmxremote.password.file=/jmx/jmxremote.password -Dcom.sun.management.jmxremote.access.file=/jmx/jmxremote.access \
    -jar eric-oss-sdk-md-publish-app.jar"]

ARG COMMIT
ARG BUILD_DATE
ARG APP_VERSION
ARG RSTATE
ARG IMAGE_PRODUCT_NUMBER
LABEL \
    org.opencontainers.image.title=eric-oss-sdk-md-publish-jsb \
    org.opencontainers.image.created=$BUILD_DATE \
    org.opencontainers.image.revision=$COMMIT \
    org.opencontainers.image.vendor=Ericsson \
    org.opencontainers.image.version=$APP_VERSION \
    com.ericsson.product-revision="${RSTATE}" \
    com.ericsson.product-number="$IMAGE_PRODUCT_NUMBER"
