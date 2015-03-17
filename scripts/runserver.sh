#!/bin/bash

# Check to see if the PYTHOPATH is set (and if so, assume it's for 2.7),
# so get rid of that.
if [ $PYTHONPATH ]
    then
    unset PYTHONPATH;
fi


sudo su -;

echo "Stopping nginx...";
/etc/init.d/nginx stop;
echo "Stopping supervisor...";
supervisorctl stop tndata_backend;

echo "sourcing virtualenv..."
source /webapps/tndata_backend/bin/activate;
cd /webapps/tndata_backend/tndata_backend/tndata_backend/ && python manage.py 0.0.0.0:80
