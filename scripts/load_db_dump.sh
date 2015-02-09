#!/bin/bash

# IF there's a `dump.sql` file in the same directory, just load it up!
# so get rid of that.
if [ -e "dump.sql" ]
    then
    psql -h 127.0.0.1 -U tndata_backend -d tndata_backend -f dump.sql
else
    echo
    echo "Could not find a DB dump.sql file!"
    echo
fi
