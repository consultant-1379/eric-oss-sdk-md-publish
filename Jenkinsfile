#!/usr/bin/env groovy

def defaultBobImage = 'armdocker.rnd.ericsson.se/proj-adp-cicd-drop/bob.2.0:1.7.0-55'
def bob = new BobCommand()
    .bobImage(defaultBobImage)
    .envVars([
        HOME:'${HOME}',
        ISO_VERSION:'${ISO_VERSION}',
        RELEASE:'${RELEASE}',
        SONAR_HOST_URL:'${SONAR_HOST_URL}',
        SONAR_AUTH_TOKEN:'${SONAR_AUTH_TOKEN}',
        GERRIT_USERNAME: '${GERRIT_USERNAME}',
        GERRIT_PASSWORD: '${GERRIT_PASSWORD}',
        GERRIT_CHANGE_NUMBER:'${GERRIT_CHANGE_NUMBER}',
        KUBECONFIG:'${KUBECONFIG}',
        K8S_NAMESPACE: '${K8S_NAMESPACE}',
        USER:'${USER}',
        SELI_ARTIFACTORY_REPO_USER:'${CREDENTIALS_SELI_ARTIFACTORY_USR}',
        SELI_ARTIFACTORY_REPO_PASS:'${CREDENTIALS_SELI_ARTIFACTORY_PSW}',
        SERO_ARTIFACTORY_REPO_USER:'${CREDENTIALS_SERO_ARTIFACTORY_USR}',
        SERO_ARTIFACTORY_REPO_PASS:'${CREDENTIALS_SERO_ARTIFACTORY_PSW}',
        XRAY_USER:'${CREDENTIALS_XRAY_SELI_ARTIFACTORY_USR}',
        XRAY_APIKEY:'${CREDENTIALS_XRAY_SELI_ARTIFACTORY_PSW}',
        VHUB_API_TOKEN:'${VHUB_API_TOKEN}',
        MAVEN_CLI_OPTS: '${MAVEN_CLI_OPTS}',
        OPEN_API_SPEC_DIRECTORY: '${OPEN_API_SPEC_DIRECTORY}',
        FUNCTIONAL_USER_USERNAME: '${FUNCTIONAL_USER_USERNAME}',
        FUNCTIONAL_USER_PASSWORD: '${FUNCTIONAL_USER_PASSWORD}',
        INT_CHART_NAME: '${INT_CHART_NAME}',
        INT_CHART_REPO: '${INT_CHART_REPO}',
        GERRIT_MIRROR: '${GERRIT_MIRROR}',
        INT_CHART_VERSION: '${CHART_VERSION}',
        STATE_VALUES_FILE: '${STATE_VALUES_FILE}',
        GET_ALL_IMAGES: '${GET_ALL_IMAGES}',
        PATH_TO_HELMFILE: '${PATH_TO_HELMFILE}'


    ])
    .needDockerSocket(true)
    .toString()

def LOCKABLE_RESOURCE_LABEL = "kaas"
def validateSdk = 'true'

pipeline {
    agent {
        node {
            label NODE_LABEL
        }
    }

    options {
        timestamps()
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '50', artifactNumToKeepStr: '50'))
    }

    environment {
        TEAM_NAME = "${teamName}"
        KUBECONFIG = "${WORKSPACE}/.kube/config"
        CREDENTIALS_XRAY_SELI_ARTIFACTORY = credentials('XRAY_SELI_ARTIFACTORY')
        CREDENTIALS_SELI_ARTIFACTORY = credentials('SELI_ARTIFACTORY')
        CREDENTIALS_SERO_ARTIFACTORY = credentials('SERO_ARTIFACTORY')
        MAVEN_CLI_OPTS = "-Duser.home=${env.HOME} -B -s ${env.WORKSPACE}/settings.xml"
        OPEN_API_SPEC_DIRECTORY = "src/main/resources/v1"
        VHUB_API_TOKEN = credentials('vhub-api-key-id')
        HADOLINT_ENABLED = "true"
        KUBEHUNTER_ENABLED = "true"
        KUBEAUDIT_ENABLED = "true"
        KUBESEC_ENABLED = "true"
        TRIVY_ENABLED = "true"
        XRAY_ENABLED = "true"
        ANCHORE_ENABLED = "false"
    }


    stages { 
         stage('Clean') {
            steps {

                sh "${bob} clean"

            }
        }
        stage('Metrics Collections') {
            parallel {

                  /*stage('RPT-Retention_policy'){
                       steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                       sh "${bob} rpt-retention"}}

                      }*/

                  stage('Repository HelmVersions'){
                     steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} helm_version_image"
                              }
                     }
                  }

                  stage('Gerrit Patchset Upload'){
                      steps{
                      withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} gerrit_patchset_upload"
                              }
                      }
                  }

                
                 stage('Dora Metrics') {
                          steps {
                             withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                                 sh "chmod +x ./combined_metrics/automatic-cbo-update.sh"
                                 sh "./combined_metrics/automatic-cbo-update.sh"
                                 sh "${bob} dora_docker_image"
                              }   
                          }
                   }
                  stage('Sonar Metrics'){
                     steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} sonar_docker_image"
                              }
                     }
                  }
                  stage('Jira Metrics'){
                       steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                     
                         sh "${bob} jira_docker_image"
                             }
                          }
                  }
                  stage('drcheck Metrics'){
                     steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} drcheck_docker_image"
                       }
                     }
                  }
                  stage('Jenkins Metrics'){
                     steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} jenkins_docker_image"
                        }
                     }
                  }
/*
                  stage('Gerrit Commits'){
                     steps{
withCredentials([usernamePassword(credentialsId: env.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME',  passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                         sh "${bob} gerrit_docker_image"
                         }
                     }
                  } 
*/





            }
        }


           



    }
}

// More about @Builder: http://mrhaki.blogspot.com/2014/05/groovy-goodness-use-builder-ast.html
import groovy.transform.builder.Builder
import groovy.transform.builder.SimpleStrategy

@Builder(builderStrategy = SimpleStrategy, prefix = '')
class BobCommand {
    def bobImage = 'bob.2.0:latest'
    def envVars = [:]
    def needDockerSocket = false

    String toString() {
        def env = envVars
                .collect({ entry -> "-e ${entry.key}=\"${entry.value}\"" })
                .join(' ')

        def cmd = """\
            |docker run
            |--init
            |--rm
            |--workdir \${PWD}
            |--user \$(id -u):\$(id -g)
            |-v \${PWD}:\${PWD}
            |-v /etc/group:/etc/group:ro
            |-v /etc/passwd:/etc/passwd:ro
            |-v /proj/mvn/:/proj/mvn
            |-v \${HOME}:\${HOME}
            |${needDockerSocket ? '-v /var/run/docker.sock:/var/run/docker.sock' : ''}
            |${env}
            |\$(for group in \$(id -G); do printf ' --group-add %s' "\$group"; done)
            |--group-add \$(stat -c '%g' /var/run/docker.sock)
            |${bobImage}
            |"""
        return cmd
                .stripMargin()           // remove indentation
                .replace('\n', ' ')      // join lines
                .replaceAll(/[ ]+/, ' ') // replace multiple spaces by one
    }
}

