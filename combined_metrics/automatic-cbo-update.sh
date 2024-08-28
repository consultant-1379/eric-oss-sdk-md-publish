####################################################################################
# Script to automatically change CBO to new version in USERMGMT
####################################################################################
#!/bin/bash
echo "Querying for the latest CBO version..."
 latest_cbo_version=$(curl -u amadm100:AKCp5bBhBeBH1StEyF5jb1ZCrhWWJ97jkUCGFpcZvbnAqVSVAzH5RkzKCJi7dVdYJxjNDoCq9 \
    -X POST https://arm.epk.ericsson.se/artifactory/api/search/aql \
    -H "content-type: text/plain" \
    -d 'items.find({ "repo": {"$eq":"docker-v2-global-local"}, "path": {"$match" : "proj-ldc/common_base_os_release/*"}}).sort({"$desc": ["created"]}).limit(1)' \
    2>/dev/null | grep path | sed -e 's_.*\/\(.*\)".*_\1_')
  echo "Latest CBO version : $latest_cbo_version"
echo "Update the Dockerfile with new CBO(SUSE)-$latest_cbo_version"
sed -i 's/SUSE_IMAGE_VERSION/'"$latest_cbo_version"'/' Dockerfile
echo "END of shell"
exit
