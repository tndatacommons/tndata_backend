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
source /webapps/tndata_backend/bin/activate && cd /webapps/tndata_backend/tndata_backend/tndata_backend/
