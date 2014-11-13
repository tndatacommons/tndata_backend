#!/bin/bash

# My path has python 2.7 stuff attached,
# so get rid of that.
unset PYTHONPATH;

# I'm lazy
source env/bin/activate && cd tndata_backend
