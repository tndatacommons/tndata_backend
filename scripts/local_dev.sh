#!/bin/bash

# This script activates our python3 virtual environment in a vagrant vm.
#
# Check to see if the PYTHOPATH is set (and if so, assume it's for 2.7),
# so get rid of that.
if [ $PYTHONPATH ]
    then
    unset PYTHONPATH;
fi

# Then just source the pyenv
source /Users/brad/tndata/tndata_backend/env/bin/activate;
cd /Users/brad/tndata/tndata_backend/tndata_backend/;

# -----------------------------------------------------------------------------
# TODO: Change the following before releasing any of this as open-source.
#
# - GCM api key
# - Database passwords
# - redis passwords
# - AWS passwords
# - Slack api token
# -----------------------------------------------------------------------------
# THESE are all settings for local development
# -----------------------------------------------------------------------------
export ADMIN_NAME="Brad Montgomery"
export ADMIN_EMAIL="bkmontgomery@tndata.org"
export MANAGER_NAME="Russell Ingram"
export MANAGER_EMAIL="ringram@tndata.org"
export DEFAULT_EMAIL="Compass Team <webmaster@tndata.org>"
export SECRET_KEY="FpLVEvBOd%uIDxhS-&YWwR(Uc*fZH=tk@a!zNKni+rJgsmjG^$"
export ALLOWED_HOSTS="localhost;127.0.0.1;.tndata.org;.tndata.org.;104.236.244.232;159.203.68.206;brad.ngrok.io;tndata.ngrok.io"
export SITE_DOMAIN="localhost"
export HAYSTACK_URL="http://127.0.0.1:9200/"
export HAYSTACK_INDEX_NAME="haystack-dev"
export GCM_API_KEY='AIzaSyCi5AGkIhEWPrO8xo3ec3MIo7-tGlRtng0'
export DB_NAME='tndata_backend'
export DB_USER='brad'
export DB_PASSWORD=''
export DB_HOST="127.0.0.1"
export DB_PORT="5432"
export REDIS_PASSWORD='VPoDYBZgeyktxArddu4EHrNMdFsUzf7TtFKTP'
export REDIS_PORT="6397"
export REDIS_HOST="127.0.0.1"
export REDIS_CACHE_DB="3"
export REDIS_METRICS_DB="4"
export REDIS_RQ_DB="5"
export PLAY_APP_URL="https://play.google.com/apps/testing/org.tndata.android.compass"
export SLACK_API_TOKEN='xoxp-4823219390-6288403475-6868819906-193c4a'
export SLACK_CHANNEL="#tech"
export SLACK_USERNAME="brad's laptop"
export MEDIA_ROOT="/Users/brad/tndata/tndata_backend/uploads"
export AWS_USER="tndata"
export AWS_STORAGE_BUCKET_NAME="tndata-staging"
export AWS_ACCESS_KEY_ID="AKIAIXQUJ3HCC6GMN74Q"
export AWS_SECRET_ACCESS_KEY="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"
